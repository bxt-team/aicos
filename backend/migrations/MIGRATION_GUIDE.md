# Multi-Tenant Database Migration Guide

## Overview

This guide explains how to apply the multi-tenant database migrations to your Supabase project.

## Migration Files

The following SQL files need to be executed in order:

1. **001_create_organizations_table.sql** - Creates organizations table with subscription tiers
2. **002_create_projects_table.sql** - Creates projects within organizations  
3. **003_create_users_table.sql** - Creates users table with auth fields
4. **004_create_memberships_tables.sql** - Creates organization and project membership tables
5. **005_create_api_keys_table.sql** - Creates API key management table
6. **006_create_audit_logs_table.sql** - Creates audit trail table
7. **007_update_rls_policies.sql** - Updates Row Level Security policies
8. **008_create_agent_tables_template.sql** - Template for updating agent tables
9. **009_add_password_storage.sql** - Adds password storage to users table

## Method 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Navigate to the SQL Editor (Database → SQL Editor)
4. For each migration file:
   - Click "New Query"
   - Copy the entire contents of the migration file
   - Paste into the SQL editor
   - Click "Run" 
   - Verify success before proceeding to next file

## Method 2: Using Supabase CLI

If you have the Supabase CLI installed:

```bash
# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref jozhoacicfupvjduswio

# Apply migrations
for file in backend/migrations/*.sql; do
  echo "Applying $file..."
  supabase db push --file "$file"
done
```

## Method 3: Combined Migration File

For convenience, you can also run all migrations at once using the combined file:
`all_migrations_combined.sql`

**WARNING**: This approach makes it harder to debug if something goes wrong. Use only if you're confident.

## Post-Migration Steps

After applying all migrations:

1. **Verify Tables Created**:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN (
     'organizations', 'projects', 'users', 
     'organization_members', 'project_members',
     'api_keys', 'audit_logs', 'migrations'
   );
   ```

2. **Check RLS Policies**:
   ```sql
   SELECT schemaname, tablename, policyname 
   FROM pg_policies 
   WHERE schemaname = 'public';
   ```

3. **Test Functions**:
   ```sql
   -- Test user registration function
   SELECT register_user(
     'test@example.com',
     'Test User',
     'hashed_password_here',
     'email'
   );
   ```

## Troubleshooting

### Error: "permission denied for schema public"
- Make sure you're using the service role key, not the anon key
- Or run the migrations through the Supabase Dashboard

### Error: "relation already exists"
- The table was already created
- You can safely skip that migration

### Error: "violates foreign key constraint"
- Make sure you're running migrations in the correct order
- Check that referenced tables exist

## Rollback

If you need to rollback:

```sql
-- Drop tables in reverse order to avoid foreign key issues
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS project_members CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS migrations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS verify_user_password CASCADE;
DROP FUNCTION IF EXISTS register_user CASCADE;
DROP FUNCTION IF EXISTS user_has_permission CASCADE;
DROP FUNCTION IF EXISTS log_audit_event CASCADE;
DROP FUNCTION IF EXISTS add_multi_tenant_columns CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- Drop views
DROP VIEW IF EXISTS users_safe CASCADE;
```

## Next Steps

After successful migration:

1. Test the authentication endpoints
2. Create a test organization and user
3. Verify Row Level Security is working
4. Begin migrating your application code