"""Match service."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Match
from repositories.match_repository import MatchRepository
from core.tenant import get_tenant_or_raise
from core.exceptions import MatchNotFoundError


class MatchService:
    """Service for match operations."""

    def __init__(self, db: AsyncSession):
        self.repository = MatchRepository(db)

    async def confirm_match(self, tenant_id: int, match_id: int) -> Match:
        """Confirm a proposed match.

        This will:
        1. Update match status to 'confirmed'
        2. Update invoice status to 'matched'
        3. Optionally update transaction status
        """
        # Validate tenant exists
        await get_tenant_or_raise(self.repository.db, tenant_id)

        # Get match
        match = await self.repository.get_by_id(tenant_id, match_id)
        if not match:
            raise MatchNotFoundError(match_id)

        if match.status != "proposed":
            from core.exceptions import ValidationError

            raise ValidationError(f"Match {match_id} is already {match.status}")

        # Update match
        match.status = "confirmed"
        match.confirmed_at = datetime.utcnow()
        await self.repository.update(match)

        # Update invoice status
        from services.invoice_service import InvoiceService

        invoice_service = InvoiceService(self.repository.db)
        await invoice_service.update_invoice_status(tenant_id, match.invoice_id, "matched")

        # Commit changes
        await self.repository.db.commit()

        return match

    async def get_match(self, tenant_id: int, match_id: int) -> Match:
        """Get match by ID."""
        match = await self.repository.get_by_id(tenant_id, match_id)
        if not match:
            raise MatchNotFoundError(match_id)
        return match

