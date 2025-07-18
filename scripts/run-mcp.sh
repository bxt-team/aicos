#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -E '^SUPABASE_ACCESS_TOKEN=' .env | xargs)
fi

# Check if SUPABASE_ACCESS_TOKEN is set
if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    echo "Error: SUPABASE_ACCESS_TOKEN not found in .env file"
    exit 1
fi

# The MCP server will now use the SUPABASE_ACCESS_TOKEN from the environment
echo "Starting MCP server with Supabase access token from .env file..."