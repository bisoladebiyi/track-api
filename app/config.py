import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_admin_client():
    # supabase "User not allowed" bug fix
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client