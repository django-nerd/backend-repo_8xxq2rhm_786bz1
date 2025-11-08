"""
Database Schemas for the app

Each Pydantic model represents a MongoDB collection. Class name is
lowercased for the collection name.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class User(BaseModel):
    email: str = Field(..., description="Email address")
    username: str = Field(..., description="Public username")
    password_hash: str = Field(..., description="SHA256 password hash")
    plan: str = Field("free", description="Subscription plan: free | plus | pro")

class Character(BaseModel):
    user_id: str = Field(..., description="Owner user id as string")
    prompt: str = Field(..., description="User prompt")
    settings: Dict[str, Any] = Field(default_factory=dict)
    preview_url: Optional[str] = Field(None, description="Preview image or render URL")
