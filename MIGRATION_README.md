# aicos Supabase Migration Guide

## Overview

This guide explains how to migrate your aicos application from JSON file-based storage to Supabase database storage. The migration is designed to be gradual and safe, with no downtime.

## Current Status

✅ **Storage abstraction layer**: Implemented  
✅ **JSON adapter**: Working (backward compatible)  
✅ **Supabase adapter**: Implemented and tested  
✅ **Dual-write mode**: Available for safe migration  
✅ **Database schema**: Created in Supabase  
✅ **Migration scripts**: Ready to use  

## Quick Start

### 1. Set Up Your Environment

Create a `.env.development` file from the example:
```bash
cp .env.development.example .env.development
```

Fill in your Supabase credentials:
```bash
SUPABASE_URL=https://jozhoacicfupvjduswio.supabase.co  # Your actual URL
SUPABASE_SERVICE_KEY=your-service-key-here
STORAGE_ADAPTER=json  # Start with JSON
```

### 2. Test Your Setup

Run the storage adapter tests:
```bash
cd backend
python test_storage_adapters.py
```

This will verify:
- JSON adapter works (current behavior)
- Supabase connection is configured
- Both adapters can save/load/update/delete data

### 3. Run a Dry Migration

See what data would be migrated:
```bash
cd backend
python -m scripts.migrate_to_supabase
# Select option 1 (Dry run)
```

## Migration Strategy

### Phase 1: Dual-Write Mode (Recommended)

1. **Enable dual-write** in your `.env`:
   ```bash
   STORAGE_ADAPTER=dual
   DUAL_WRITE_READ_FROM=json
   ```

2. **Restart your application**. Now:
   - All writes go to BOTH JSON and Supabase
   - All reads still come from JSON (safe!)
   - No behavior change for users

3. **Monitor for a few days** to ensure:
   - No errors in logs
   - Data appears in Supabase dashboard
   - Application works normally

### Phase 2: Switch Read to Supabase

1. **Change the read source**:
   ```bash
   DUAL_WRITE_READ_FROM=supabase
   ```

2. **Test thoroughly**:
   - All features should work identically
   - Performance should be similar or better

3. **Monitor for issues**

### Phase 3: Full Migration

1. **Switch to Supabase only**:
   ```bash
   STORAGE_ADAPTER=supabase
   # Remove DUAL_WRITE_READ_FROM
   ```

2. **Archive JSON files** (keep as backup)

## Storage Adapters

### JSON Adapter (Current)
- Stores data in `static/*.json` files
- No setup required
- Good for development/small scale

### Supabase Adapter
- Stores data in PostgreSQL database
- Requires Supabase account
- Better for production/scale

### Dual-Write Adapter
- Writes to both JSON and Supabase
- Configurable read source
- Perfect for gradual migration

## Collections Mapping

| Collection Name | JSON File | Supabase Table |
|----------------|-----------|----------------|
| affirmations | affirmations_storage.json | agent_affirmation_items |
| visual_posts | visual_posts_storage.json | agent_visual_posts |
| instagram_posts | instagram_posts_history.json | agent_instagram_posts |
| instagram_analyses | instagram_analysis_storage.json | agent_instagram_analyses |
| content_items | workflows_storage.json | agent_content_items |
| workflows | workflows_storage.json | system_workflows |

## Running the Migration

### Option 1: Migrate Everything
```bash
cd backend
python -m scripts.migrate_to_supabase
# Select option 2 (Migrate all collections)
```

### Option 2: Migrate Specific Collection
```bash
cd backend
python -m scripts.migrate_to_supabase
# Select option 3 (Migrate specific collection)
```

### Option 3: Command Line
```bash
cd backend
# Dry run first
python -m scripts.migrate_to_supabase --dry-run

# Migrate specific collections
python -m scripts.migrate_to_supabase affirmations visual_posts

# Migrate everything
python -m scripts.migrate_to_supabase
```

## Updating Your Code

Most agents won't need changes! The storage layer handles everything.

### If You Have Custom Storage Code

Replace direct file operations:

**Before:**
```python
# Direct file access
with open('static/affirmations.json', 'r') as f:
    data = json.load(f)
```

**After:**
```python
# Using storage adapter
from app.core.storage import get_storage

storage = get_storage()
affirmations = await storage.list('affirmations')
```

### Example: Updated Agent
```python
from app.core.storage import get_storage

class MyAgent:
    def __init__(self):
        self.storage = get_storage()
    
    async def save_data(self, data):
        # Works with any storage backend!
        return await self.storage.save('my_collection', data)
```

## Monitoring

### Check Supabase Dashboard
1. Go to your Supabase project
2. Navigate to Table Editor
3. Verify data is appearing in tables

### Check Application Logs
Look for storage-related messages:
```
✅ Saved to agent_affirmation_items
⚠️ Failed to save to secondary adapter (if in dual-write)
```

### Run Health Checks
```bash
# Check all agent health endpoints
curl http://localhost:8000/api/qa-health
curl http://localhost:8000/api/instagram/health
```

## Troubleshooting

### "Supabase connection failed"
- Check your SUPABASE_URL and SUPABASE_SERVICE_KEY
- Ensure your Supabase project is active
- Try the connection test script

### "Table not found"
- Ensure all tables are created (check Supabase dashboard)
- Table names are case-sensitive

### "Data not appearing in Supabase"
- Check you're in dual-write or supabase mode
- Look for errors in console logs
- Verify with test script

### Performance Issues
- Add indexes to frequently queried fields
- Use Supabase query optimization
- Consider caching for read-heavy operations

## Rollback Plan

If issues occur at any phase:

1. **From Dual-Write**: Just set `STORAGE_ADAPTER=json`
2. **From Supabase**: 
   - Set `STORAGE_ADAPTER=json`
   - Your JSON files are still there!
3. **Data Recovery**: JSON backups are maintained

## Benefits After Migration

- ⚡ **Better Performance**: Indexed queries, connection pooling
- 🔄 **Real-time Updates**: Supabase real-time subscriptions
- 🛡️ **Security**: Row-level security, encrypted connections
- 📊 **Analytics**: SQL queries for insights
- 🔧 **Easier Maintenance**: Automated backups, monitoring
- 🚀 **Scalability**: Handle more users and data

## Questions?

- Check the [Supabase docs](https://supabase.com/docs)
- Review `SUPABASE_MIGRATION_PLAN.md` for technical details
- Test with the provided scripts before production migration

Happy migrating! 🚀