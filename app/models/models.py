from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class OrganizationDB(BaseModel):
    name: str = Field(...)
    collection_name: str = Field(...)
    admin_email: EmailStr = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class AdminDB(BaseModel):
    email: EmailStr = Field(...)
    hashed_password: str = Field(...)
    organization_name: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
