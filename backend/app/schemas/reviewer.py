from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class SessionResponse(BaseModel):
    user_id: str
    role: str
    csrf_token: str | None = None


class RevisionResponse(BaseModel):
    id: int
    question_id: int | None
    acting_user: str
    created_at: datetime
    old_value: dict
    new_value: dict
    model_config = {'from_attributes': True}
