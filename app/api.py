import calendar
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse
from app.models import (
    AuthRequest, JobApplication, JobApplicationCreate, 
    UserProfile, PasswordChangeRequest
)
from app.services import verify_old_password
from app.config import supabase, origins, get_supabase_admin_client

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
@api.get("/")
def index():
    return { "message" : "Welcome to trackr"}

@api.post("/api/login")
def login(user: AuthRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail=response["error"]["message"])
        
        user_metadata = response.user.user_metadata
        user_obj = {k: v for k, v in user_metadata.items() if k != 'sub'}
        user_obj['id'] = user_metadata.get('sub')
        
        return {"message": "Login successful.", "user": user_obj, "token": response.session.access_token }
    except Exception as e: 
        raise HTTPException(status_code=401, detail=str(e))

@api.post("/api/signup")
def signup(new_user: AuthRequest):
    try:
        response = supabase.auth.sign_up({
            "email": new_user.email,
            "password": new_user.password,
            "email_confirm": True,
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail=response["error"]["message"])

        user_metadata = response.user.user_metadata
        user_obj = {k: v for k, v in user_metadata.items() if k != 'sub'}
        user_obj['id'] = user_metadata.get('sub')
        
        return {"message": "Signup successful.", "user": user_obj, "token": response.session.access_token }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api.get("/api/dash-stats")
def get_dash_stats(uid: UUID = Query(..., description="User ID")):
    try:
        response = supabase.table("Applications").select("*").eq("uid", str(uid)).execute()
        applications = response.data

        if not applications:
            return {
                "statusCounts": {},
                "totalApplications": 0,
                "recentApplications": [],
                "weeklyAppliedStats": {}
            }

        # For Application Count per Status
        status_counts = defaultdict(int)
        for app in applications:
            status_counts[app.get("status", "Unknown")] += 1

        # Total Application Number
        total_applications = len(applications)

        # Applications From The Past 3 Days
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)
        recent_applied = [
            app for app in applications
            if app["status"] == "Applied" and parse(app["created_at"]) >= three_days_ago
        ]

        # Applications From The Past Week
        one_week_ago = now - timedelta(days=6)
        weekly_counts = defaultdict(int)

        for app in applications:
            if app["status"] == "Applied":
                created_date = parse(app["created_at"])
                if one_week_ago.date() <= created_date.date() <= now.date():
                    weekday = calendar.day_name[created_date.weekday()]
                    weekly_counts[weekday] += 1

        today_index = now.weekday()
        ordered_days = [calendar.day_name[(today_index + i + 1) % 7] for i in range(7)]
        ordered_weekly_counts = {day: weekly_counts.get(day, 0) for day in ordered_days}

        return {
            "statusCounts": dict(status_counts),
            "totalApplications": total_applications,
            "recentApplications": recent_applied,
            "weeklyAppliedStats": ordered_weekly_counts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@api.get("/api/applications")
def get_applications(uid: UUID = Query(..., description="User ID")):
    try:
        response = supabase.table("Applications").select("*").eq("uid", str(uid)).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/api/applications")
def add_application(application: JobApplicationCreate):
    data = application.model_dump()
    data["uid"] = str(data["uid"])
    try:
        response = supabase.table("Applications").insert(data).execute()
        return {
            "data": response.data,
            "message": "Application added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@api.put("/api/applications/{id}")
def edit_application(id: UUID, application: JobApplication):
    try:
        data = application.model_dump()
        data["uid"] = str(data["uid"])
        data["id"] = str(data["id"])
        response = supabase.table("Applications").update(data).eq("id", id).execute()
        return {
            "data": response.data,
            "message": "Application updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/api/applications/{id}")
def delete_application(id: UUID):
    try:
        response = supabase.table("Applications").delete().eq("id", id).execute()
        return {
            "data": response.data,
            "message": "Application deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.put("/api/user/{id}")
def edit_user(id: UUID, updated_user_data: UserProfile, supabase=Depends(get_supabase_admin_client)):
    try:
        response = supabase.auth.admin.update_user_by_id(
            str(id),
            attributes= {
                "user_metadata": updated_user_data.model_dump()
            }
        )
        user_metadata = response.user.user_metadata
        user_obj = {k: v for k, v in user_metadata.items() if k != 'sub'}
        user_obj['id'] = user_metadata.get('sub')
        
        return {"message": "User updated successfully", "user": user_obj}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.delete("/api/user/{id}")
def delete_user(id: UUID, supabase=Depends(get_supabase_admin_client)):
    try:
        supabase.auth.admin.delete_user(str(id), True)
        supabase.table("Applications").delete().eq("uid", id).execute()
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@api.put("/api/change-password/{id}")
def change_password(id: UUID, data: PasswordChangeRequest, supabase=Depends(get_supabase_admin_client)):
    try:
        user = supabase.auth.admin.get_user_by_id(str(id))
        email = user.user.email if user and user.user else None

        if not email:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not verify_old_password(email, data.current_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        if data.current_password == data.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from current password")

        supabase.auth.admin.update_user_by_id(
            str(id),
            attributes={"password": data.new_password}
        )

        return {"message": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))