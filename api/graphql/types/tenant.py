"""GraphQL tenant types."""
import strawberry
from datetime import datetime


@strawberry.type
class Tenant:
    """Tenant GraphQL type."""

    id: int
    name: str
    created_at: datetime

    @classmethod
    def from_model(cls, tenant):
        """Create from SQLAlchemy model."""
        return cls(
            id=tenant.id,
            name=tenant.name,
            created_at=tenant.created_at,
        )


@strawberry.input
class CreateTenantInput:
    """Input for creating a tenant."""

    name: str

