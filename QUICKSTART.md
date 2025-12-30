# Quick Start Guide

## Prerequisites

- Python 3.13+
- Docker (for PostgreSQL)
- pip

## Setup (5 minutes)

1. **Run setup script**

   ```bash
   ./setup.sh
   ```

   Or manually:

   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # Install dependencies
   pip install -e ".[dev]"

   # Copy environment file
   cp .env.example .env

   # Start PostgreSQL
   docker-compose up -d

   # Run migrations
   alembic upgrade head
   ```

2. **Start the server**

   ```bash
   uvicorn main:app --reload
   ```

3. **Access the APIs**
   - REST API Docs: http://localhost:8000/docs
   - GraphQL Playground: http://localhost:8000/api/graphql
   - Health Check: http://localhost:8000/health

## Frontend (Recommended)

For the best experience, use the included React frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000 in your browser.

The frontend provides a visual interface for:

- Creating tenants and invoices
- Importing transactions
- Running reconciliation
- Viewing matches with scores
- Getting explanations
- Confirming matches

## Quick Test (REST API)

### 1. Create a Tenant (REST)

```bash
curl -X POST http://localhost:8000/api/rest/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

### 2. Create an Invoice (REST)

```bash
curl -X POST http://localhost:8000/api/rest/tenants/1/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.00,
    "currency": "USD",
    "invoice_number": "INV-001",
    "description": "Monthly subscription"
  }'
```

### 3. Import Bank Transactions (REST)

```bash
curl -X POST http://localhost:8000/api/rest/tenants/1/bank-transactions/import \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: test-import-001" \
  -d '{
    "transactions": [
      {
        "external_id": "TXN-001",
        "posted_at": "2024-01-20T10:00:00Z",
        "amount": 1000.00,
        "currency": "USD",
        "description": "Payment received"
      }
    ]
  }'
```

### 4. Run Reconciliation (REST)

```bash
curl -X POST "http://localhost:8000/api/rest/tenants/1/reconcile?min_score=50.0"
```

### 5. Get AI Explanation (REST)

```bash
curl "http://localhost:8000/api/rest/tenants/1/reconcile/explain?invoice_id=1&transaction_id=1"
```

### 6. Confirm a Match (REST)

```bash
curl -X POST http://localhost:8000/api/rest/tenants/1/matches/1/confirm
```

## GraphQL Example

Visit http://localhost:8000/api/graphql and try:

```graphql
mutation {
  createTenant(input: { name: "Test Corp" }) {
    id
    name
  }
}

query {
  invoices(tenantId: 1) {
    id
    amount
    status
  }
}
```

## Run Tests

```bash
pytest
```

## Project Structure

```
invoice-reconciliation/
├── alembic/              # Database migrations
├── api/                  # API layer
│   ├── rest/            # REST endpoints
│   ├── graphql/         # GraphQL schema
│   └── schemas/         # Pydantic schemas
├── core/                # Core utilities
│   ├── config.py        # Configuration
│   ├── database.py      # DB session management
│   └── exceptions.py    # Custom exceptions
├── models/              # SQLAlchemy models
├── repositories/         # Data access layer
├── services/             # Business logic layer
│   ├── reconciliation_scorer.py  # Scoring algorithm
│   └── ai_explanation_service.py # AI integration
├── tests/                # Test suite
├── main.py               # FastAPI app
├── docker-compose.yml    # PostgreSQL setup
└── README.md             # Full documentation
```

## Key Features Demonstrated

✅ Multi-tenant isolation (RLS + application-level)  
✅ Shared service layer (REST + GraphQL)  
✅ Deterministic reconciliation scoring  
✅ AI explanations with fallback  
✅ Idempotent bulk imports  
✅ Comprehensive test suite  
✅ Clean architecture  
✅ Production-ready patterns

## Next Steps

1. Review the README.md for detailed design decisions
2. Explore the API docs at /docs
3. Try the GraphQL Playground
4. Run the test suite
5. Review the code structure

## Troubleshooting

**Database connection issues:**

- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in .env

**Migration issues:**

- Reset database: `docker-compose down -v && docker-compose up -d`
- Re-run migrations: `alembic upgrade head`

**Import errors:**

- Ensure Python 3.13+: `python3 --version`
- Reinstall dependencies: `pip install -e ".[dev]"`
