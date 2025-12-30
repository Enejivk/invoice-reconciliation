#!/bin/bash
# Quick script to start the backend

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "Starting Invoice Reconciliation API..."
echo "API Docs: http://localhost:8000/docs"
echo "GraphQL: http://localhost:8000/api/graphql"
echo "Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --reload

