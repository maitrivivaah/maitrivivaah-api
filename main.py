from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import httpx

from config import get_settings
from routers import auth, profiles, matches, plans, admin

settings = get_settings()

SELF_URL = "https://maitrivivaah-api.onrender.com/health"

async def keep_alive():
    """Ping self every 10 minutes to prevent Render free tier from sleeping."""
    await asyncio.sleep(60)  # wait 1 min after startup before first ping
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get(SELF_URL, timeout=10)
            print("🪷 Keep-alive ping sent")
        except Exception as e:
            print(f"⚠️ Keep-alive ping failed: {e}")
        await asyncio.sleep(600)  # ping every 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🪷 MaitriVivaah API starting — env: {settings.app_env}")
    task = asyncio.create_task(keep_alive())
    yield
    task.cancel()
    print("🪷 MaitriVivaah API shutting down")


app = FastAPI(
    title="MaitriVivaah API",
    description="Backend API for MaitriVivaah — Jain Matrimony Platform",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc at /redoc
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(matches.router)
app.include_router(plans.router)
app.include_router(admin.router)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "MaitriVivaah API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
