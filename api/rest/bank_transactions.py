"""Bank transaction REST endpoints."""
from fastapi import APIRouter, Depends, Path, Request, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from services.bank_transaction_service import BankTransactionService
from api.schemas.bank_transaction import (
    BankTransactionImportRequest,
    BankTransactionImportResponse,
    BankTransactionListResponse,
)

router = APIRouter(prefix="/tenants/{tenant_id}/bank-transactions", tags=["bank-transactions"])


@router.post("/import", response_model=BankTransactionImportResponse, status_code=201)
async def import_bank_transactions(
    tenant_id: int = Path(..., description="Tenant ID"),
    data: BankTransactionImportRequest = ...,
    request: Request = ...,
    db: AsyncSession = Depends(get_db),
):
    """Bulk import bank transactions with idempotency support."""
    # Extract idempotency key from header
    idempotency_key = request.headers.get(settings.idempotency_key_header)
    
    service = BankTransactionService(db)
    
    transactions_data = [
        {
            "external_id": tx.external_id,
            "posted_at": tx.posted_at,
            "amount": tx.amount,
            "currency": tx.currency,
            "description": tx.description,
        }
        for tx in data.transactions
    ]
    
    result = await service.import_transactions(
        tenant_id=tenant_id,
        transactions=transactions_data,
        idempotency_key=idempotency_key,
    )
    
    return BankTransactionImportResponse(**result)


@router.get("", response_model=BankTransactionListResponse)
async def list_bank_transactions(
    tenant_id: int = Path(..., description="Tenant ID"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List bank transactions with optional filters."""
    from datetime import datetime

    filters = {}
    if currency:
        filters["currency"] = currency
    if min_amount is not None:
        filters["min_amount"] = min_amount
    if max_amount is not None:
        filters["max_amount"] = max_amount
    if start_date:
        filters["start_date"] = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        filters["end_date"] = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    service = BankTransactionService(db)
    transactions = await service.list_transactions(
        tenant_id=tenant_id, filters=filters, limit=limit, offset=offset
    )
    total = await service.repository.count(tenant_id, filters)

    return BankTransactionListResponse(transactions=transactions, total=total)


@router.delete("/{transaction_id}", status_code=204)
async def delete_bank_transaction(
    tenant_id: int = Path(..., description="Tenant ID"),
    transaction_id: int = Path(..., description="Transaction ID"),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bank transaction."""
    service = BankTransactionService(db)
    await service.delete_transaction(tenant_id, transaction_id)
    await db.commit()

