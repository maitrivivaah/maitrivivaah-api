from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


class TeamRole(str, Enum):
    admin = "admin"
    moderator = "moderator"
    support = "support"


# ── Team management ────────────────────────────────────────────────────────────

class CreateTeamMemberRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: TeamRole
    phone: Optional[str] = None


class UpdateTeamMemberRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[TeamRole] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: TeamRole
    is_active: bool
    created_at: str


# ── User moderation ────────────────────────────────────────────────────────────

class AdminUserAction(str, Enum):
    activate = "activate"
    deactivate = "deactivate"
    verify = "verify"
    unverify = "unverify"
    delete = "delete"


class AdminUserActionRequest(BaseModel):
    action: AdminUserAction
    reason: Optional[str] = None


# ── Dashboard stats ────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    male_profiles: int
    female_profiles: int
    paid_users: int
    new_registrations_today: int
    new_registrations_this_week: int
    plan_breakdown: dict   # {"free": 120, "silver": 45, "gold": 20, "platinum": 5}
