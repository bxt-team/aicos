# MCP (Model Context Protocol) Usage

## Overview
This project uses MCP to integrate with Supabase. The configuration is stored in `.mcp.json`.

## Setup

1. **Environment Variables**
   - Ensure your `.env` file contains the `SUPABASE_ACCESS_TOKEN`:
     ```
     SUPABASE_ACCESS_TOKEN=your_supabase_access_token_here
     ```

2. **Running MCP**
   - The MCP server expects the `SUPABASE_ACCESS_TOKEN` to be available as an environment variable
   - When using Claude Desktop or other MCP clients, make sure to:
     - Either set the environment variable globally before launching the client
     - Or use a script that loads the `.env` file before starting the MCP client

## Configuration Structure

The `.mcp.json` file configures the Supabase MCP server:
- **command**: Uses `npx` to run the latest Supabase MCP server
- **args**: Includes the project reference ID
- **env**: Removed from the config - the token should come from environment variables

## Security Note
Never commit access tokens to version control. Always use environment variables for sensitive data.