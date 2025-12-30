"""GraphQL context."""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GraphQLContext:
    """GraphQL request context."""

    db: AsyncSession
    tenant_id: int | None = None

    def ensure_tenant(self, tenant_id: int) -> None:
        """Ensure tenant ID matches context tenant."""
        if self.tenant_id and self.tenant_id != tenant_id:
            from core.exceptions import TenantMismatchError

            raise TenantMismatchError()

