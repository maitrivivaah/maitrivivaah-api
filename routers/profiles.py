from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from schemas.profile import ProfileCreateRequest, ProfileUpdateRequest, ProfileResponse, ProfileSummary
from middleware.auth_middleware import get_current_user
from database import get_supabase_admin
from datetime import date
import cloudinary
import cloudinary.uploader
from config import get_settings

router = APIRouter(prefix="/profiles", tags=["Profiles"])
settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)


def _calculate_age(dob_str: str) -> int:
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 0


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(body: ProfileCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a new matrimony profile for the logged-in user."""
    db = get_supabase_admin()
    user_id = current_user["sub"]

    # Prevent duplicate profiles
    existing = db.table("profiles").select("id").eq("user_id", user_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PATCH to update.")

    data = body.model_dump()
    data["user_id"] = user_id
    data["age"] = _calculate_age(body.date_of_birth)
    data["is_active"] = True
    data["is_verified"] = False

    # Serialize lists to JSON-compatible format for Supabase
    for field in ["partner_jain_sect", "partner_education", "partner_location", "hobbies"]:
        if data.get(field):
            data[field] = [v.value if hasattr(v, "value") else v for v in data[field]]

    result = db.table("profiles").insert(data).execute()
    profile = result.data[0]
    profile["age"] = data["age"]
    return ProfileResponse(**profile)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get the logged-in user's own profile."""
    db = get_supabase_admin()
    result = db.table("profiles").select("*").eq("user_id", current_user["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete registration.")
    profile = result.data[0]
    if profile.get("date_of_birth"):
        profile["age"] = _calculate_age(profile["date_of_birth"])
    return ProfileResponse(**profile)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(body: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update parts of the logged-in user's profile."""
    db = get_supabase_admin()
    user_id = current_user["sub"]

    existing = db.table("profiles").select("id").eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = db.table("profiles").update(update_data).eq("user_id", user_id).execute()
    profile = result.data[0]
    if profile.get("date_of_birth"):
        profile["age"] = _calculate_age(profile["date_of_birth"])
    return ProfileResponse(**profile)


@router.post("/me/photo")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a profile photo to Cloudinary."""
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images accepted")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image must be under 5MB")

    user_id = current_user["sub"]

    result = cloudinary.uploader.upload(
        contents,
        folder=f"maitrivivaah/profiles/{user_id}",
        public_id="primary",
        overwrite=True,
        transformation=[{"width": 800, "height": 800, "crop": "fill", "gravity": "face"}],
    )
    photo_url = result["secure_url"]

    db = get_supabase_admin()
    db.table("profiles").update({"photo_url": photo_url}).eq("user_id", user_id).execute()

    return {"photo_url": photo_url}


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str, current_user: dict = Depends(get_current_user)):
    """Get any profile by ID (for viewing matches)."""
    db = get_supabase_admin()
    result = db.table("profiles").select("*").eq("id", profile_id).eq("is_active", True).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = result.data[0]
    if profile.get("date_of_birth"):
        profile["age"] = _calculate_age(profile["date_of_birth"])

    # Hide contact info for free-plan users viewing others
    viewer_plan_result = db.table("profiles").select("selected_plan").eq("user_id", current_user["sub"]).execute()
    viewer_plan = viewer_plan_result.data[0]["selected_plan"] if viewer_plan_result.data else "free"
    if viewer_plan == "free":
        profile.pop("phone", None)
        profile.pop("whatsapp", None)

    return ProfileResponse(**profile)
