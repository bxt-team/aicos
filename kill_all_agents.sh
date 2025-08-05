#!/bin/bash

echo "Stopping all aicos agents and services..."

# Kill backend processes (FastAPI/Uvicorn)
echo "Stopping backend services..."
pkill -f "uvicorn app.main:app"
pkill -f "cd backend && uvicorn"

# Kill frontend processes (React)
echo "Stopping frontend services..."
pkill -f "react-scripts start"
pkill -f "aicos/frontend/node_modules"

# Kill any Python processes related to the project
echo "Stopping any Python agent processes..."
pkill -f "aicos.*python"
pkill -f "aicos/backend"

# Kill any remaining Node processes specific to this project
echo "Stopping any remaining Node processes..."
pkill -f "aicos/frontend"

# Also kill processes by port if they're still running
echo "Checking and killing processes on common ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Port 8000 already free"
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Port 3000 already free"

echo "All agents and services stopped!"
echo ""
echo "To verify, you can run:"
echo "  ps aux | grep -E '(aicos|uvicorn|react-scripts)' | grep -v grep"