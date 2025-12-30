"""Tests for AI explanation."""
import pytest
from decimal import Decimal
from datetime import datetime


@pytest.mark.asyncio
async def test_ai_explanation_endpoint(client, tenant, invoice, bank_transaction):
    """Test AI explanation endpoint."""
    response = await client.get(
        f"/api/rest/tenants/{tenant.id}/reconcile/explain",
        params={
            "invoice_id": invoice.id,
            "transaction_id": bank_transaction.id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 0
    # Should have confidence even if AI is disabled (fallback)
    assert "confidence" in data


@pytest.mark.asyncio
async def test_ai_explanation_fallback(client, tenant, invoice, bank_transaction):
    """Test that AI explanation falls back gracefully."""
    from services.ai_explanation_service import AIExplanationService

    service = AIExplanationService()
    explanation = await service.explain_match(
        invoice, bank_transaction, Decimal("75.0"), None
    )

    assert "explanation" in explanation
    assert "confidence" in explanation
    assert len(explanation["explanation"]) > 0
    assert explanation["confidence"] in ["high", "medium", "low"]

