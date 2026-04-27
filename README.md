# MaitriVivaah API — Python FastAPI Backend

Jain matrimony platform backend. Built with **FastAPI** + **Supabase** + **Cloudinary**.

## Project Structure

```
maitrivivaah-api/
├── main.py                  # App entry point, CORS, router registration
├── config.py                # Settings loaded from .env
├── database.py              # Supabase client (anon + admin)
├── requirements.txt
├── supabase_schema.sql      # Run this in Supabase SQL editor first
├── .env.example             # Copy to .env and fill in values
│
├── routers/
│   ├── auth.py              # POST /auth/signup, /login, /google, /refresh
│   ├── profiles.py          # GET/POST/PATCH /profiles, photo upload
│   ├── matches.py           # GET /matches, POST /matches/:id/interest
│   ├── plans.py             # GET /plans, POST /plans/upgrade
│   └── admin.py             # Admin dashboard, user moderation, team management
│
├── schemas/
│   ├── auth.py              # Request/response models for auth
│   ├── profile.py           # Profile fields, enums (JainSect, Gender etc.)
│   ├── plan.py              # Plan catalog and upgrade models
│   └── admin.py             # Admin dashboard and team schemas
│
├── services/
│   ├── auth_service.py      # Password hashing, JWT creation, Google OAuth
│   ├── match_service.py     # Compatibility scoring engine (0–100)
│   └── whatsapp_service.py  # WhatsApp notifications via Twilio
│
└── middleware/
    └── auth_middleware.py   # JWT verification FastAPI dependencies
```

## Quick Start

### 1. Clone and install

```bash
cd maitrivivaah-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pydantic-settings    # Required for config.py
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Supabase, Cloudinary, and Google OAuth credentials
```

### 3. Set up Supabase database

Go to your Supabase project → **SQL Editor** → paste and run `supabase_schema.sql`.

### 4. Run the server

```bash
uvicorn main:app --reload --port 8000
```

API is now live at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register with email + password |
| POST | `/auth/login` | Login, returns JWT tokens |
| GET | `/auth/google` | Redirect to Google OAuth |
| GET | `/auth/google/callback` | Google OAuth callback |
| POST | `/auth/set-password` | Set password after Google signup |
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/refresh` | Refresh access token |

### Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/profiles/` | Create profile after signup |
| GET | `/profiles/me` | Get own profile |
| PATCH | `/profiles/me` | Update own profile |
| POST | `/profiles/me/photo` | Upload profile photo |
| GET | `/profiles/{id}` | View another user's profile |

### Matches
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/matches/` | Browse profiles with filters |
| POST | `/matches/{id}/interest` | Send interest to a profile |
| GET | `/matches/interests/received` | See who expressed interest |
| GET | `/matches/interests/sent` | See interests you've sent |

### Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plans/` | Get all plan details (public) |
| GET | `/plans/me` | Get your current plan |
| POST | `/plans/upgrade` | Upgrade plan after payment |

### Admin (requires admin JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/dashboard` | Stats overview |
| GET | `/admin/users` | List all users |
| PATCH | `/admin/users/{id}` | Activate/deactivate/verify/delete |
| GET | `/admin/team` | List team members |
| POST | `/admin/team` | Create team member |
| PATCH | `/admin/team/{id}` | Update team member |
| POST | `/admin/team/{id}/reset-password` | Reset password |
| DELETE | `/admin/team/{id}` | Remove team member |

---

## Deployment (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set all environment variables in Railway dashboard → Variables.

---

## Next Steps

- **Phase 2**: React JS web frontend (`maitrivivaah-web/`)
- **Phase 3**: React Native mobile app (`maitrivivaah-mobile/`)
- **Payment**: Add Razorpay integration in `/plans/upgrade`
- **Email**: Add SendGrid for transactional emails (welcome, reset password)
- **Chat**: Enable Supabase Realtime for in-app messaging
