from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse,
    ForgotPasswordRequest, SetPasswordRequest
)
from services.auth_service import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_google_auth_url, exchange_google_code
)
from services.whatsapp_service import notify_admin_new_registration, notify_user_registration
from middleware.auth_middleware import get_current_user
from database import get_supabase_admin
from config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    """Register a new user with email + password."""
    db = get_supabase_admin()

    # Check email not already registered
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user record
    hashed = hash_password(body.password)
    user = db.table("users").insert({
        "email": body.email,
        "password_hash": hashed,
        "full_name": body.full_name,
        "phone": body.phone,
        "is_active": True,
        "auth_provider": "email",
    }).execute()

    user_data = user.data[0]
    user_id = user_data["id"]

    # Notify admin via WhatsApp
    if body.phone:
        notify_user_registration(body.phone, body.full_name)
    notify_admin_new_registration(body.full_name, body.email, "free")

    access_token  = create_access_token(user_id, body.email)
    refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=body.email,
        full_name=body.full_name,
        has_profile=False,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Login with email and password."""
    db = get_supabase_admin()

    result = db.table("users").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = result.data[0]

    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account deactivated. Contact support.")

    if not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if profile exists
    profile = db.table("profiles").select("id").eq("user_id", user["id"]).execute()
    has_profile = bool(profile.data)

    access_token  = create_access_token(user["id"], user["email"], user.get("role", "user"))
    refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        has_profile=has_profile,
    )


@router.get("/google")
async def google_login():
    """Redirect user to Google consent screen."""
    url = get_google_auth_url()
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth redirect. Creates or logs in user."""
    db = get_supabase_admin()

    google_user = await exchange_google_code(code)
    email  = google_user["email"]
    name   = google_user.get("name", "")
    avatar = google_user.get("picture", "")

    # Upsert user
    existing = db.table("users").select("*").eq("email", email).execute()
    if existing.data:
        user = existing.data[0]
        user_id = user["id"]
    else:
        new_user = db.table("users").insert({
            "email": email,
            "full_name": name,
            "avatar_url": avatar,
            "is_active": True,
            "auth_provider": "google",
            "password_hash": None,
        }).execute()
        user = new_user.data[0]
        user_id = user["id"]
        notify_admin_new_registration(name, email, "free")

    profile = db.table("profiles").select("id").eq("user_id", user_id).execute()
    has_profile = bool(profile.data)
    needs_password = user.get("auth_provider") == "google" and not user.get("password_hash")

    access_token  = create_access_token(user_id, email, user.get("role", "user"))
    refresh_token = create_refresh_token(user_id)

    # Redirect to frontend with tokens
    redirect_url = (
        f"{settings.frontend_url}/auth/callback"
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
        f"&has_profile={str(has_profile).lower()}"
        f"&needs_password={str(needs_password).lower()}"
    )
    return RedirectResponse(redirect_url)


@router.post("/set-password")
async def set_password(body: SetPasswordRequest, current_user: dict = Depends(get_current_user)):
    """Allow a Google-signup user to also set a password."""
    db = get_supabase_admin()
    hashed = hash_password(body.password)
    db.table("users").update({"password_hash": hashed}).eq("id", current_user["sub"]).execute()
    return {"message": "Password set successfully"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Send a password reset email via Supabase Auth."""
    db = get_supabase_admin()
    # Supabase handles the reset email automatically
    db.auth.reset_password_email(body.email)
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Exchange a refresh token for a new access token."""
    from jose import jwt, JWTError
    from config import get_settings
    s = get_settings()
    try:
        payload = jwt.decode(refresh_token, s.secret_key, algorithms=[s.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload["sub"]
        db = get_supabase_admin()
        user = db.table("users").select("email, role").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=401, detail="User not found")
        u = user.data[0]
        new_token = create_access_token(user_id, u["email"], u.get("role", "user"))
        return {"access_token": new_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
