from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from schemas.profile import ProfileSummary, JainSect, Gender
from services.match_service import score_match, get_match_label
from middleware.auth_middleware import get_current_user
from database import get_supabase_admin
from datetime import date

router = APIRouter(prefix="/matches", tags=["Matches"])


def _calculate_age(dob_str: str) -> int:
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 0


@router.get("/", response_model=List[dict])
async def browse_matches(
    gender: Optional[Gender] = None,
    jain_sect: Optional[JainSect] = None,
    min_age: Optional[int] = Query(None, ge=18, le=60),
    max_age: Optional[int] = Query(None, ge=18, le=60),
    city: Optional[str] = None,
    state: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """
    Browse all active profiles with optional filters.
    Results include a compatibility score for Gold/Platinum plan users.
    """
    db = get_supabase_admin()
    user_id = current_user["sub"]

    # Get viewer's own profile for scoring
    my_profile_result = db.table("profiles").select("*").eq("user_id", user_id).execute()
    my_profile = my_profile_result.data[0] if my_profile_result.data else {}
    my_gender = my_profile.get("gender")
    my_plan = my_profile.get("selected_plan", "free")

    # Build query — show opposite gender by default
    query = db.table("profiles").select(
        "id, full_name, date_of_birth, gender, city, state, jain_sect, "
        "occupation, photo_url, is_verified, selected_plan"
    ).eq("is_active", True).neq("user_id", user_id)

    # Default: show opposite gender
    if gender:
        query = query.eq("gender", gender.value)
    elif my_gender == "male":
        query = query.eq("gender", "female")
    elif my_gender == "female":
        query = query.eq("gender", "male")

    if jain_sect:
        query = query.eq("jain_sect", jain_sect.value)
    if city:
        query = query.ilike("city", f"%{city}%")
    if state:
        query = query.ilike("state", f"%{state}%")

    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    profiles = result.data or []

    # Age filter (computed field — not stored directly)
    if min_age or max_age:
        filtered = []
        for p in profiles:
            age = _calculate_age(p.get("date_of_birth", ""))
            p["age"] = age
            if min_age and age < min_age:
                continue
            if max_age and age > max_age:
                continue
            filtered.append(p)
        profiles = filtered
    else:
        for p in profiles:
            p["age"] = _calculate_age(p.get("date_of_birth", ""))

    # Add compatibility score for paid plans
    if my_plan in ("gold", "platinum"):
        for p in profiles:
            p["compatibility_score"] = score_match(my_profile, p)
            p["compatibility_label"] = get_match_label(p["compatibility_score"])
        profiles.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)

    return profiles


@router.post("/{profile_id}/interest")
async def send_interest(profile_id: str, current_user: dict = Depends(get_current_user)):
    """Express interest in a profile. Notifies recipient via WhatsApp."""
    from services.whatsapp_service import notify_interest_received
    db = get_supabase_admin()
    user_id = current_user["sub"]

    # Get sender's name
    my_profile = db.table("profiles").select("full_name").eq("user_id", user_id).execute()
    sender_name = my_profile.data[0]["full_name"] if my_profile.data else "Someone"

    # Get recipient's contact
    recipient = db.table("profiles").select("user_id, full_name, whatsapp").eq("id", profile_id).execute()
    if not recipient.data:
        return {"message": "Profile not found"}

    recipient_data = recipient.data[0]

    # Store interest record
    db.table("interests").upsert({
        "sender_id": user_id,
        "recipient_id": recipient_data["user_id"],
        "profile_id": profile_id,
        "status": "pending",
    }).execute()

    # Notify via WhatsApp if they have a number
    if recipient_data.get("whatsapp"):
        notify_interest_received(recipient_data["whatsapp"], sender_name)

    return {"message": f"Interest sent to {recipient_data['full_name']}"}


@router.get("/interests/received", response_model=List[dict])
async def get_received_interests(current_user: dict = Depends(get_current_user)):
    """Get all interest requests received by the logged-in user."""
    db = get_supabase_admin()
    result = db.table("interests").select(
        "*, profiles!sender_id(full_name, city, jain_sect, photo_url)"
    ).eq("recipient_id", current_user["sub"]).eq("status", "pending").execute()
    return result.data or []


@router.get("/interests/sent", response_model=List[dict])
async def get_sent_interests(current_user: dict = Depends(get_current_user)):
    """Get all interests the logged-in user has sent."""
    db = get_supabase_admin()
    result = db.table("interests").select(
        "*, profiles!recipient_id(full_name, city, jain_sect, photo_url)"
    ).eq("sender_id", current_user["sub"]).execute()
    return result.data or []
