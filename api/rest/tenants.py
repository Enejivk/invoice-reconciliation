"""Tenant REST endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.tenant_service import TenantService
from api.schemas.tenant import TenantCreate, TenantResponse, TenantListResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    data: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant."""
    service = TenantService(db)
    tenant = await service.create_tenant(data.name)
    await db.commit()
    return tenant


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants."""
    service = TenantService(db)
    tenants = await service.list_tenants(limit=limit, offset=offset)
    return TenantListResponse(tenants=tenants, total=len(tenants))

