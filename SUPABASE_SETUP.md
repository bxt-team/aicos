# Supabase Development Setup

## 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign in or create an account
3. Click "New Project"
4. Fill in:
   - Project name: `7cycles-ai-dev`
   - Database password: (save this securely)
   - Region: Choose closest to you
   - Plan: Free tier is fine for development

## 2. Get Your Credentials

Once project is created, go to Settings > API to find:
- Project URL: `https://[PROJECT_REF].supabase.co`
- Anon/Public key: `eyJ...` (safe for client-side)
- Service Role key: `eyJ...` (server-side only, full access)

## 3. Set Up Environment Variables

Create `.env.development` file:
```bash
# Supabase Development
SUPABASE_URL=https://[YOUR_PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
SUPABASE_SERVICE_KEY=[YOUR_SERVICE_KEY]
SUPABASE_DB_PASSWORD=[YOUR_DB_PASSWORD]

# Optional: Direct database connection
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

## 4. Install Supabase MCP

The Supabase MCP allows Claude to directly interact with your database.

### Installation Steps:

1. Install the MCP globally:
```bash
npm install -g @modelcontextprotocol/server-supabase
```

2. Add to your Claude settings (`.claude/settings.json`):
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--url",
        "https://[YOUR_PROJECT_REF].supabase.co",
        "--service-role-key",
        "[YOUR_SERVICE_KEY]"
      ]
    }
  }
}
```

3. Restart Claude Code for the MCP to take effect

## 5. Install Python Dependencies

Add to `backend/requirements.txt`:
```
supabase==2.0.3
```

Then install:
```bash
cd backend
pip install -r requirements.txt
```

## 6. Test Connection

Create a test script `backend/test_supabase.py`:
```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('.env.development')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)

# Test connection
try:
    response = supabase.table('system_generic_storage').select("*").limit(1).execute()
    print("✅ Supabase connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 7. Database Setup Options

### Option A: Use Supabase Dashboard
- Go to Table Editor in Supabase Dashboard
- Create tables manually using the UI

### Option B: Use SQL Editor
- Go to SQL Editor in Supabase Dashboard
- Run the migration SQL from SUPABASE_MIGRATION_PLAN.md

### Option C: Use Migrations (Recommended)
```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Initialize local project
supabase init

# Link to remote project
supabase link --project-ref [YOUR_PROJECT_REF]

# Create migration
supabase migration new initial_schema

# Apply migrations
supabase db push
```

## Security Notes

1. **Never commit `.env.development` to git**
   - Add to `.gitignore`
   
2. **Service Role Key Security**
   - Only use on backend
   - Never expose to frontend
   
3. **Row Level Security (RLS)**
   - Enable RLS on all tables
   - Define policies based on your needs

## Next Steps

1. Create the database schema
2. Test the connection
3. Implement storage adapters
4. Begin migration