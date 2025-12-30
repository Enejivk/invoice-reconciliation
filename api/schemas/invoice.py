"""Invoice schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""

    vendor_id: Optional[int] = None
    invoice_number: Optional[str] = Field(None, max_length=255)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    invoice_date: Optional[datetime] = None
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""

    id: int
    tenant_id: int
    vendor_id: Optional[int]
    invoice_number: Optional[str]
    amount: Decimal
    currency: str
    invoice_date: Optional[datetime]
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""

    invoices: list[InvoiceResponse]
    total: int


class InvoiceFilters(BaseModel):
    """Schema for invoice filters."""

    status: Optional[str] = None
    vendor_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

