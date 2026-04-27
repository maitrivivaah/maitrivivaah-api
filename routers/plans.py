from fastapi import APIRouter, Depends, HTTPException
from schemas.plan import PlanUpgradeRequest, PlanResponse, PLAN_CATALOG
from middleware.auth_middleware import get_current_user
from database import get_supabase_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/", response_model=dict)
async def get_all_plans():
    """Return the full plan catalog — public endpoint, no auth needed."""
    return {
        plan_id: plan.model_dump()
        for plan_id, plan in PLAN_CATALOG.items()
    }


@router.get("/me", response_model=PlanResponse)
async def get_my_plan(current_user: dict = Depends(get_current_user)):
    """Get the logged-in user's current plan and expiry."""
    db = get_supabase_admin()
    result = db.table("profiles").select("selected_plan, plan_expires_at").eq(
        "user_id", current_user["sub"]
    ).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = result.data[0]
    plan_id = profile.get("selected_plan", "free")
    features = PLAN_CATALOG.get(plan_id, PLAN_CATALOG["free"])

    return PlanResponse(
        current_plan=plan_id,
        expires_at=profile.get("plan_expires_at"),
        features=features,
    )


@router.post("/upgrade", response_model=PlanResponse)
async def upgrade_plan(body: PlanUpgradeRequest, current_user: dict = Depends(get_current_user)):
    """
    Upgrade the user's plan after payment confirmation.
    In production: verify Razorpay/UPI payment_reference before upgrading.
    """
    db = get_supabase_admin()

    if body.plan not in PLAN_CATALOG:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")

    plan = PLAN_CATALOG[body.plan]
    expires_at = (datetime.utcnow() + timedelta(days=plan.duration_days)).isoformat()

    result = db.table("profiles").update({
        "selected_plan": body.plan,
        "plan_expires_at": expires_at,
        "plan_payment_ref": body.payment_reference,
    }).eq("user_id", current_user["sub"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return PlanResponse(
        current_plan=body.plan,
        expires_at=expires_at,
        features=plan,
    )
