from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


# ── Plan schemas ───────────────────────────────────────────────────────────────

class PlanFeatures(BaseModel):
    name: str
    price_inr: int
    duration_days: int
    can_view_contact: bool
    can_send_interest: bool
    max_photos: int
    featured_listing: bool
    priority_support: bool
    ai_match_score: bool


PLAN_CATALOG: dict = {
    "free": PlanFeatures(
        name="Free", price_inr=0, duration_days=30,
        can_view_contact=False, can_send_interest=True,
        max_photos=1, featured_listing=False,
        priority_support=False, ai_match_score=False
    ),
    "silver": PlanFeatures(
        name="Silver", price_inr=999, duration_days=90,
        can_view_contact=True, can_send_interest=True,
        max_photos=5, featured_listing=False,
        priority_support=False, ai_match_score=False
    ),
    "gold": PlanFeatures(
        name="Gold", price_inr=2499, duration_days=180,
        can_view_contact=True, can_send_interest=True,
        max_photos=10, featured_listing=True,
        priority_support=True, ai_match_score=False
    ),
    "platinum": PlanFeatures(
        name="Platinum", price_inr=4999, duration_days=365,
        can_view_contact=True, can_send_interest=True,
        max_photos=20, featured_listing=True,
        priority_support=True, ai_match_score=True
    ),
}


class PlanUpgradeRequest(BaseModel):
    plan: str
    payment_reference: Optional[str] = None  # Razorpay / UPI reference


class PlanResponse(BaseModel):
    current_plan: str
    expires_at: Optional[str] = None
    features: PlanFeatures
