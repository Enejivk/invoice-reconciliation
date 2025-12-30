"""Bank transaction service."""
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import BankTransaction
from repositories.bank_transaction_repository import BankTransactionRepository
from repositories.idempotency_repository import IdempotencyRepository
from core.tenant import get_tenant_or_raise
from core.exceptions import IdempotencyConflictError


class BankTransactionService:
    """Service for bank transaction operations."""

    def __init__(self, db: AsyncSession):
        self.repository = BankTransactionRepository(db)
        self.idempotency_repo = IdempotencyRepository(db)

    def _hash_request(self, data: Any) -> str:
        """Hash request payload for idempotency."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def import_transactions(
        self,
        tenant_id: int,
        transactions: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import bank transactions with idempotency support.

        Args:
            tenant_id: Tenant ID
            transactions: List of transaction data
            idempotency_key: Optional idempotency key

        Returns:
            Dict with 'count' and 'transaction_ids'
        """
        # Validate tenant exists
        await get_tenant_or_raise(self.repository.db, tenant_id)

        # Handle idempotency
        if idempotency_key:
            request_hash = self._hash_request(transactions)
            endpoint = "/tenants/{tenant_id}/bank-transactions/import"

            try:
                idempotency_record, is_new = await self.idempotency_repo.create_or_get(
                    tenant_id=tenant_id,
                    key=idempotency_key,
                    endpoint=endpoint,
                    request_hash=request_hash,
                )

                if not is_new:
                    # Return cached response
                    if idempotency_record.response_data:
                        return json.loads(idempotency_record.response_data)
                    # If no cached response, proceed (shouldn't happen, but handle gracefully)
            except IdempotencyConflictError:
                raise

        # Import transactions
        imported_transactions = []
        for tx_data in transactions:
            transaction = BankTransaction(
                tenant_id=tenant_id,
                external_id=tx_data.get("external_id"),
                posted_at=datetime.fromisoformat(tx_data["posted_at"].replace("Z", "+00:00"))
                if isinstance(tx_data["posted_at"], str)
                else tx_data["posted_at"],
                amount=Decimal(str(tx_data["amount"])),
                currency=tx_data.get("currency", "USD"),
                description=tx_data.get("description"),
            )
            imported_transaction = await self.repository.create(transaction)
            imported_transactions.append(imported_transaction)

        # Commit transaction
        await self.repository.db.commit()

        # Store response in idempotency record if exists
        response_data = {
            "count": len(imported_transactions),
            "transaction_ids": [tx.id for tx in imported_transactions],
        }

        if idempotency_key:
            idempotency_record.response_data = json.dumps(response_data)
            await self.idempotency_repo.update(idempotency_record)
            await self.repository.db.commit()

        return response_data

    async def list_transactions(
        self,
        tenant_id: int,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BankTransaction]:
        """List bank transactions with optional filters."""
        return await self.repository.list(
            tenant_id=tenant_id, filters=filters or {}, limit=limit, offset=offset
        )

    async def get_unmatched_transactions(
        self, tenant_id: int
    ) -> List[BankTransaction]:
        """Get transactions that haven't been matched."""
        return await self.repository.get_unmatched_transactions(tenant_id)

    async def delete_transaction(self, tenant_id: int, transaction_id: int) -> None:
        """Delete a bank transaction."""
        transaction = await self.repository.get_by_id(tenant_id, transaction_id)
        if not transaction:
            from core.exceptions import NotFoundError
            raise NotFoundError(f"Bank transaction {transaction_id} not found")
        
        await self.repository.delete(transaction)
        await self.repository.db.flush()

