from fastapi import APIRouter, Depends, HTTPException, status
from schemas.admin import (
    CreateTeamMemberRequest, UpdateTeamMemberRequest, TeamMemberResponse,
    AdminUserActionRequest, AdminUserAction, DashboardStats
)
from middleware.auth_middleware import get_current_admin, require_super_admin
from services.auth_service import hash_password
from database import get_supabase_admin
import secrets
import string

router = APIRouter(prefix="/admin", tags=["Admin"])


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    """High-level stats for the admin dashboard."""
    db = get_supabase_admin()

    users_result   = db.table("users").select("id, is_active, created_at").execute()
    profiles_result = db.table("profiles").select("id, gender, selected_plan, created_at").execute()

    users    = users_result.data or []
    profiles = profiles_result.data or []

    from datetime import datetime, timedelta
    now   = datetime.utcnow()
    today = now.date().isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()

    plan_breakdown = {"free": 0, "silver": 0, "gold": 0, "platinum": 0}
    for p in profiles:
        plan = p.get("selected_plan", "free")
        plan_breakdown[plan] = plan_breakdown.get(plan, 0) + 1

    return DashboardStats(
        total_users=len(users),
        active_users=sum(1 for u in users if u.get("is_active")),
        male_profiles=sum(1 for p in profiles if p.get("gender") == "male"),
        female_profiles=sum(1 for p in profiles if p.get("gender") == "female"),
        paid_users=sum(1 for p in profiles if p.get("selected_plan") != "free"),
        new_registrations_today=sum(1 for u in users if u.get("created_at", "").startswith(today)),
        new_registrations_this_week=sum(1 for u in users if u.get("created_at", "") >= week_ago),
        plan_breakdown=plan_breakdown,
    )


# ── User moderation ────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = 1,
    limit: int = 20,
    current_admin: dict = Depends(get_current_admin)
):
    """List all registered users with pagination."""
    db = get_supabase_admin()
    offset = (page - 1) * limit
    result = db.table("users").select(
        "id, email, full_name, phone, is_active, created_at, role"
    ).range(offset, offset + limit - 1).order("created_at", desc=True).execute()
    return result.data or []


@router.patch("/users/{user_id}")
async def moderate_user(
    user_id: str,
    body: AdminUserActionRequest,
    current_admin: dict = Depends(get_current_admin)
):
    """Activate, deactivate, verify, or delete a user."""
    db = get_supabase_admin()

    if body.action == AdminUserAction.activate:
        db.table("users").update({"is_active": True}).eq("id", user_id).execute()
        db.table("profiles").update({"is_active": True}).eq("user_id", user_id).execute()
        return {"message": "User activated"}

    elif body.action == AdminUserAction.deactivate:
        db.table("users").update({"is_active": False}).eq("id", user_id).execute()
        db.table("profiles").update({"is_active": False}).eq("user_id", user_id).execute()
        return {"message": "User deactivated"}

    elif body.action == AdminUserAction.verify:
        db.table("profiles").update({"is_verified": True}).eq("user_id", user_id).execute()
        return {"message": "Profile verified"}

    elif body.action == AdminUserAction.unverify:
        db.table("profiles").update({"is_verified": False}).eq("user_id", user_id).execute()
        return {"message": "Profile verification removed"}

    elif body.action == AdminUserAction.delete:
        db.table("profiles").delete().eq("user_id", user_id).execute()
        db.table("users").delete().eq("id", user_id).execute()
        return {"message": "User and profile deleted"}


# ── Team management ────────────────────────────────────────────────────────────

@router.get("/team", response_model=list[TeamMemberResponse])
async def list_team(current_admin: dict = Depends(get_current_admin)):
    """List all team/admin members."""
    db = get_supabase_admin()
    result = db.table("users").select(
        "id, email, full_name, role, is_active, created_at"
    ).in_("role", ["admin", "moderator", "support"]).execute()
    return result.data or []


@router.post("/team", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    body: CreateTeamMemberRequest,
    current_admin: dict = Depends(require_super_admin)
):
    """Create a new team member. Only super admins can do this."""
    db = get_supabase_admin()

    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already exists")

    temp_password = _generate_temp_password()
    result = db.table("users").insert({
        "email": body.email,
        "full_name": body.full_name,
        "phone": body.phone,
        "role": body.role.value,
        "is_active": True,
        "auth_provider": "email",
        "password_hash": hash_password(temp_password),
    }).execute()

    member = result.data[0]
    # In production: email the temp_password to body.email via SendGrid/SES
    print(f"[DEV] Temp password for {body.email}: {temp_password}")

    return TeamMemberResponse(**member)


@router.patch("/team/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: str,
    body: UpdateTeamMemberRequest,
    current_admin: dict = Depends(require_super_admin)
):
    db = get_supabase_admin()
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = db.table("users").update(update_data).eq("id", member_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Team member not found")
    return TeamMemberResponse(**result.data[0])


@router.post("/team/{member_id}/reset-password")
async def reset_team_member_password(
    member_id: str,
    current_admin: dict = Depends(require_super_admin)
):
    db = get_supabase_admin()
    temp_password = _generate_temp_password()
    db.table("users").update({"password_hash": hash_password(temp_password)}).eq("id", member_id).execute()
    # In production: send via email
    print(f"[DEV] New temp password for {member_id}: {temp_password}")
    return {"message": "Password reset. Temporary password sent to member's email."}


@router.delete("/team/{member_id}")
async def delete_team_member(
    member_id: str,
    current_admin: dict = Depends(require_super_admin)
):
    db = get_supabase_admin()
    db.table("users").delete().eq("id", member_id).in_("role", ["admin", "moderator", "support"]).execute()
    return {"message": "Team member removed"}
