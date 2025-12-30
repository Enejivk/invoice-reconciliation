"""Tests for invoice endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime


@pytest.mark.asyncio
async def test_create_invoice(client, tenant):
    """Test creating an invoice."""
    response = await client.post(
        f"/api/rest/tenants/{tenant.id}/invoices",
        json={
            "amount": 150.50,
            "currency": "USD",
            "invoice_number": "INV-002",
            "description": "Test invoice creation",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "150.50"
    assert data["currency"] == "USD"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_list_invoices(client, tenant, invoice):
    """Test listing invoices."""
    response = await client.get(f"/api/rest/tenants/{tenant.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    assert len(data["invoices"]) >= 1
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_invoices_with_status_filter(client, tenant, invoice):
    """Test listing invoices with status filter."""
    response = await client.get(
        f"/api/rest/tenants/{tenant.id}/invoices?status=open"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(inv["status"] == "open" for inv in data["invoices"])


@pytest.mark.asyncio
async def test_list_invoices_with_amount_filter(client, tenant, invoice):
    """Test listing invoices with amount filter."""
    response = await client.get(
        f"/api/rest/tenants/{tenant.id}/invoices?min_amount=50&max_amount=200"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(
        Decimal(inv["amount"]) >= 50 and Decimal(inv["amount"]) <= 200
        for inv in data["invoices"]
    )


@pytest.mark.asyncio
async def test_delete_invoice(client, tenant, invoice):
    """Test deleting an invoice."""
    response = await client.delete(
        f"/api/rest/tenants/{tenant.id}/invoices/{invoice.id}"
    )
    assert response.status_code == 204

    # Verify it's deleted by listing invoices
    response = await client.get(f"/api/rest/tenants/{tenant.id}/invoices")
    assert response.status_code == 200
    invoice_ids = [inv["id"] for inv in response.json()["invoices"]]
    assert invoice.id not in invoice_ids

