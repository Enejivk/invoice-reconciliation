"""GraphQL queries."""
import strawberry
from typing import Optional, List
from datetime import datetime

from api.graphql.context import GraphQLContext
from api.graphql.types.tenant import Tenant
from api.graphql.types.invoice import Invoice, InvoiceFilters
from api.graphql.types.bank_transaction import BankTransaction
from api.graphql.types.match import Match, Explanation
from services.tenant_service import TenantService
from services.invoice_service import InvoiceService
from services.bank_transaction_service import BankTransactionService
from services.reconciliation_service import ReconciliationService
from services.ai_explanation_service import AIExplanationService
from services.reconciliation_scorer import ReconciliationScorer


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    async def tenants(
        self, info, limit: int = 100, offset: int = 0
    ) -> List[Tenant]:
        """List all tenants."""
        context: GraphQLContext = info.context
        service = TenantService(context.db)
        tenants = await service.list_tenants(limit=limit, offset=offset)
        return [Tenant.from_model(t) for t in tenants]

    @strawberry.field
    async def invoices(
        self,
        info,
        tenant_id: int,
        filters: Optional[InvoiceFilters] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Invoice]:
        """List invoices with optional filters."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = InvoiceService(context.db)

        filter_dict = {}
        if filters:
            if filters.status:
                filter_dict["status"] = filters.status
            if filters.vendor_id:
                filter_dict["vendor_id"] = filters.vendor_id
            if filters.min_amount:
                filter_dict["min_amount"] = filters.min_amount
            if filters.max_amount:
                filter_dict["max_amount"] = filters.max_amount
            if filters.start_date:
                filter_dict["start_date"] = filters.start_date
            if filters.end_date:
                filter_dict["end_date"] = filters.end_date

        invoices = await service.list_invoices(
            tenant_id=tenant_id, filters=filter_dict, limit=limit, offset=offset
        )
        return [Invoice.from_model(inv) for inv in invoices]

    @strawberry.field
    async def bank_transactions(
        self,
        info,
        tenant_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BankTransaction]:
        """List bank transactions."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = BankTransactionService(context.db)
        transactions = await service.list_transactions(
            tenant_id=tenant_id, limit=limit, offset=offset
        )
        return [BankTransaction.from_model(tx) for tx in transactions]

    @strawberry.field
    async def match_candidates(
        self,
        info,
        tenant_id: int,
        invoice_id: Optional[int] = None,
        transaction_id: Optional[int] = None,
    ) -> List[Match]:
        """Get match candidates."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        service = ReconciliationService(context.db)
        matches = await service.get_match_candidates(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            transaction_id=transaction_id,
        )
        return [Match.from_model(m) for m in matches]

    @strawberry.field
    async def explain_reconciliation(
        self,
        info,
        tenant_id: int,
        invoice_id: int,
        transaction_id: int,
    ) -> Explanation:
        """Get AI explanation for a match decision."""
        context: GraphQLContext = info.context
        context.ensure_tenant(tenant_id)

        # Get invoice and transaction
        invoice_service = InvoiceService(context.db)
        invoice = await invoice_service.get_invoice(tenant_id, invoice_id)

        transaction_service = BankTransactionService(context.db)
        transaction = await transaction_service.repository.get_by_id(
            tenant_id, transaction_id
        )
        if not transaction:
            from core.exceptions import ValidationError
            raise ValidationError(f"Transaction {transaction_id} not found")

        # Get vendor if exists
        vendor_name = None
        if invoice.vendor_id:
            from sqlalchemy import select
            from models.database import Vendor
            result = await context.db.execute(
                select(Vendor).where(Vendor.id == invoice.vendor_id)
            )
            vendor = result.scalar_one_or_none()
            if vendor:
                vendor_name = vendor.name

        # Calculate score
        score = ReconciliationScorer.calculate_score(invoice, transaction, vendor)

        # Get explanation
        ai_service = AIExplanationService()
        explanation = await ai_service.explain_match(
            invoice, transaction, score, vendor_name
        )

        return Explanation(**explanation)

