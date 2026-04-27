from supabase import create_client, Client
from config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_supabase() -> Client:
    """Return a cached Supabase client (anon key — for user-scoped operations)."""
    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache()
def get_supabase_admin() -> Client:
    """Return a cached Supabase admin client (service role — bypass RLS).
    Use ONLY in admin / server-side routes. Never expose to frontend.
    """
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
