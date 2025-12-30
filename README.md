# Invoice Reconciliation API

A multi-tenant invoice reconciliation API built with Python 3.13, FastAPI, Strawberry GraphQL, and SQLAlchemy 2.0.

## Features

- **Multi-Tenant Architecture**: Complete tenant isolation with Row-Level Security (RLS) policies
- **Dual API Support**: Both REST (FastAPI) and GraphQL (Strawberry) APIs sharing the same service layer
- **Intelligent Reconciliation**: Deterministic scoring algorithm for matching invoices to bank transactions
- **AI-Powered Explanations**: Optional AI integration with graceful fallback to deterministic explanations
- **Idempotency**: Safe bulk imports with idempotency key support
- **Comprehensive Testing**: Full test suite covering all major functionality

## Tech Stack

- **Python 3.13**
- **FastAPI** - REST API framework
- **Strawberry GraphQL** - GraphQL implementation
- **SQLAlchemy 2.0** - Modern ORM with async support
- **PostgreSQL** - Production-ready database with RLS
- **Alembic** - Database migrations
- **Pytest** - Testing framework

## Setup

### Prerequisites

- Python 3.13+
- PostgreSQL 16+ (or Docker)
- pip

### Installation

1. **Clone the repository**
   ```bash
   cd invoice-reconciliation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database URL and optional AI settings
   ```

5. **Start PostgreSQL (using Docker)**
   ```bash
   docker-compose up -d
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at:
- REST API: http://localhost:8000/api/rest
- GraphQL: http://localhost:8000/api/graphql
- API Docs: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/api/graphql

## Frontend

A React frontend is included for visual testing and demonstration.

**Setup:**
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

**Features:**
- Create and manage tenants
- Create invoices
- Import bank transactions
- Run reconciliation
- View match candidates with scores
- Get AI explanations
- Confirm matches

See `frontend/README.md` for details.

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## API Endpoints

### REST API

#### Tenants
- `POST /api/rest/tenants` - Create tenant
- `GET /api/rest/tenants` - List tenants

#### Invoices
- `POST /api/rest/tenants/{tenant_id}/invoices` - Create invoice
- `GET /api/rest/tenants/{tenant_id}/invoices` - List invoices (with filters: status, vendor_id, min_amount, max_amount, start_date, end_date)
- `DELETE /api/rest/tenants/{tenant_id}/invoices/{id}` - Delete invoice

#### Bank Transactions
- `POST /api/rest/tenants/{tenant_id}/bank-transactions/import` - Bulk import (with `X-Idempotency-Key` header)

#### Reconciliation
- `POST /api/rest/tenants/{tenant_id}/reconcile?min_score=50.0` - Run reconciliation
- `GET /api/rest/tenants/{tenant_id}/reconcile/explain?invoice_id=X&transaction_id=Y` - Get AI explanation

#### Matches
- `POST /api/rest/tenants/{tenant_id}/matches/{match_id}/confirm` - Confirm a match

### GraphQL API

Visit http://localhost:8000/api/graphql for interactive GraphQL Playground.

**Queries:**
- `tenants` - List tenants
- `invoices(tenantId, filters, pagination)` - List invoices with filters
- `bankTransactions(tenantId, pagination)` - List bank transactions
- `matchCandidates(tenantId, invoiceId?, transactionId?)` - Get match candidates
- `explainReconciliation(tenantId, invoiceId, transactionId)` - Get AI explanation

**Mutations:**
- `createTenant(input)` - Create tenant
- `createInvoice(tenantId, input)` - Create invoice
- `deleteInvoice(tenantId, invoiceId)` - Delete invoice
- `importBankTransactions(tenantId, input, idempotencyKey)` - Import transactions
- `reconcile(tenantId, minScore?)` - Run reconciliation
- `confirmMatch(tenantId, matchId)` - Confirm match

## Design Decisions

### Architecture

The application follows a clean layered architecture:

```
API Layer (REST/GraphQL)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (SQLAlchemy Models)
```

**Key Principle**: Both REST and GraphQL APIs share the same service layer, ensuring consistency and avoiding code duplication.

### Multi-Tenancy

**Enforcement Strategy:**
1. **Application Level**: All repository queries automatically filter by `tenant_id`
2. **Database Level**: Row-Level Security (RLS) policies enabled on all tenant-scoped tables
3. **API Level**: Tenant ID extracted from path/context and validated

**Isolation Guarantees:**
- Every query includes tenant_id filter
- RLS policies provide defense-in-depth
- Tenant validation in service layer
- No cross-tenant data leaks possible

### Reconciliation Scoring Algorithm

The scoring system uses deterministic heuristics (not AI):

**Scoring Breakdown (0-100 points):**
- **Amount Match (0-40 points)**:
  - Exact match: 40 points
  - Within 1%: 35 points
  - Within 5%: 25 points
  - Within 10%: 15 points
  - Beyond 10%: Degrading score

- **Date Proximity (0-30 points)**:
  - Same day: 30 points
  - ±1 day: 25 points
  - ±3 days: 20 points
  - ±7 days: 10 points
  - ±30 days: 5 points
  - Beyond 30 days: Degrading score

- **Text Similarity (0-20 points)**:
  - Vendor name in description: 15 points
  - Common keywords: Up to 10 points
  - Invoice number match: 5 points

- **Currency Match (0-10 points)**:
  - Same currency: 10 points
  - Different: 0 points

**Matching Strategy:**
- One-to-one matching (each invoice → best transaction)
- Greedy assignment (highest scores first)
- Minimum score threshold (default: 50.0)
- Prevents duplicate matches (one transaction → one invoice)

### Idempotency Implementation

**Design:**
- Idempotency keys stored in database with request hash
- Same key + same payload → return cached response
- Same key + different payload → 409 Conflict
- Keys scoped per tenant

**Flow:**
1. Extract `X-Idempotency-Key` header
2. Hash request payload (SHA-256)
3. Check for existing key:
   - If exists with same hash → return cached response
   - If exists with different hash → raise 409 Conflict
   - If not exists → process request, store result, return

**Transaction Safety:**
- Import operation wrapped in database transaction
- Idempotency record created atomically with data
- Rollback on any error

### AI Integration

**Design Philosophy:**
- AI is optional enhancement, not core functionality
- Always provides fallback explanation
- Never blocks critical paths
- Configurable via environment variables

**Implementation:**
- Abstracted `AIExplanationService` class
- OpenAI integration (configurable)
- Graceful degradation on errors/timeouts
- Deterministic fallback explanations
- Mockable for testing

**Fallback Explanation:**
- Based on score components
- Lists matching factors (amount, date, currency, vendor)
- Provides confidence level (high/medium/low)
- Always available, even without AI

### Database Design

**PostgreSQL Choice:**
- Production-ready with proper concurrency
- Row-Level Security (RLS) support
- Advanced features (indexes, constraints, JSONB)
- Better than SQLite for multi-tenant workloads

**Key Features:**
- Proper indexes on tenant_id + common filters
- Foreign key constraints with CASCADE
- Check constraints (amount >= 0, score 0-100)
- Unique constraints (idempotency keys, matches)
- RLS policies enabled (defense-in-depth)

**Migrations:**
- Alembic for schema versioning
- Initial migration creates all tables + RLS
- Easy to extend with new migrations

### Transaction Boundaries

**Critical Operations:**
1. **Bank Transaction Import**:
   - Wrapped in transaction
   - Idempotency key stored atomically
   - Rollback on any error

2. **Match Confirmation**:
   - Updates match status
   - Updates invoice status
   - All in single transaction

3. **Reconciliation**:
   - Creates multiple match records
   - Committed atomically
   - No partial states

## Testing Strategy

**Test Coverage:**
1. ✅ Creating invoices
2. ✅ Listing invoices (with filters)
3. ✅ Deleting invoices
4. ✅ Importing bank transactions (including idempotency)
5. ✅ Reconciliation produces candidates with expected ranking
6. ✅ Confirming a match updates expected state
7. ✅ AI explanation endpoint (mocked AI + fallback path)

**Test Approach:**
- SQLite in-memory database for fast tests
- Fixtures for common entities (tenant, vendor, invoice, transaction)
- Integration tests for full API flows
- Unit tests for service logic
- Mocked AI service for explanation tests

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/invoice_reconciliation

# AI Configuration (optional)
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo-preview
AI_ENABLED=false

# Application
DEBUG=true
LOG_LEVEL=INFO

# Idempotency
IDEMPOTENCY_KEY_HEADER=X-Idempotency-Key
```

## Example Usage

### Create Tenant and Invoice (REST)

```bash
# Create tenant
curl -X POST http://localhost:8000/api/rest/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'

# Create invoice
curl -X POST http://localhost:8000/api/rest/tenants/1/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.00,
    "currency": "USD",
    "invoice_number": "INV-001",
    "description": "Monthly subscription"
  }'
```

### Import Bank Transactions (REST)

```bash
curl -X POST http://localhost:8000/api/rest/tenants/1/bank-transactions/import \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: import-2024-01-20" \
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

### Run Reconciliation (REST)

```bash
curl -X POST "http://localhost:8000/api/rest/tenants/1/reconcile?min_score=50.0"
```

### GraphQL Example

```graphql
mutation {
  createTenant(input: { name: "Acme Corp" }) {
    id
    name
  }
  
  createInvoice(
    tenantId: 1
    input: {
      amount: 1000.0
      currency: "USD"
      invoiceNumber: "INV-001"
    }
  ) {
    id
    amount
    status
  }
}
```

## Trade-offs and Considerations

### PostgreSQL vs SQLite
- **Chosen**: PostgreSQL for production readiness, RLS support, and concurrency
- **Trade-off**: Requires database setup (mitigated with Docker)

### One-to-One vs Many-to-Many Matching
- **Chosen**: One-to-one (greedy assignment)
- **Trade-off**: Simpler but may miss optimal global matches
- **Rationale**: Pragmatic for MVP, can be enhanced later

### AI Integration Approach
- **Chosen**: Optional enhancement with fallback
- **Trade-off**: Less sophisticated than AI-first approach
- **Rationale**: Reliability and cost considerations

### Idempotency Scope
- **Chosen**: Per-tenant scoping
- **Trade-off**: Same key can be reused across tenants
- **Rationale**: Prevents cross-tenant conflicts

## Future Enhancements

- [ ] Cursor-based pagination for GraphQL
- [ ] DataLoaders for N+1 query prevention
- [ ] Webhook support for match confirmations
- [ ] Advanced reconciliation algorithms (Hungarian algorithm)
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Authentication/Authorization
- [ ] Multi-currency support enhancements

## License

MIT

