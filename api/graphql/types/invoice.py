"""GraphQL invoice types."""
import strawberry
from datetime import datetime
from decimal import Decimal
from typing import Optional


@strawberry.type
class Invoice:
    """Invoice GraphQL type."""

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

    @classmethod
    def from_model(cls, invoice):
        """Create from SQLAlchemy model."""
        return cls(
            id=invoice.id,
            tenant_id=invoice.tenant_id,
            vendor_id=invoice.vendor_id,
            invoice_number=invoice.invoice_number,
            amount=invoice.amount,
            currency=invoice.currency,
            invoice_date=invoice.invoice_date,
            description=invoice.description,
            status=invoice.status,
            created_at=invoice.created_at,
        )


@strawberry.input
class CreateInvoiceInput:
    """Input for creating an invoice."""

    vendor_id: Optional[int] = None
    invoice_number: Optional[str] = None
    amount: float
    currency: str = "USD"
    invoice_date: Optional[datetime] = None
    description: Optional[str] = None


@strawberry.input
class InvoiceFilters:
    """Filters for invoice queries."""

    status: Optional[str] = None
    vendor_id: Optional[int] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

