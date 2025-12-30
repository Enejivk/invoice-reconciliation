"""Invoice repository."""
from datetime import datetime
from typing import Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Invoice
from repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for invoice operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Invoice, db)

    def _apply_filters(self, query, filters: dict):
        """Apply filters to invoice query."""
        if "status" in filters and filters["status"]:
            query = query.where(Invoice.status == filters["status"])

        if "vendor_id" in filters and filters["vendor_id"]:
            query = query.where(Invoice.vendor_id == filters["vendor_id"])

        if "min_amount" in filters and filters["min_amount"] is not None:
            query = query.where(Invoice.amount >= filters["min_amount"])

        if "max_amount" in filters and filters["max_amount"] is not None:
            query = query.where(Invoice.amount <= filters["max_amount"])

        if "start_date" in filters and filters["start_date"]:
            query = query.where(Invoice.invoice_date >= filters["start_date"])

        if "end_date" in filters and filters["end_date"]:
            query = query.where(Invoice.invoice_date <= filters["end_date"])

        return query

    async def get_open_invoices(self, tenant_id: int) -> list[Invoice]:
        """Get all open invoices for a tenant."""
        query = select(Invoice).where(
            and_(Invoice.tenant_id == tenant_id, Invoice.status == "open")
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

