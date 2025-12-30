"""Bank transaction schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class BankTransactionCreate(BaseModel):
    """Schema for creating a bank transaction."""

    external_id: Optional[str] = Field(None, max_length=255)
    posted_at: datetime
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None


class BankTransactionResponse(BaseModel):
    """Schema for bank transaction response."""

    id: int
    tenant_id: int
    external_id: Optional[str]
    posted_at: datetime
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BankTransactionImportRequest(BaseModel):
    """Schema for bulk import request."""

    transactions: list[BankTransactionCreate] = Field(..., min_items=1)


class BankTransactionImportResponse(BaseModel):
    """Schema for bulk import response."""

    count: int
    transaction_ids: list[int]


class BankTransactionListResponse(BaseModel):
    """Schema for list of bank transactions."""

    transactions: list[BankTransactionResponse]
    total: int


class BankTransactionFilters(BaseModel):
    """Schema for bank transaction filters."""

    currency: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

