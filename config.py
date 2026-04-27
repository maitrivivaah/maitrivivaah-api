from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # JWT
    secret_key: str = "maitrivivaah-default-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # WhatsApp / Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    whatsapp_from: str = ""
    admin_whatsapp: str = ""

    # App
    app_env: str = "development"
    frontend_url: str = "https://maitrivivaah-web.vercel.app"
    allowed_origins: str = "https://maitrivivaah-web.vercel.app"

    @property
    def origins_list(self):
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
