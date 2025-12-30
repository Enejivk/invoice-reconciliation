"""Tenant repository."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Tenant
from repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Tenant, db)

    async def get_by_id(self, tenant_id: int, id: int) -> Optional[Tenant]:
        """Get tenant by ID (no tenant filtering for tenants table)."""
        query = select(Tenant).where(Tenant.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Tenant]:
        """List all tenants (no tenant filtering)."""
        query = select(Tenant).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, name: str) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(name=name)
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

