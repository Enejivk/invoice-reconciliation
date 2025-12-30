"""Tests for bank transaction endpoints."""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_import_bank_transactions(client, tenant):
    """Test importing bank transactions."""
    transactions = [
        {
            "external_id": "TXN-001",
            "posted_at": "2024-01-20T10:00:00Z",
            "amount": 200.00,
            "currency": "USD",
            "description": "Payment received",
        },
        {
            "external_id": "TXN-002",
            "posted_at": "2024-01-21T10:00:00Z",
            "amount": 150.50,
            "currency": "USD",
            "description": "Another payment",
        },
    ]

    response = await client.post(
        f"/api/rest/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 2
    assert len(data["transaction_ids"]) == 2


@pytest.mark.asyncio
async def test_import_bank_transactions_idempotency(client, tenant):
    """Test idempotency of bank transaction import."""
    transactions = [
        {
            "external_id": "TXN-IDEMPOTENT",
            "posted_at": "2024-01-20T10:00:00Z",
            "amount": 300.00,
            "currency": "USD",
            "description": "Idempotent transaction",
        }
    ]

    idempotency_key = "test-key-123"

    # First import
    response1 = await client.post(
        f"/api/rest/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
        headers={"X-Idempotency-Key": idempotency_key},
    )
    assert response1.status_code == 201
    data1 = response1.json()
    transaction_ids_1 = data1["transaction_ids"]

    # Second import with same key - should return same result
    response2 = await client.post(
        f"/api/rest/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
        headers={"X-Idempotency-Key": idempotency_key},
    )
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["transaction_ids"] == transaction_ids_1

    # Third import with same key but different payload - should conflict
    different_transactions = [
        {
            "external_id": "TXN-DIFFERENT",
            "posted_at": "2024-01-20T10:00:00Z",
            "amount": 400.00,
            "currency": "USD",
            "description": "Different transaction",
        }
    ]
    response3 = await client.post(
        f"/api/rest/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": different_transactions},
        headers={"X-Idempotency-Key": idempotency_key},
    )
    assert response3.status_code == 409  # Conflict

