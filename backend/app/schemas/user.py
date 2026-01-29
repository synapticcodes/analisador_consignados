"""
User schemas - Pydantic models for User API validation
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema para User."""

    email: EmailStr | None = None
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema para criação de usuário."""

    email: EmailStr
    password: str


class UserUpdate(UserBase):
    """Schema para atualização de usuário."""

    password: str | None = None


class UserResponse(UserBase):
    """Schema para resposta de usuário."""

    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}
