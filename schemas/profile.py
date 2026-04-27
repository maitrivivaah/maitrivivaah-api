from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"


class MaritalStatus(str, Enum):
    never_married = "never_married"
    divorced = "divorced"
    widowed = "widowed"
    awaiting_divorce = "awaiting_divorce"


class JainSect(str, Enum):
    digambar = "digambar"
    shwetambar = "shwetambar"
    sthanakvasi = "sthanakvasi"
    terapanthi = "terapanthi"
    other = "other"


class EducationLevel(str, Enum):
    high_school = "high_school"
    diploma = "diploma"
    bachelors = "bachelors"
    masters = "masters"
    phd = "phd"
    other = "other"


class PlanType(str, Enum):
    free = "free"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


# ── Request schemas ────────────────────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    # Personal
    full_name: str
    date_of_birth: str                     # ISO format: "1995-08-15"
    gender: Gender
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    complexion: Optional[str] = None
    mother_tongue: Optional[str] = None

    # Religion
    jain_sect: JainSect
    gotra: Optional[str] = None
    kul: Optional[str] = None
    natak: Optional[str] = None            # Jain-specific sub-group

    # Location
    city: str
    state: str
    country: str = "India"
    grew_up_in: Optional[str] = None

    # Education & Career
    education_level: EducationLevel
    education_field: Optional[str] = None
    college: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    annual_income: Optional[str] = None    # Stored as range string e.g. "5-10 LPA"

    # Family
    father_name: Optional[str] = None
    father_occupation: Optional[str] = None
    mother_name: Optional[str] = None
    mother_occupation: Optional[str] = None
    siblings: Optional[int] = None
    family_type: Optional[str] = None     # Joint / Nuclear
    family_values: Optional[str] = None   # Traditional / Moderate / Liberal

    # Marital
    marital_status: MaritalStatus = MaritalStatus.never_married
    have_children: bool = False

    # Partner preferences
    partner_age_min: Optional[int] = None
    partner_age_max: Optional[int] = None
    partner_height_min: Optional[int] = None
    partner_height_max: Optional[int] = None
    partner_jain_sect: Optional[List[JainSect]] = None
    partner_education: Optional[List[EducationLevel]] = None
    partner_location: Optional[List[str]] = None

    # About
    about_me: Optional[str] = None
    hobbies: Optional[List[str]] = None

    # Plan
    selected_plan: PlanType = PlanType.free

    # Contact
    phone: Optional[str] = None
    whatsapp: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """All fields optional — PATCH semantics."""
    full_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[str] = None
    about_me: Optional[str] = None
    hobbies: Optional[List[str]] = None
    partner_age_min: Optional[int] = None
    partner_age_max: Optional[int] = None
    partner_jain_sect: Optional[List[JainSect]] = None
    selected_plan: Optional[PlanType] = None


# ── Response schemas ───────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    age: Optional[int] = None
    gender: Gender
    city: str
    state: str
    jain_sect: JainSect
    education_level: EducationLevel
    occupation: Optional[str] = None
    annual_income: Optional[str] = None
    marital_status: MaritalStatus
    about_me: Optional[str] = None
    selected_plan: PlanType
    photo_url: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True


class ProfileSummary(BaseModel):
    """Shorter version used in match listings."""
    id: str
    full_name: str
    age: Optional[int] = None
    city: str
    jain_sect: JainSect
    occupation: Optional[str] = None
    photo_url: Optional[str] = None
    is_verified: bool = False
