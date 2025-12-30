"""GraphQL match types."""
import strawberry
from datetime import datetime
from decimal import Decimal
from typing import Optional


@strawberry.type
class Match:
    """Match GraphQL type."""

    id: int
    tenant_id: int
    invoice_id: int
    bank_transaction_id: int
    score: Decimal
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime]

    @classmethod
    def from_model(cls, match):
        """Create from SQLAlchemy model."""
        return cls(
            id=match.id,
            tenant_id=match.tenant_id,
            invoice_id=match.invoice_id,
            bank_transaction_id=match.bank_transaction_id,
            score=match.score,
            status=match.status,
            created_at=match.created_at,
            confirmed_at=match.confirmed_at,
        )


@strawberry.type
class Explanation:
    """AI explanation GraphQL type."""

    explanation: str
    confidence: Optional[str] = None

