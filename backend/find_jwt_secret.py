#!/usr/bin/env python3
"""
Script to help find the correct JWT secret for your Supabase project
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt
import json

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get the keys
supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
current_jwt_secret = os.getenv('JWT_SECRET_KEY')

print("=== Supabase JWT Secret Finder ===\n")

print("Your Supabase project ref: jozhoacicfupvjduswio")
print("Dashboard URL: https://supabase.com/dashboard/project/jozhoacicfupvjduswio/settings/api")
print("\n" + "="*50 + "\n")

print("IMPORTANT: To find your JWT secret:")
print("1. Go to the URL above")
print("2. Scroll down to 'JWT Settings' section")
print("3. Look for 'JWT Secret' (NOT the anon key or service key)")
print("4. Copy the entire secret value")
print("5. The secret should be a long string (usually 40+ characters)")
print("\n" + "="*50 + "\n")

if supabase_anon_key:
    # Decode the anon key to show what we're trying to verify
    try:
        header = jwt.get_unverified_header(supabase_anon_key)
        payload = jwt.decode(supabase_anon_key, key=None, options={"verify_signature": False})
        
        print("Your SUPABASE_ANON_KEY token info:")
        print(f"  Algorithm: {header['alg']}")
        print(f"  Issuer: {payload.get('iss')}")
        print(f"  Reference: {payload.get('ref')}")
        print(f"  Role: {payload.get('role')}")
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error decoding anon key: {e}")

print("Current JWT_SECRET_KEY in .env:")
if current_jwt_secret:
    print(f"  Length: {len(current_jwt_secret)} characters")
    print(f"  First 10 chars: {current_jwt_secret[:10]}...")
    print(f"  Last 10 chars: ...{current_jwt_secret[-10:]}")
else:
    print("  NOT SET")

print("\n" + "="*50 + "\n")

# Test verification with different approaches
if current_jwt_secret and supabase_anon_key:
    print("Testing JWT verification...")
    
    # Test 1: Direct verification
    try:
        jwt.decode(
            supabase_anon_key,
            current_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        print("✅ SUCCESS: Current JWT_SECRET_KEY is correct!")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("\nThis means the JWT_SECRET_KEY in your .env file doesn't match")
        print("the secret used to sign your Supabase tokens.")
        
print("\n" + "="*50 + "\n")
print("Next steps:")
print("1. Go to your Supabase dashboard (URL above)")
print("2. Find the JWT Secret in the JWT Settings section")
print("3. Update JWT_SECRET_KEY in your .env file with the correct value")
print("4. Restart your backend server")
print("\nNote: The JWT secret is different from your anon key and service key!")