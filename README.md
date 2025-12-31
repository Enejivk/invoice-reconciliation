# Invoice Reconciliation API

multi-tenant API built with Python 3.13, FastAPI, and Strawberry GraphQL. It matches invoices to bank transactions using deterministic scoring and provides AI explanations.

## Get Started

> 🚨 **CRITICAL WARNING: CHECK DOCKER STATUS**
>
> You **MUST** ensure that Docker is up and running on your machine **before** attempting to start the backend.
>
> **The Consequence:** We run the PostgreSQL database inside a Docker container. If Docker is not running, the application **WILL FAIL** with a Database Connection Error.
>
> **If you see a Database Error:** It is almost certainly because Docker is not running. Please start Docker and try again.

### System Requirements

- **Python 3.13+**
- **Docker & Docker Compose** (for the database)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/Enejivk/invoice-reconciliation.git
   cd invoice-reconciliation
   ```

2. **Run the automated setup**
   This script creates the venv, installs deps, sets up `.env`, and starts PostgreSQL.

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the server**
   The easiest way is to use the start script:

   ```bash
   chmod +x start_backend.sh
   ./start_backend.sh
   ```

   _Or manually:_

   ```bash
   # macOS/Linux:
   source venv/bin/activate

   # Windows:
   venv\Scripts\activate

   uvicorn main:app --reload
   ```

### Manual Setup (If you prefer doing it yourself)

If you don't want to use the script, here is the blow-by-blow:

```bash
# 1. Environment
python -m venv venv

# Activate venv
# macOS/Linux: source venv/bin/activate
# Windows: venv\Scripts\activate

# 2. Dependencies
pip install -e ".[dev]"

# 3. Configuration
# macOS/Linux: cp .env.example .env
# Windows: copy .env.example .env

# 4. Infrastructure
docker-compose up -d

# 5. Database Schema
alembic upgrade head
```

**Where to go once it's running:**

- **In-browser Docs**: `http://localhost:8000/docs`
- **GraphQL Explorer**: `http://localhost:8000/api/graphql`
- **Health Check**: `http://localhost:8000/health`

---

## 🛠️ How to Test & Explore

### 1. Manual Testing (The easy way)

If you want to poke around without writing code, use the built-in explorers:

- **Swagger UI**: Go to `http://localhost:8000/docs`. You can try out every REST endpoint (Tenants, Invoices, Imports) directly from your browser.
- **GraphQL Playground**: Go to `http://localhost:8000/api/graphql`. It has full "Introspection" enabled so you can see the whole schema and run queries/mutations manually.
- **Postman**: I've included a `postman_collection.json` file. To use it: Open Postman, click **Import**, and drag this file in. It’s pre-configured with the `base_url`, so you can just click and test!

### 2. Frontend Testing (The visual way)

I've included a React frontend so you can see the reconciliation process in action.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. You can create a tenant, upload "bank data," and watch the AI explain why it matched an invoice. It's the best way to see the "Senior-level" logic in a real-world UI.

## Design Decisions

### Why PostgreSQL instead of SQLite?

---

I went with **PostgreSQL** because it's built for multi-tenant apps. It gives us Row-Level Security (RLS) and better concurrency than SQLite. Even though SQLite is easier to set up for a demo, Postgres is what you'd actually use in production to keep customers' data safely separated.

### How do I make sure Tenant A never sees Tenant B's data?

---

I didn't want to rely on developers remembering to add a `WHERE tenant_id = X` every time. Instead, I built a `BaseRepository` that handles this automatically behind the scenes. Every database query is forced to filter by the tenant ID, so isolation isn't an afterthought—it's built into the foundation.

### Why not let AI handle the matching?

---

Matching money is too important for "hallucinations." I used a **deterministic scoring engine** (Heuristics) instead. It gives you a score from 0 to 100 based on:

- **Exact Amounts** (40 points)
- **Date Proximity** (30 points)
- **Text Similarity** like vendor names (20 points)
- **Currency** matches (10 points)

We use AI (Claude 3.5 Sonnet) specifically to **explain** the match to the user in plain English, which is where LLMs actually shine.

### What happens if the AI service is down?

---

Reliability is key. If the Anthropic API is slow or the key is missing, the system doesn't crash. It falls back to a "deterministic explanation" based on those match scores I mentioned above. The user always gets an answer.

### How do I stop double-imports?

---

If a user clicks "Import" twice by accident, the system checks the `X-Idempotency-Key` header. I hash the whole payload (SHA-256) so if the data is the same, we just return the previous result. If someone tries to re-use a key with different data, we catch it and return a `409 Conflict`.

---

## 📂 How is the code organized?

---

I've followed a clean, layered architecture to keep the "Brain" separate from the "API":

```text
invoice-reconciliation/
├── alembic/          # Database migration logic & history
├── api/              # Entry points (Protocol layer)
│   ├── rest/         # FastAPI routers & endpoints
│   ├── graphql/      # Strawberry GQL schema & mutations
│   └── schemas/      # Pydantic models for validation
├── core/             # Shared config, DB sessions, & exceptions
├── models/           # SQLAlchemy 2.0 database models
├── repositories/     # Data Access Layer (Tenant isolation happens here)
├── services/         # Business Logic (Reconciliation & AI logic)
├── tests/            # Full test suite (Pytest)
├── frontend/         # React dashboard for visual testing
└── main.py           # Application entry point
```

- **`api/`**: This is the "Front Desk". Both REST and GraphQL live here and talk to the same services.
- **`services/`**: The "Brain". This is where the scoring engine and AI orchestration live. It doesn't care if a request came from REST or GraphQl.
- **`repositories/`**: The "Gatekeeper". It enforces tenant isolation on every query so you don't leak data.
- **`models/`**: The "Blueprint". Just the database structure.

---

## 🧪 How do I run the tests?

I set up the tests to use an in-memory SQLite database so they run instantly without you needing to mess with Postgres.

```bash
pytest
```

I've covered the critical paths: Creating invoices, bulk importing transactions (with idempotency tests), making sure the scoring ranking is correct, and verifying that the AI fallback works.

---

## Troubleshooting

- **Database**: If it won't connect, make sure Docker is running (`docker-compose ps`).
- **Migrations**: If you need to start fresh, just run `docker-compose down -v` to wipe the volumes and restart.
- **Python**: Make sure you're on **3.13+**.
