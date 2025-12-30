"""Pytest configuration and fixtures."""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from models.database import Tenant, Vendor, Invoice, BankTransaction, Match
from main import app
from sqlalchemy import select


# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session():
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield TestSessionLocal()
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session):
    """Create test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def vendor(db_session: AsyncSession, tenant: Tenant) -> Vendor:
    """Create a test vendor."""
    vendor = Vendor(tenant_id=tenant.id, name="Test Vendor")
    db_session.add(vendor)
    await db_session.commit()
    await db_session.refresh(vendor)
    return vendor


@pytest.fixture
async def invoice(db_session: AsyncSession, tenant: Tenant, vendor: Vendor) -> Invoice:
    """Create a test invoice."""
    invoice = Invoice(
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        invoice_number="INV-001",
        amount=Decimal("100.00"),
        currency="USD",
        invoice_date=datetime(2024, 1, 15),
        description="Test invoice",
        status="open",
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def bank_transaction(db_session: AsyncSession, tenant: Tenant) -> BankTransaction:
    """Create a test bank transaction."""
    transaction = BankTransaction(
        tenant_id=tenant.id,
        external_id="TXN-001",
        posted_at=datetime(2024, 1, 16),
        amount=Decimal("100.00"),
        currency="USD",
        description="Payment for invoice",
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction

