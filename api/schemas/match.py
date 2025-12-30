"""Match schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class MatchResponse(BaseModel):
    """Schema for match response."""

    id: int
    tenant_id: int
    invoice_id: int
    bank_transaction_id: int
    score: Decimal
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Schema for match list response."""

    matches: list[MatchResponse]
    total: int


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response."""

    matches: list[MatchResponse]
    count: int


class ExplanationResponse(BaseModel):
    """Schema for AI explanation response."""

    explanation: str
    confidence: Optional[str] = None

