"""Match repository."""
from typing import Optional
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Match
from repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    """Repository for match operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Match, db)

    def _apply_filters(self, query, filters: dict):
        """Apply filters to match query."""
        if "status" in filters and filters["status"]:
            query = query.where(Match.status == filters["status"])

        if "invoice_id" in filters and filters["invoice_id"]:
            query = query.where(Match.invoice_id == filters["invoice_id"])

        if "bank_transaction_id" in filters and filters["bank_transaction_id"]:
            query = query.where(Match.bank_transaction_id == filters["bank_transaction_id"])

        if "min_score" in filters and filters["min_score"] is not None:
            query = query.where(Match.score >= filters["min_score"])

        return query

    async def get_candidates_for_invoice(
        self, tenant_id: int, invoice_id: int, limit: int = 10
    ) -> list[Match]:
        """Get match candidates for an invoice, ordered by score."""
        query = (
            select(Match)
            .where(
                and_(
                    Match.tenant_id == tenant_id,
                    Match.invoice_id == invoice_id,
                    Match.status == "proposed",
                )
            )
            .order_by(desc(Match.score))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_candidates_for_transaction(
        self, tenant_id: int, transaction_id: int, limit: int = 10
    ) -> list[Match]:
        """Get match candidates for a transaction, ordered by score."""
        query = (
            select(Match)
            .where(
                and_(
                    Match.tenant_id == tenant_id,
                    Match.bank_transaction_id == transaction_id,
                    Match.status == "proposed",
                )
            )
            .order_by(desc(Match.score))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_candidates(
        self, tenant_id: int, min_score: float = 0.0
    ) -> list[Match]:
        """Get all match candidates above threshold."""
        query = (
            select(Match)
            .where(
                and_(
                    Match.tenant_id == tenant_id,
                    Match.status == "proposed",
                    Match.score >= min_score,
                )
            )
            .order_by(desc(Match.score))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

