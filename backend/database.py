"""
database.py — Supabase client singleton.
Import `supabase` from this module everywhere.
"""
import os
from dotenv import load_dotenv

# Explicitly load .env from the same folder as this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL:
    raise RuntimeError(
        "Missing SUPABASE_URL in .env\n"
        "Get it from: Supabase Dashboard → Settings → API → Project URL"
    )
if not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_KEY in .env\n"
        "Get it from: Supabase Dashboard → Settings → API → service_role key"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)