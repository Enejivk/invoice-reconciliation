"""GraphQL bank transaction types."""
import strawberry
from datetime import datetime
from decimal import Decimal
from typing import Optional


@strawberry.type
class BankTransaction:
    """Bank transaction GraphQL type."""

    id: int
    tenant_id: int
    external_id: Optional[str]
    posted_at: datetime
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime

    @classmethod
    def from_model(cls, transaction):
        """Create from SQLAlchemy model."""
        return cls(
            id=transaction.id,
            tenant_id=transaction.tenant_id,
            external_id=transaction.external_id,
            posted_at=transaction.posted_at,
            amount=transaction.amount,
            currency=transaction.currency,
            description=transaction.description,
            created_at=transaction.created_at,
        )


@strawberry.input
class BankTransactionInput:
    """Input for bank transaction."""

    external_id: Optional[str] = None
    posted_at: datetime
    amount: float
    currency: str = "USD"
    description: Optional[str] = None


@strawberry.input
class ImportBankTransactionsInput:
    """Input for importing bank transactions."""

    transactions: list[BankTransactionInput]
    idempotency_key: Optional[str] = None

