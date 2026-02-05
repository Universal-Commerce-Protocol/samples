#!/bin/bash

# Ensure we are in the exact demo directory
cd "$(dirname "$0")"

# Activate the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Trap cleanup to gracefully stop the background server
trap 'kill $SUPPLIER_PID 2>/dev/null; echo -e "\nServer stopped."' EXIT INT TERM

echo -e "\n🚀 Starting Local Supplier Server (Port 8000)..."
python supplier_server.py &
SUPPLIER_PID=$!

# Give the server a moment to bind and start
sleep 2

echo -e "\n🤖 Starting Interactive Buyer Agent..."
python buyer_agent.py
