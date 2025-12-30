# Invoice Reconciliation Frontend

A clean, modern React frontend for the Invoice Reconciliation API.

## Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the frontend**
   ```bash
   npm run dev
   ```

3. **Make sure the backend is running**
   ```bash
   # In the root directory
   uvicorn main:app --reload
   ```

4. **Open your browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Features

- ✅ Create and manage tenants
- ✅ Create invoices with full details
- ✅ Import bank transactions
- ✅ Run automatic reconciliation
- ✅ View match candidates with scores
- ✅ Get AI explanations for matches
- ✅ Confirm matches
- ✅ Beautiful, responsive UI

## Usage

1. **Create a Tenant**: Start by creating a tenant (organization)
2. **Create Invoices**: Add invoices that need to be matched
3. **Import Transactions**: Import bank transactions
4. **Run Reconciliation**: Click "Run Reconciliation" to automatically match invoices to transactions
5. **Review Matches**: See match candidates with scores
6. **Get Explanations**: Click "Get Explanation" to see why a match was suggested
7. **Confirm Matches**: Confirm matches to finalize them

## Tech Stack

- React 18
- Vite (fast build tool)
- Axios (HTTP client)
- Modern CSS (no framework needed)

