"""Bank transaction REST endpoints."""
from fastapi import APIRouter, Depends, Path, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from services.bank_transaction_service import BankTransactionService
from api.schemas.bank_transaction import (
    BankTransactionImportRequest,
    BankTransactionImportResponse,
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

