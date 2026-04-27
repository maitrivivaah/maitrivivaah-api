from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import get_settings
from database import get_supabase_admin

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_token(token: str) -> dict:
    """Decode and validate a JWT. Returns the payload dict."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — inject into any route that requires login."""
    return verify_token(token)


def get_current_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — inject into admin-only routes."""
    payload = verify_token(token)
    role = payload.get("role", "user")
    if role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return payload


def require_super_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — only full admins, not moderators."""
    payload = verify_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return payload
