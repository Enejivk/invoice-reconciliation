"""AI explanation service with graceful fallback."""
import json
import logging
from typing import Optional
from decimal import Decimal

from core.config import settings
from models.database import Invoice, BankTransaction
from services.reconciliation_scorer import ReconciliationScorer

logger = logging.getLogger(__name__)


class AIExplanationService:
    """Service for generating AI-powered explanations with fallback."""

    def __init__(self):
        self.enabled = settings.ai_enabled and bool(settings.openai_api_key)
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def explain_match(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: Decimal,
        vendor_name: Optional[str] = None,
    ) -> dict[str, str]:
        """Generate explanation for a match.

        Returns:
            Dict with 'explanation' and optional 'confidence' fields
        """
        if not self.enabled:
            return self._fallback_explanation(invoice, transaction, score, vendor_name)

        try:
            return await self._call_llm(invoice, transaction, score, vendor_name)
        except Exception as e:
            logger.warning(f"AI explanation failed: {e}, using fallback")
            return self._fallback_explanation(invoice, transaction, score, vendor_name)

    async def _call_llm(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: Decimal,
        vendor_name: Optional[str],
    ) -> dict[str, str]:
        """Call LLM API for explanation."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Build context (only tenant-authorized data)
            context = {
                "invoice": {
                    "amount": str(invoice.amount),
                    "currency": invoice.currency,
                    "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    "invoice_number": invoice.invoice_number,
                    "description": invoice.description,
                    "vendor": vendor_name,
                },
                "transaction": {
                    "amount": str(transaction.amount),
                    "currency": transaction.currency,
                    "posted_at": transaction.posted_at.isoformat(),
                    "description": transaction.description,
                },
                "match_score": str(score),
            }

            prompt = f"""You are analyzing a potential match between an invoice and a bank transaction.

Invoice:
- Amount: {context['invoice']['amount']} {context['invoice']['currency']}
- Date: {context['invoice']['invoice_date'] or 'Not specified'}
- Invoice Number: {context['invoice']['invoice_number'] or 'Not specified'}
- Vendor: {context['invoice']['vendor'] or 'Not specified'}
- Description: {context['invoice']['description'] or 'Not specified'}

Bank Transaction:
- Amount: {context['transaction']['amount']} {context['transaction']['currency']}
- Posted Date: {context['transaction']['posted_at']}
- Description: {context['transaction']['description'] or 'Not specified'}

Match Score: {score}/100

Provide a concise explanation (2-6 sentences) of why this is or isn't a good match. Focus on:
1. Amount comparison
2. Date proximity
3. Any matching identifiers or descriptions
4. Overall confidence level

Return a JSON object with 'explanation' (string) and 'confidence' (string: 'high', 'medium', or 'low').
"""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial reconciliation assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            return {
                "explanation": result.get("explanation", "AI explanation unavailable"),
                "confidence": result.get("confidence", "medium"),
            }

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    def _fallback_explanation(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: Decimal,
        vendor_name: Optional[str],
    ) -> dict[str, str]:
        """Generate deterministic fallback explanation."""
        reasons = []
        confidence = "low"

        # Amount analysis
        amount_diff = abs(float(invoice.amount - transaction.amount))
        amount_pct = (
            (amount_diff / float(invoice.amount)) * 100 if float(invoice.amount) > 0 else 100
        )

        if amount_diff == 0:
            reasons.append("exact amount match")
            confidence = "high"
        elif amount_pct <= 1:
            reasons.append(f"amount match within 1% (difference: {amount_pct:.2f}%)")
            confidence = "high"
        elif amount_pct <= 5:
            reasons.append(f"amount match within 5% (difference: {amount_pct:.2f}%)")
            confidence = "medium"
        elif amount_pct <= 10:
            reasons.append(f"amount match within 10% (difference: {amount_pct:.2f}%)")
            confidence = "medium"
        else:
            reasons.append(f"significant amount difference ({amount_pct:.2f}%)")
            confidence = "low"

        # Date analysis
        if invoice.invoice_date:
            days_diff = abs((invoice.invoice_date.date() - transaction.posted_at.date()).days)
            if days_diff == 0:
                reasons.append("same date")
                if confidence == "high":
                    pass  # Keep high
                else:
                    confidence = "medium"
            elif days_diff <= 3:
                reasons.append(f"dates within {days_diff} days")
            elif days_diff <= 7:
                reasons.append(f"dates within {days_diff} days")
            else:
                reasons.append(f"dates differ by {days_diff} days")

        # Currency
        if invoice.currency.upper() == transaction.currency.upper():
            reasons.append("same currency")
        else:
            reasons.append("different currencies")
            confidence = "low"

        # Vendor/description matching
        if vendor_name and transaction.description:
            if vendor_name.lower() in transaction.description.lower():
                reasons.append("vendor name found in transaction description")
                if confidence != "high":
                    confidence = "medium"

        # Build explanation
        explanation = f"This match has a score of {score}/100. "
        if reasons:
            explanation += "Key factors: " + ", ".join(reasons) + "."
        else:
            explanation += "Limited matching factors identified."

        return {
            "explanation": explanation,
            "confidence": confidence,
        }

