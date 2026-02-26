from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
