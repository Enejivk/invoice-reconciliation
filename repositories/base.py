"""Base repository with tenant isolation."""
from typing import Generic, TypeVar, Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with tenant isolation enforcement."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    def _ensure_tenant_filter(self, tenant_id: int, query):
        """Ensure tenant_id is always in the query filter."""
        # This is a safety mechanism - all queries MUST include tenant_id
        if hasattr(self.model, "tenant_id"):
            return query.where(self.model.tenant_id == tenant_id)
        return query

    async def get_by_id(
        self, tenant_id: int, id: int, include_relations: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get entity by ID with tenant isolation."""
        query = select(self.model).where(
            and_(self.model.id == id, self.model.tenant_id == tenant_id)
        )

        if include_relations:
            for relation in include_relations:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: int,
        filters: Optional[dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ModelType]:
        """List entities with tenant isolation and optional filters."""
        query = select(self.model).where(self.model.tenant_id == tenant_id)

        if filters:
            query = self._apply_filters(query, filters)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _apply_filters(self, query, filters: dict):
        """Apply filters to query - override in subclasses."""
        return query

    async def create(self, entity: ModelType) -> ModelType:
        """Create entity."""
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Update entity."""
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete entity."""
        await self.db.delete(entity)
        await self.db.flush()

    async def count(self, tenant_id: int, filters: Optional[dict] = None) -> int:
        """Count entities with tenant isolation."""
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model).where(
            self.model.tenant_id == tenant_id
        )

        if filters:
            query = self._apply_filters(query, filters)

        result = await self.db.execute(query)
        return result.scalar_one() or 0

