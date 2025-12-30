"""Invoice service."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Invoice
from repositories.invoice_repository import InvoiceRepository
from core.tenant import get_tenant_or_raise


class InvoiceService:
    """Service for invoice operations."""

    def __init__(self, db: AsyncSession):
        self.repository = InvoiceRepository(db)

    async def create_invoice(
        self,
        tenant_id: int,
        vendor_id: Optional[int],
        invoice_number: Optional[str],
        amount: Decimal,
        currency: str,
        invoice_date: Optional[datetime],
        description: Optional[str],
    ) -> Invoice:
        """Create a new invoice."""
        # Validate tenant exists
        await get_tenant_or_raise(self.repository.db, tenant_id)

        invoice = Invoice(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            invoice_number=invoice_number,
            amount=amount,
            currency=currency or "USD",
            invoice_date=invoice_date,
            description=description,
            status="open",
        )

        return await self.repository.create(invoice)

    async def get_invoice(self, tenant_id: int, invoice_id: int) -> Invoice:
        """Get invoice by ID."""
        invoice = await self.repository.get_by_id(tenant_id, invoice_id)
        if not invoice:
            from core.exceptions import InvoiceNotFoundError

            raise InvoiceNotFoundError(invoice_id)
        return invoice

    async def list_invoices(
        self,
        tenant_id: int,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices with optional filters."""
        return await self.repository.list(
            tenant_id=tenant_id, filters=filters or {}, limit=limit, offset=offset
        )

    async def delete_invoice(self, tenant_id: int, invoice_id: int) -> None:
        """Delete an invoice."""
        invoice = await self.get_invoice(tenant_id, invoice_id)
        await self.repository.delete(invoice)

    async def update_invoice_status(
        self, tenant_id: int, invoice_id: int, status: str
    ) -> Invoice:
        """Update invoice status."""
        invoice = await self.get_invoice(tenant_id, invoice_id)
        invoice.status = status
        return await self.repository.update(invoice)

