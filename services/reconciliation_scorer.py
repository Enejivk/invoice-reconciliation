"""Reconciliation scoring algorithm."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from models.database import Invoice, BankTransaction, Vendor


class ReconciliationScorer:
    """Deterministic scoring algorithm for invoice-transaction matching."""

    # Scoring weights
    AMOUNT_WEIGHT = 40  # 0-40 points
    DATE_WEIGHT = 30  # 0-30 points
    TEXT_WEIGHT = 20  # 0-20 points
    CURRENCY_WEIGHT = 10  # 0-10 points
    MAX_SCORE = 100

    @staticmethod
    def calculate_score(
        invoice: Invoice,
        transaction: BankTransaction,
        vendor: Optional[Vendor] = None,
    ) -> Decimal:
        """Calculate match score between invoice and transaction.

        Scoring breakdown:
        - Amount match: 0-40 points (exact = 40, within 1% = 35, within 5% = 25, within 10% = 15)
        - Date proximity: 0-30 points (same day = 30, ±1 day = 25, ±3 days = 20, ±7 days = 10, ±30 days = 5)
        - Text similarity: 0-20 points (vendor name = 15, description keywords = 10, text ratio = 5-10)
        - Currency match: 0-10 points (same = 10, different = 0)

        Returns:
            Score from 0-100
        """
        amount_score = ReconciliationScorer._score_amount_match(
            invoice.amount, transaction.amount
        )
        date_score = ReconciliationScorer._score_date_proximity(
            invoice.invoice_date, transaction.posted_at
        )
        text_score = ReconciliationScorer._score_text_similarity(
            invoice, transaction, vendor
        )
        currency_score = ReconciliationScorer._score_currency_match(
            invoice.currency, transaction.currency
        )

        total_score = amount_score + date_score + text_score + currency_score
        return Decimal(str(min(total_score, ReconciliationScorer.MAX_SCORE)))

    @staticmethod
    def _score_amount_match(invoice_amount: Decimal, transaction_amount: Decimal) -> float:
        """Score amount match: 0-40 points."""
        if invoice_amount == transaction_amount:
            return 40.0

        # Calculate percentage difference
        diff = abs(float(invoice_amount - transaction_amount))
        avg = abs(float((invoice_amount + transaction_amount) / 2))
        if avg == 0:
            return 0.0

        pct_diff = diff / avg

        if pct_diff <= 0.01:  # Within 1%
            return 35.0
        elif pct_diff <= 0.05:  # Within 5%
            return 25.0
        elif pct_diff <= 0.10:  # Within 10%
            return 15.0
        else:
            return max(0.0, 15.0 - (pct_diff - 0.10) * 50)  # Degrade beyond 10%

    @staticmethod
    def _score_date_proximity(
        invoice_date: Optional[datetime], transaction_date: datetime
    ) -> float:
        """Score date proximity: 0-30 points."""
        if not invoice_date:
            return 0.0

        # Normalize to dates (ignore time)
        invoice_day = invoice_date.date()
        transaction_day = transaction_date.date()

        if invoice_day == transaction_day:
            return 30.0

        days_diff = abs((invoice_day - transaction_day).days)

        if days_diff == 1:
            return 25.0
        elif days_diff <= 3:
            return 20.0
        elif days_diff <= 7:
            return 10.0
        elif days_diff <= 30:
            return 5.0
        else:
            return max(0.0, 5.0 - (days_diff - 30) * 0.1)  # Degrade beyond 30 days

    @staticmethod
    def _score_text_similarity(
        invoice: Invoice, transaction: BankTransaction, vendor: Optional[Vendor]
    ) -> float:
        """Score text similarity: 0-20 points."""
        score = 0.0

        # Vendor name match (15 points)
        if vendor and vendor.name:
            vendor_name_lower = vendor.name.lower()
            transaction_desc_lower = (transaction.description or "").lower()
            invoice_desc_lower = (invoice.description or "").lower()

            if vendor_name_lower in transaction_desc_lower or vendor_name_lower in invoice_desc_lower:
                score += 15.0

        # Description keyword matching (10 points)
        if invoice.description and transaction.description:
            invoice_words = set(invoice.description.lower().split())
            transaction_words = set(transaction.description.lower().split())
            common_words = invoice_words.intersection(transaction_words)

            if len(common_words) > 0:
                # Simple ratio of common words
                ratio = len(common_words) / max(len(invoice_words), len(transaction_words))
                score += min(10.0, ratio * 10.0)

        # Invoice number in transaction description (5 points)
        if invoice.invoice_number and transaction.description:
            if invoice.invoice_number.lower() in transaction.description.lower():
                score += 5.0

        return min(score, 20.0)

    @staticmethod
    def _score_currency_match(invoice_currency: str, transaction_currency: str) -> float:
        """Score currency match: 0-10 points."""
        if invoice_currency.upper() == transaction_currency.upper():
            return 10.0
        return 0.0

