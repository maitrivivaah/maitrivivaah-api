-- ============================================================
-- MaitriVivaah — Supabase PostgreSQL Schema
-- Run this in your Supabase SQL editor (Dashboard → SQL Editor)
-- ============================================================

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ── Users table ───────────────────────────────────────────────────────────────
create table if not exists users (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  password_hash text,
  full_name     text,
  phone         text,
  avatar_url    text,
  role          text default 'user' check (role in ('user', 'admin', 'moderator', 'support')),
  is_active     boolean default true,
  auth_provider text default 'email' check (auth_provider in ('email', 'google')),
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- ── Profiles table ────────────────────────────────────────────────────────────
create table if not exists profiles (
  id                   uuid primary key default gen_random_uuid(),
  user_id              uuid references users(id) on delete cascade unique,

  -- Personal
  full_name            text not null,
  date_of_birth        date,
  age                  int,
  gender               text check (gender in ('male', 'female')),
  height_cm            int,
  weight_kg            int,
  complexion           text,
  mother_tongue        text,

  -- Religion
  jain_sect            text check (jain_sect in ('digambar','shwetambar','sthanakvasi','terapanthi','other')),
  gotra                text,
  kul                  text,
  natak                text,

  -- Location
  city                 text,
  state                text,
  country              text default 'India',
  grew_up_in           text,

  -- Education
  education_level      text,
  education_field      text,
  college              text,
  occupation           text,
  employer             text,
  annual_income        text,

  -- Family
  father_name          text,
  father_occupation    text,
  mother_name          text,
  mother_occupation    text,
  siblings             int,
  family_type          text,
  family_values        text,

  -- Marital
  marital_status       text default 'never_married',
  have_children        boolean default false,

  -- Partner preferences
  partner_age_min      int,
  partner_age_max      int,
  partner_height_min   int,
  partner_height_max   int,
  partner_jain_sect    text[],
  partner_education    text[],
  partner_location     text[],

  -- About
  about_me             text,
  hobbies              text[],
  photo_url            text,

  -- Plan
  selected_plan        text default 'free' check (selected_plan in ('free','silver','gold','platinum')),
  plan_expires_at      timestamptz,
  plan_payment_ref     text,

  -- Contact
  phone                text,
  whatsapp             text,

  -- Status
  is_active            boolean default true,
  is_verified          boolean default false,
  created_at           timestamptz default now(),
  updated_at           timestamptz default now()
);

-- ── Interests table ───────────────────────────────────────────────────────────
create table if not exists interests (
  id            uuid primary key default gen_random_uuid(),
  sender_id     uuid references users(id) on delete cascade,
  recipient_id  uuid references users(id) on delete cascade,
  profile_id    uuid references profiles(id) on delete cascade,
  status        text default 'pending' check (status in ('pending', 'accepted', 'declined')),
  created_at    timestamptz default now(),
  unique(sender_id, profile_id)
);

-- ── Row Level Security (RLS) ──────────────────────────────────────────────────
-- Users can only read/update their own user record
alter table users enable row level security;
create policy "users_own_record" on users
  for all using (auth.uid()::text = id::text);

-- Profiles are publicly readable (active ones), but only owner can write
alter table profiles enable row level security;
create policy "profiles_public_read" on profiles
  for select using (is_active = true);
create policy "profiles_owner_write" on profiles
  for all using (auth.uid()::text = user_id::text);

-- Interests: sender and recipient can read; sender can insert
alter table interests enable row level security;
create policy "interests_read" on interests
  for select using (
    auth.uid()::text = sender_id::text or
    auth.uid()::text = recipient_id::text
  );
create policy "interests_insert" on interests
  for insert with check (auth.uid()::text = sender_id::text);

-- ── Indexes ────────────────────────────────────────────────────────────────────
create index if not exists idx_profiles_gender     on profiles(gender);
create index if not exists idx_profiles_jain_sect  on profiles(jain_sect);
create index if not exists idx_profiles_city       on profiles(city);
create index if not exists idx_profiles_state      on profiles(state);
create index if not exists idx_profiles_plan       on profiles(selected_plan);
create index if not exists idx_profiles_active     on profiles(is_active);
create index if not exists idx_interests_recipient on interests(recipient_id);
