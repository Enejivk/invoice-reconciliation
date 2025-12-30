"""Match REST endpoints."""
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.match_service import MatchService
from api.schemas.match import MatchResponse

router = APIRouter(prefix="/tenants/{tenant_id}/matches", tags=["matches"])


@router.post("/{match_id}/confirm", response_model=MatchResponse)
async def confirm_match(
    tenant_id: int = Path(..., description="Tenant ID"),
    match_id: int = Path(..., description="Match ID"),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a proposed match."""
    service = MatchService(db)
    match = await service.confirm_match(tenant_id, match_id)
    return match

