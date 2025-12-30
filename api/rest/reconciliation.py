"""Reconciliation REST endpoints."""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.reconciliation_service import ReconciliationService
from services.ai_explanation_service import AIExplanationService
from services.invoice_service import InvoiceService
from services.bank_transaction_service import BankTransactionService
from api.schemas.match import ReconciliationResponse, ExplanationResponse, MatchResponse

router = APIRouter(prefix="/tenants/{tenant_id}/reconcile", tags=["reconciliation"])


@router.post("", response_model=ReconciliationResponse)
async def reconcile(
    tenant_id: int = Path(..., description="Tenant ID"),
    min_score: float = Query(default=50.0, ge=0.0, le=100.0, description="Minimum match score"),
    db: AsyncSession = Depends(get_db),
):
    """Run reconciliation and return all current match candidates."""
    service = ReconciliationService(db)
    # Run the reconciliation algorithm
    await service.reconcile(tenant_id, min_score=min_score)
    
    # Get all current proposed matches (including existing ones)
    matches = await service.get_match_candidates(tenant_id)
    return ReconciliationResponse(matches=matches, count=len(matches))


@router.get("/candidates", response_model=ReconciliationResponse)
async def list_candidates(
    tenant_id: int = Path(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    """List existing match candidates without running reconciliation."""
    service = ReconciliationService(db)
    matches = await service.get_match_candidates(tenant_id)
    return ReconciliationResponse(matches=matches, count=len(matches))


@router.get("/explain", response_model=ExplanationResponse)
async def explain_reconciliation(
    tenant_id: int = Path(..., description="Tenant ID"),
    invoice_id: int = Query(..., description="Invoice ID"),
    transaction_id: int = Query(..., description="Bank Transaction ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get AI explanation for a match decision."""
    # Get invoice and transaction
    invoice_service = InvoiceService(db)
    invoice = await invoice_service.get_invoice(tenant_id, invoice_id)
    
    transaction_service = BankTransactionService(db)
    transaction = await transaction_service.repository.get_by_id(tenant_id, transaction_id)
    if not transaction:
        from core.exceptions import ValidationError
        raise ValidationError(f"Transaction {transaction_id} not found")
    
    # Get vendor if exists
    vendor_name = None
    vendor = None
    if invoice.vendor_id:
        from sqlalchemy import select
        from models.database import Vendor
        result = await db.execute(select(Vendor).where(Vendor.id == invoice.vendor_id))
        vendor = result.scalar_one_or_none()
        if vendor:
            vendor_name = vendor.name
    
    # Calculate score
    from services.reconciliation_scorer import ReconciliationScorer
    score = ReconciliationScorer.calculate_score(invoice, transaction, vendor)
    
    # Get explanation
    ai_service = AIExplanationService()
    explanation = await ai_service.explain_match(invoice, transaction, score, vendor_name)
    
    return ExplanationResponse(**explanation)

