"""Tenant service."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Tenant
from repositories.tenant_repository import TenantRepository


class TenantService:
    """Service for tenant operations."""

    def __init__(self, db: AsyncSession):
        self.repository = TenantRepository(db)

    async def create_tenant(self, name: str) -> Tenant:
        """Create a new tenant."""
        return await self.repository.create(name)

    async def get_tenant(self, tenant_id: int) -> Tenant:
        """Get tenant by ID."""
        tenant = await self.repository.get_by_id(tenant_id, tenant_id)
        if not tenant:
            from core.exceptions import TenantNotFoundError

            raise TenantNotFoundError(tenant_id)
        return tenant

    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        """List all tenants."""
        return await self.repository.list_all(limit=limit, offset=offset)

