"""Tenant schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Schema for creating a tenant."""

    name: str = Field(..., min_length=1, max_length=255)


class TenantResponse(BaseModel):
    """Schema for tenant response."""

    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Schema for tenant list response."""

    tenants: list[TenantResponse]
    total: int

