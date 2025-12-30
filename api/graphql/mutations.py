"""GraphQL mutations."""
import strawberry
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from api.graphql.context import GraphQLContext
from api.graphql.types.tenant import Tenant, CreateTenantInput
from api.graphql.types.invoice import Invoice, CreateInvoiceInput
from api.graphql.types.bank_transaction import BankTransaction, ImportBankTransactionsInput
from api.graphql.types.match import Match
from services.tenant_service import TenantService
from services.invoice_service import InvoiceService
from services.bank_transaction_service import BankTransactionService
from services.reconciliation_service import ReconciliationService
from services.match_service import MatchService


@strawberry.type
class ImportResult:
    """Result of bank transaction import."""

    success: bool
    imported_count: int
    transaction_ids: List[int]


@strawberry.type
class ReconciliationResult:
    """Result of reconciliation."""

    success: bool
    match_count: int
    matches: List[Match]


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    async def create_tenant(self, info, input: CreateTenantInput) -> Tenant:
        """Create a new tenant."""
        context: GraphQLContext = info.context
        service = TenantService(context.db)
        tenant = await service.create_tenant(input.name)
        await context.db.commit()
        return Tenant.from_model(tenant)

    @strawberry.mutation
    async def create_invoice(
        self, info, tenant_id: int, input: CreateInvoiceInput
    ) -> Invoice:
        """Create a new invoice."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = InvoiceService(context.db)
        invoice = await service.create_invoice(
            tenant_id=tenant_id,
            vendor_id=input.vendor_id,
            invoice_number=input.invoice_number,
            amount=Decimal(str(input.amount)),
            currency=input.currency,
            invoice_date=input.invoice_date,
            description=input.description,
        )
        await context.db.commit()
        return Invoice.from_model(invoice)

    @strawberry.mutation
    async def delete_invoice(
        self, info, tenant_id: int, invoice_id: int
    ) -> bool:
        """Delete an invoice."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = InvoiceService(context.db)
        await service.delete_invoice(tenant_id, invoice_id)
        await context.db.commit()
        return True

    @strawberry.mutation
    async def import_bank_transactions(
        self,
        info,
        tenant_id: int,
        input: ImportBankTransactionsInput,
    ) -> ImportResult:
        """Import bank transactions with idempotency support."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = BankTransactionService(context.db)

        transactions_data = [
            {
                "external_id": tx.external_id,
                "posted_at": tx.posted_at,
                "amount": tx.amount,
                "currency": tx.currency,
                "description": tx.description,
            }
            for tx in input.transactions
        ]

        result = await service.import_transactions(
            tenant_id=tenant_id,
            transactions=transactions_data,
            idempotency_key=input.idempotency_key,
        )

        return ImportResult(
            success=True,
            imported_count=result["count"],
            transaction_ids=result["transaction_ids"],
        )

    @strawberry.mutation
    async def reconcile(
        self,
        info,
        tenant_id: int,
        min_score: Optional[float] = 50.0,
    ) -> ReconciliationResult:
        """Run reconciliation and generate match candidates."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = ReconciliationService(context.db)
        matches = await service.reconcile(tenant_id, min_score=min_score or 50.0)

        return ReconciliationResult(
            success=True,
            match_count=len(matches),
            matches=[Match.from_model(m) for m in matches],
        )

    @strawberry.mutation
    async def confirm_match(
        self, info, tenant_id: int, match_id: int
    ) -> Match:
        """Confirm a proposed match."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = MatchService(context.db)
        match = await service.confirm_match(tenant_id, match_id)
        return Match.from_model(match)

