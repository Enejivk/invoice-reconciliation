"""Idempotency key repository."""
from typing import Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import IdempotencyKey
from repositories.base import BaseRepository


class IdempotencyRepository(BaseRepository[IdempotencyKey]):
    """Repository for idempotency key operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(IdempotencyKey, db)

    async def get_by_key(
        self, tenant_id: int, key: str
    ) -> Optional[IdempotencyKey]:
        """Get idempotency key by tenant and key."""
        query = select(IdempotencyKey).where(
            and_(IdempotencyKey.tenant_id == tenant_id, IdempotencyKey.key == key)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_or_get(
        self,
        tenant_id: int,
        key: str,
        endpoint: str,
        request_hash: str,
        response_data: Optional[str] = None,
    ) -> tuple[IdempotencyKey, bool]:
        """Create idempotency key or get existing one.
        
        Returns:
            Tuple of (IdempotencyKey, is_new)
        """
        existing = await self.get_by_key(tenant_id, key)

        if existing:
            # Check if request hash matches
            if existing.request_hash != request_hash:
                from core.exceptions import IdempotencyConflictError

                raise IdempotencyConflictError(
                    f"Idempotency key '{key}' already exists with different request payload"
                )
            return existing, False

        # Create new
        idempotency_key = IdempotencyKey(
            tenant_id=tenant_id,
            key=key,
            endpoint=endpoint,
            request_hash=request_hash,
            response_data=response_data,
        )
        self.db.add(idempotency_key)
        await self.db.flush()
        await self.db.refresh(idempotency_key)
        return idempotency_key, True

