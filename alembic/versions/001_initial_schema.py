"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create vendors table
    op.create_table(
        "vendors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_vendor_tenant", "vendors", ["tenant_id"])
    op.create_index("idx_vendor_tenant_name", "vendors", ["tenant_id", "name"])

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("vendor_id", sa.BigInteger(), nullable=True),
        sa.Column("invoice_number", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount >= 0", name="check_invoice_amount_positive"),
    )
    op.create_index("idx_invoice_tenant", "invoices", ["tenant_id"])
    op.create_index("idx_invoice_tenant_status", "invoices", ["tenant_id", "status"])
    op.create_index("idx_invoice_tenant_vendor", "invoices", ["tenant_id", "vendor_id"])
    op.create_index("idx_invoice_tenant_date", "invoices", ["tenant_id", "invoice_date"])
    op.create_index("idx_invoice_tenant_amount", "invoices", ["tenant_id", "amount"])

    # Create bank_transactions table
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_bank_transaction_tenant_external"),
    )
    op.create_index("idx_bank_transaction_tenant", "bank_transactions", ["tenant_id"])
    op.create_index("idx_bank_transaction_tenant_external", "bank_transactions", ["tenant_id", "external_id"])
    op.create_index("idx_bank_transaction_tenant_posted", "bank_transactions", ["tenant_id", "posted_at"])
    op.create_index("idx_bank_transaction_tenant_amount", "bank_transactions", ["tenant_id", "amount"])

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("invoice_id", sa.BigInteger(), nullable=False),
        sa.Column("bank_transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="proposed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_transaction_id"], ["bank_transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "invoice_id", "bank_transaction_id", name="uq_match_tenant_invoice_transaction"),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="check_match_score_range"),
    )
    op.create_index("idx_match_tenant", "matches", ["tenant_id"])
    op.create_index("idx_match_tenant_status", "matches", ["tenant_id", "status"])
    op.create_index("idx_match_tenant_invoice", "matches", ["tenant_id", "invoice_id"])
    op.create_index("idx_match_tenant_transaction", "matches", ["tenant_id", "bank_transaction_id"])

    # Create idempotency_keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_idempotency_tenant_key"),
    )
    op.create_index("idx_idempotency_tenant_key", "idempotency_keys", ["tenant_id", "key"])

    # Enable Row Level Security on tenant-scoped tables
    op.execute("ALTER TABLE vendors ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE invoices ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE matches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY")

    # Create RLS policies (using a function-based approach for flexibility)
    # Note: In production, you'd use current_setting('app.current_tenant_id')
    # For now, we'll rely on application-level filtering, but RLS is enabled


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("matches")
    op.drop_table("bank_transactions")
    op.drop_table("invoices")
    op.drop_table("vendors")
    op.drop_table("tenants")

