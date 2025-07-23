#!/usr/bin/env python3
"""
Quick fix to remove created_by fields from organization creation
Run this to temporarily fix the issue while you apply the database migration
"""

import os
from pathlib import Path

# Read the organizations.py file
file_path = Path(__file__).parent / "app/api/routers/organizations.py"
with open(file_path, 'r') as f:
    content = f.read()

# Remove created_by fields
original_content = content
content = content.replace(
    '''            "created_by": str(current_user["user_id"]),
            "created_at": datetime.utcnow().isoformat(),''',
    '''            "created_at": datetime.utcnow().isoformat(),'''
)

content = content.replace(
    '''            "created_by": str(current_user["user_id"]),
            "created_at": datetime.utcnow().isoformat(),''',
    '''            "created_at": datetime.utcnow().isoformat(),'''
)

if content != original_content:
    # Backup original file
    backup_path = file_path.with_suffix('.py.backup')
    with open(backup_path, 'w') as f:
        f.write(original_content)
    
    # Write fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")
    print(f"📁 Backup saved to {backup_path}")
    print("\nTo restore original:")
    print(f"  mv {backup_path} {file_path}")
else:
    print("❌ No changes needed - created_by fields not found or already removed")