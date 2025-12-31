"""SQLAlchemy database models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base


class Tenant(Base):
    """Tenant model."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    vendors = relationship("Vendor", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    bank_transactions = relationship(
        "BankTransaction", back_populates="tenant", cascade="all, delete-orphan"
    )
    matches = relationship("Match", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"


class Vendor(Base):
    """Vendor model."""

    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="vendors")
    invoices = relationship("Invoice", back_populates="vendor", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("idx_vendor_tenant", "tenant_id"),
        Index("idx_vendor_tenant_name", "tenant_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, tenant_id={self.tenant_id}, name={self.name})>"


class Invoice(Base):
    """Invoice model."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(BigInteger, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(255), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(
        String(50),
        default="open",
        nullable=False,
        server_default="open",
    )  # open, matched, paid
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    matches = relationship("Match", back_populates="invoice", cascade="all, delete-orphan")

    # Indexes for performance and filtering
    __table_args__ = (
        Index("idx_invoice_tenant", "tenant_id"),
        Index("idx_invoice_tenant_status", "tenant_id", "status"),
        Index("idx_invoice_tenant_vendor", "tenant_id", "vendor_id"),
        Index("idx_invoice_tenant_date", "tenant_id", "invoice_date"),
        Index("idx_invoice_tenant_amount", "tenant_id", "amount"),
        CheckConstraint("amount >= 0", name="check_invoice_amount_positive"),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount})>"


class BankTransaction(Base):
    """Bank transaction model."""

    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255), nullable=True)  # External system ID for idempotency
    posted_at = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    description = Column(Text, nullable=True)  # Bank memo/description
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="bank_transactions")
    matches = relationship("Match", back_populates="bank_transaction", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("idx_bank_transaction_tenant", "tenant_id"),
        Index("idx_bank_transaction_tenant_external", "tenant_id", "external_id"),
        Index("idx_bank_transaction_tenant_posted", "tenant_id", "posted_at"),
        Index("idx_bank_transaction_tenant_amount", "tenant_id", "amount"),
        UniqueConstraint("tenant_id", "external_id", name="uq_bank_transaction_tenant_external"),
    )

    def __repr__(self) -> str:
        return f"<BankTransaction(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount})>"


class Match(Base):
    """Match model for invoice-transaction matches."""

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    bank_transaction_id = Column(
        BigInteger, ForeignKey("bank_transactions.id", ondelete="CASCADE"), nullable=False
    )
    score = Column(Numeric(5, 2), nullable=False)  # 0-100 confidence score
    status = Column(
        String(50),
        default="proposed",
        nullable=False,
        server_default="proposed",
    )  # proposed, confirmed, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="matches")
    invoice = relationship("Invoice", back_populates="matches")
    bank_transaction = relationship("BankTransaction", back_populates="matches")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "invoice_id", "bank_transaction_id", name="uq_match_tenant_invoice_transaction"
        ),
        Index("idx_match_tenant", "tenant_id"),
        Index("idx_match_tenant_status", "tenant_id", "status"),
        Index("idx_match_tenant_invoice", "tenant_id", "invoice_id"),
        Index("idx_match_tenant_transaction", "tenant_id", "bank_transaction_id"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_match_score_range"),
    )

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, tenant_id={self.tenant_id}, score={self.score}, status={self.status})>"


class IdempotencyKey(Base):
    """Idempotency key storage for bank transaction imports."""

    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)  # SHA-256 hash of request payload
    response_data = Column(Text, nullable=True)  # JSON response cached
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Unique constraint: same tenant + %key can only exist once
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_idempotency_tenant_key"),
        Index("idx_idempotency_tenant_key", "tenant_id", "key"),
    )

    def __repr__(self) -> str:
        return f"<IdempotencyKey(id={self.id}, tenant_id={self.tenant_id}, key={self.key[:20]}...)>"

