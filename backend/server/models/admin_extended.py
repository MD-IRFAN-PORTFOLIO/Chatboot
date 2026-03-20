from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# --- General System Response ---
class BaseResponse(BaseModel):
    message: str
    status: str = "success"

# --- User Management ---
class UserProfile(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: Optional[str] = None
    signup_date: datetime
    last_active: datetime
    total_conversations: int = 0
    status: str = "active"  # active, blocked

# --- Prompt Management ---
class PromptConfig(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    system_prompt: str
    temperature: float = 0.7
    response_length: int = 1000
    creativity_level: str = "Balanced" # Low, Balanced, High
    updated_at: datetime

# --- API Management ---
class APIKeyConfig(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    api_provider: str = "Gemini"
    api_key: str
    request_limit: int = 1500
    requests_today: int = 0
    status: str = "active"

# --- Activity Log ---
class ActivityLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    admin_id: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = None

# --- Feedback Management ---
class Feedback(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: Optional[str] = None
    conversation_id: str
    rating: int  # 1-5
    comments: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Analytics Dashboard Response ---
class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_conversations: int
    api_requests_today: int
    error_rate: float
    # These would normally be lists of points, simplified for now
    daily_conversations: List[dict] = []
    user_growth: List[dict] = []
