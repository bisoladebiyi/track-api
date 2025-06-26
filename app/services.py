import httpx
from app.config import SUPABASE_URL, SUPABASE_KEY

def verify_old_password(email: str, password: str) -> bool:
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password
    }

    response = httpx.post(url, json=payload, headers=headers)

    return response.status_code == 200