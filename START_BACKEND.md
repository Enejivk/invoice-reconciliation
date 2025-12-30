# How to Start the Backend

## Quick Start (First Time Setup)

### Step 1: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -e ".[dev]"
```

### Step 3: Create .env File
```bash
cp .env.example .env
```

The .env file will have:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/invoice_reconciliation
AI_ENABLED=false
```

### Step 4: Start PostgreSQL Database
```bash
docker-compose up -d
```

Wait a few seconds for PostgreSQL to start.

### Step 5: Run Database Migrations
```bash
alembic upgrade head
```

### Step 6: Start the Backend Server
```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Access the Backend

Once running, you can access:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/api/graphql
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## Starting After First Setup

If you've already set up once, just do:

```bash
# Activate virtual environment
source venv/bin/activate

# Start database (if not running)
docker-compose up -d

# Start server
uvicorn main:app --reload
```

## Troubleshooting

**Database connection error?**
- Make sure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in .env file

**Port 8000 already in use?**
- Use a different port: `uvicorn main:app --reload --port 8001`

**Migration errors?**
- Reset database: `docker-compose down -v && docker-compose up -d`
- Re-run migrations: `alembic upgrade head`

**Module not found errors?**
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -e ".[dev]"`

