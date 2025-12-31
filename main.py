"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from api.rest import api_router
from api.graphql.schema import schema
from api.graphql.context import GraphQLContext

app = FastAPI(
    title="Invoice Reconciliation API",
    description="Multi-Tenant Invoice Reconciliation API with REST and GraphQL",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_context() -> GraphQLContext:
    """Get GraphQL context."""
    async for db in get_db():
        return GraphQLContext(db=db, tenant_id=None)


# REST API routes
app.include_router(api_router, prefix="/api/rest")

# GraphQL endpoint
graphql_app = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
)
app.include_router(graphql_app, prefix="/api/graphql")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Invoice Reconciliation API",
        "docs": "/docs",
        "graphql": "/api/graphql",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (unique constraints)."""
    # Check for unique violation (postgres specific, but generic enough for now)
    # The string check is a safety net if pgcode is not available
    if "unique constraint" in str(exc.orig).lower() or (
        hasattr(exc.orig, "pgcode") and exc.orig.pgcode == "23505"
    ):
        return JSONResponse(
            status_code=409,
            content={"detail": "Duplicate entry detected. This record already exists."},
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error (Database Integrity)"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

