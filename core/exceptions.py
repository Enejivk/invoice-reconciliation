"""Custom exceptions."""
from fastapi import HTTPException, status


class TenantNotFoundError(HTTPException):
    """Raised when tenant is not found."""

    def __init__(self, tenant_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )


class TenantMismatchError(HTTPException):
    """Raised when tenant ID mismatch is detected."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch - unauthorized access",
        )


class IdempotencyConflictError(HTTPException):
    """Raised when idempotency key conflict occurs."""

    def __init__(self, message: str = "Idempotency key conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )


class InvoiceNotFoundError(HTTPException):
    """Raised when invoice is not found."""

    def __init__(self, invoice_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )


class MatchNotFoundError(HTTPException):
    """Raised when match is not found."""

    def __init__(self, match_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} not found",
        )


class ValidationError(HTTPException):
    """Raised when validation fails."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

