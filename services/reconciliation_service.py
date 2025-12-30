"""Reconciliation service."""
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Match, Invoice, BankTransaction, Vendor
from repositories.invoice_repository import InvoiceRepository
from repositories.bank_transaction_repository import BankTransactionRepository
from repositories.match_repository import MatchRepository
from services.reconciliation_scorer import ReconciliationScorer
from core.tenant import get_tenant_or_raise


class ReconciliationService:
    """Service for reconciliation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.transaction_repo = BankTransactionRepository(db)
        self.match_repo = MatchRepository(db)

    async def reconcile(self, tenant_id: int, min_score: float = 50.0) -> List[Match]:
        """Run reconciliation and generate match candidates.

        Strategy: One-to-one matching
        - For each open invoice, find the best matching transaction
        - Only create matches above min_score threshold
        - Each transaction can only match one invoice (best match wins)

        Args:
            tenant_id: Tenant ID
            min_score: Minimum score threshold (0-100)

        Returns:
            List of match candidates
        """
        # Validate tenant exists
        await get_tenant_or_raise(self.db, tenant_id)

        # Get open invoices and unmatched transactions
        invoices = await self.invoice_repo.get_open_invoices(tenant_id)
        transactions = await self.transaction_repo.get_unmatched_transactions(tenant_id)

        if not invoices or not transactions:
            return []

        # Get vendors for invoices
        from sqlalchemy import select, and_
        from models.database import Vendor

        vendor_ids = {inv.vendor_id for inv in invoices if inv.vendor_id}
        vendors = {}
        if vendor_ids:
            result = await self.db.execute(
                select(Vendor).where(
                    and_(Vendor.id.in_(vendor_ids), Vendor.tenant_id == tenant_id)
                )
            )
            vendors = {v.id: v for v in result.scalars().all()}

        # Generate match candidates
        candidates: List[tuple[Invoice, BankTransaction, float]] = []

        for invoice in invoices:
            best_match = None
            best_score = 0.0

            for transaction in transactions:
                vendor = vendors.get(invoice.vendor_id) if invoice.vendor_id else None
                score = float(
                    ReconciliationScorer.calculate_score(invoice, transaction, vendor)
                )

                if score >= min_score and score > best_score:
                    best_match = transaction
                    best_score = score

            if best_match:
                candidates.append((invoice, best_match, best_score))

        # Create match records (remove duplicates - one transaction can only match one invoice)
        # Sort by score descending, then assign matches greedily
        candidates.sort(key=lambda x: x[2], reverse=True)

        created_matches: List[Match] = []
        used_transactions = set()

        for invoice, transaction, score in candidates:
            # Skip if transaction already matched
            if transaction.id in used_transactions:
                continue

            # Check if match already exists
            from sqlalchemy import select, and_
            from models.database import Match

            existing_query = select(Match).where(
                and_(
                    Match.tenant_id == tenant_id,
                    Match.invoice_id == invoice.id,
                    Match.bank_transaction_id == transaction.id,
                )
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update score if better
                if score > float(existing.score):
                    existing.score = score
                    await self.match_repo.update(existing)
                    created_matches.append(existing)
                continue

            # Create new match
            match = Match(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                bank_transaction_id=transaction.id,
                score=score,
                status="proposed",
            )

            created_match = await self.match_repo.create(match)
            created_matches.append(created_match)
            used_transactions.add(transaction.id)

        # Commit all matches
        await self.db.commit()

        return created_matches

    async def get_match_candidates(
        self, tenant_id: int, invoice_id: int = None, transaction_id: int = None
    ) -> List[Match]:
        """Get match candidates for an invoice or transaction."""
        if invoice_id:
            return await self.match_repo.get_candidates_for_invoice(
                tenant_id, invoice_id
            )
        elif transaction_id:
            return await self.match_repo.get_candidates_for_transaction(
                tenant_id, transaction_id
            )
        else:
            return await self.match_repo.get_all_candidates(tenant_id)

