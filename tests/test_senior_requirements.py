import pytest
from decimal import Decimal
from datetime import datetime

@pytest.mark.asyncio
async def test_multi_tenant_isolation(client, db_session):
    """Test that tenants cannot see each other's data."""
    # Create two tenants
    from models.database import Tenant, Invoice
    
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.commit()
    await db_session.refresh(tenant_a)
    await db_session.refresh(tenant_b)
    
    # Create an invoice for Tenant A
    invoice_a = Invoice(
        tenant_id=tenant_a.id,
        amount=Decimal("100.00"),
        currency="USD",
        description="Tenant A Invoice",
        status="open"
    )
    db_session.add(invoice_a)
    await db_session.commit()
    
    # Try to access Tenant A's invoice using Tenant B's context
    # This should return 404 because the repository filters by tenant_id
    response = await client.get(f"/api/rest/tenants/{tenant_b.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    invoice_ids = [inv["id"] for inv in data["invoices"]]
    assert invoice_a.id not in invoice_ids
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_delete_bank_transaction(client, tenant, bank_transaction):
    """Test deleting a bank transaction."""
    response = await client.delete(
        f"/api/rest/tenants/{tenant.id}/bank-transactions/{bank_transaction.id}"
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    response = await client.get(f"/api/rest/tenants/{tenant.id}/bank-transactions")
    data = response.json()
    tx_ids = [tx["id"] for tx in data["transactions"]]
    assert bank_transaction.id not in tx_ids
