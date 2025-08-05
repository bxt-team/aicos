# Supabase MCP Setup Guide

## Step 1: Create Supabase Project

1. **Go to** [https://supabase.com](https://supabase.com) and sign in
2. **Click** "New Project"
3. **Configure your project:**
   - Organization: Select or create one
   - Project name: `aicos-dev`
   - Database Password: Generate a strong password (save this!)
   - Region: Choose closest to you (e.g., Frankfurt for EU)
   - Pricing Plan: Free tier

4. **Wait** for project to be created (takes ~2 minutes)

## Step 2: Get Your Credentials

Once created, navigate to:

1. **Project Settings** (gear icon in sidebar)
2. **API** section
3. **Copy these values:**
   - Project URL: `https://xxxxxxxxxxxxx.supabase.co`
   - anon public key: `eyJ...` (long JWT token)
   - service_role key: `eyJ...` (different JWT token)

## Step 3: Configure MCP in Claude

1. **Create** `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase"
      ],
      "env": {
        "SUPABASE_URL": "YOUR_PROJECT_URL",
        "SUPABASE_SERVICE_ROLE_KEY": "YOUR_SERVICE_KEY"
      }
    }
  }
}
```

2. **Replace** `YOUR_PROJECT_URL` and `YOUR_SERVICE_KEY` with actual values

## Step 4: Create .env.development

```bash
# Copy and fill in your credentials
cp .env.development.example .env.development
```

Edit `.env.development`:
```bash
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...your-anon-key...
SUPABASE_SERVICE_KEY=eyJ...your-service-key...
SUPABASE_DB_PASSWORD=your-database-password
```

## Step 5: Test MCP Connection

After restarting Claude Code, you should see Supabase MCP tools available:
- mcp__supabase__list_tables
- mcp__supabase__execute_sql
- mcp__supabase__apply_migration
- etc.

## Step 6: Quick Test

Once configured, I can run:
```sql
SELECT version();
```

To verify the connection is working.

---

**Ready?** Once you have:
1. ✅ Created the Supabase project
2. ✅ Copied your credentials
3. ✅ Created `.mcp.json` with your credentials
4. ✅ Created `.env.development` with your credentials
5. ✅ Restarted Claude Code

Let me know and I'll proceed with creating the database schema!