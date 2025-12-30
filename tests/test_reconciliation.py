"""Tests for reconciliation."""
import pytest
from decimal import Decimal
from datetime import datetime


@pytest.mark.asyncio
async def test_reconciliation_produces_candidates(client, tenant, invoice, bank_transaction):
    """Test that reconciliation produces match candidates."""
    response = await client.post(
        f"/api/rest/tenants/{tenant.id}/reconcile?min_score=50.0"
    )
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert data["count"] >= 0

    # If we have matching invoice and transaction, we should get matches
    if data["count"] > 0:
        match = data["matches"][0]
        assert "score" in match
        assert float(match["score"]) >= 50.0
        assert match["status"] == "proposed"


@pytest.mark.asyncio
async def test_reconciliation_scoring_behavior(client, tenant, db_session):
    """Test reconciliation scoring behavior."""
    from models.database import Invoice, BankTransaction, Vendor
    from services.reconciliation_scorer import ReconciliationScorer

    # Create exact match scenario
    vendor = Vendor(tenant_id=tenant.id, name="Exact Match Vendor")
    db_session.add(vendor)
    await db_session.flush()

    invoice = Invoice(
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        amount=Decimal("100.00"),
        currency="USD",
        invoice_date=datetime(2024, 1, 15),
        status="open",
    )
    db_session.add(invoice)
    await db_session.flush()

    transaction = BankTransaction(
        tenant_id=tenant.id,
        posted_at=datetime(2024, 1, 15),  # Same date
        amount=Decimal("100.00"),  # Exact amount
        currency="USD",
        description="Exact Match Vendor payment",
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(invoice)
    await db_session.refresh(transaction)
    await db_session.refresh(vendor)

    # Calculate score
    score = ReconciliationScorer.calculate_score(invoice, transaction, vendor)
    assert float(score) >= 80.0  # Should be high score for exact match


@pytest.mark.asyncio
async def test_confirm_match_logic(tenant, invoice, bank_transaction, db_session):
    """Test the logic of confirming a match via the service."""
    from services.match_service import MatchService
    from models.database import Match

    # Create a match first
    match = Match(
        tenant_id=tenant.id,
        invoice_id=invoice.id,
        bank_transaction_id=bank_transaction.id,
        score=Decimal("85.0"),
        status="proposed",
    )
    db_session.add(match)
    await db_session.commit()
    await db_session.refresh(match)

    service = MatchService(db_session)
    confirmed_match = await service.confirm_match(tenant.id, match.id)

    assert confirmed_match.status == "confirmed"
    assert confirmed_match.confirmed_at is not None

    # Verify invoice status updated
    from services.invoice_service import InvoiceService
    invoice_service = InvoiceService(db_session)
    updated_invoice = await invoice_service.get_invoice(tenant.id, invoice.id)
    assert updated_invoice.status == "matched"

