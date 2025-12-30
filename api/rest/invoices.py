"""Invoice REST endpoints."""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.invoice_service import InvoiceService
from api.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceFilters,
)
from api.schemas.match import MatchResponse

router = APIRouter(prefix="/tenants/{tenant_id}/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    tenant_id: int = Path(..., description="Tenant ID"),
    data: InvoiceCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice."""
    service = InvoiceService(db)
    invoice = await service.create_invoice(
        tenant_id=tenant_id,
        vendor_id=data.vendor_id,
        invoice_number=data.invoice_number,
        amount=data.amount,
        currency=data.currency,
        invoice_date=data.invoice_date,
        description=data.description,
    )
    await db.commit()
    return invoice


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    tenant_id: int = Path(..., description="Tenant ID"),
    status: str | None = Query(None, description="Filter by status"),
    vendor_id: int | None = Query(None, description="Filter by vendor ID"),
    min_amount: float | None = Query(None, description="Minimum amount"),
    max_amount: float | None = Query(None, description="Maximum amount"),
    start_date: str | None = Query(None, description="Start date (ISO format)"),
    end_date: str | None = Query(None, description="End date (ISO format)"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with optional filters."""
    from datetime import datetime

    filters = {}
    if status:
        filters["status"] = status
    if vendor_id:
        filters["vendor_id"] = vendor_id
    if min_amount is not None:
        filters["min_amount"] = min_amount
    if max_amount is not None:
        filters["max_amount"] = max_amount
    if start_date:
        filters["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        filters["end_date"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    service = InvoiceService(db)
    invoices = await service.list_invoices(
        tenant_id=tenant_id, filters=filters, limit=limit, offset=offset
    )
    total = await service.repository.count(tenant_id, filters)

    return InvoiceListResponse(invoices=invoices, total=total)


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    tenant_id: int = Path(..., description="Tenant ID"),
    invoice_id: int = Path(..., description="Invoice ID"),
    db: AsyncSession = Depends(get_db),
):
    """Delete an invoice."""
    service = InvoiceService(db)
    await service.delete_invoice(tenant_id, invoice_id)
    await db.commit()


@router.get("/{invoice_id}/match", response_model=MatchResponse | None)
async def get_invoice_match(
    tenant_id: int = Path(..., description="Tenant ID"),
    invoice_id: int = Path(..., description="Invoice ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get the confirmed match for an invoice."""
    from services.match_service import MatchService

    service = MatchService(db)
    match = await service.get_confirmed_match_for_invoice(tenant_id, invoice_id)
    return match

