"""Bank transaction repository."""
from typing import Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import BankTransaction
from repositories.base import BaseRepository


class BankTransactionRepository(BaseRepository[BankTransaction]):
    """Repository for bank transaction operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(BankTransaction, db)

    def _apply_filters(self, query, filters: dict):
        """Apply filters to bank transaction query."""
        if "min_amount" in filters and filters["min_amount"] is not None:
            query = query.where(BankTransaction.amount >= filters["min_amount"])

        if "max_amount" in filters and filters["max_amount"] is not None:
            query = query.where(BankTransaction.amount <= filters["max_amount"])

        if "start_date" in filters and filters["start_date"]:
            query = query.where(BankTransaction.posted_at >= filters["start_date"])

        if "end_date" in filters and filters["end_date"]:
            query = query.where(BankTransaction.posted_at <= filters["end_date"])

        if "currency" in filters and filters["currency"]:
            query = query.where(BankTransaction.currency == filters["currency"])

        return query

    async def get_unmatched_transactions(self, tenant_id: int) -> list[BankTransaction]:
        """Get transactions that haven't been matched yet."""
        from models.database import Match

        # Get transactions that don't have confirmed matches
        subquery = (
            select(Match.bank_transaction_id)
            .where(and_(Match.tenant_id == tenant_id, Match.status == "confirmed"))
            .subquery()
        )

        query = select(BankTransaction).where(
            and_(
                BankTransaction.tenant_id == tenant_id,
                ~BankTransaction.id.in_(select(subquery.c.bank_transaction_id)),
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_external_id(
        self, tenant_id: int, external_id: str
    ) -> Optional[BankTransaction]:
        """Get transaction by external ID (for idempotency)."""
        query = select(BankTransaction).where(
            and_(
                BankTransaction.tenant_id == tenant_id,
                BankTransaction.external_id == external_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

