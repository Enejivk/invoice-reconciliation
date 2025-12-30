"""Tenant context management."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Tenant
from core.exceptions import TenantNotFoundError


async def get_tenant_or_raise(db: AsyncSession, tenant_id: int) -> Tenant:
    """Get tenant by ID or raise exception."""
    from sqlalchemy import select

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise TenantNotFoundError(tenant_id)

    return tenant


async def validate_tenant_access(
    db: AsyncSession, tenant_id: int, resource_tenant_id: int
) -> None:
    """Validate that user has access to tenant resource."""
    if tenant_id != resource_tenant_id:
        from core.exceptions import TenantMismatchError

        raise TenantMismatchError()

