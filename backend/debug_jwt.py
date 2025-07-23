#!/usr/bin/env python3
"""
JWT Debug Script
Analyzes JWT tokens to understand validation failures
"""
import os
import json
import base64
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def decode_jwt_parts(token):
    """Decode JWT header and payload without verification"""
    parts = token.split('.')
    
    if len(parts) != 3:
        print(f"Invalid JWT format. Expected 3 parts, got {len(parts)}")
        return None, None
    
    # Add padding if needed
    def pad_base64(data):
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return data
    
    try:
        # Decode header
        header = json.loads(base64.urlsafe_b64decode(pad_base64(parts[0])))
        print("\n=== JWT Header ===")
        print(json.dumps(header, indent=2))
        
        # Decode payload
        payload = json.loads(base64.urlsafe_b64decode(pad_base64(parts[1])))
        print("\n=== JWT Payload ===")
        print(json.dumps(payload, indent=2))
        
        return header, payload
    except Exception as e:
        print(f"Error decoding JWT parts: {e}")
        return None, None

def verify_with_secret(token, secret):
    """Try to verify JWT with a given secret"""
    try:
        # Try different algorithms
        algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        
        for algo in algorithms:
            try:
                decoded = jwt.decode(token, secret, algorithms=[algo])
                print(f"\n✓ Successfully verified with algorithm: {algo}")
                return decoded
            except jwt.InvalidAlgorithmError:
                continue
            except jwt.InvalidSignatureError:
                continue
            except Exception as e:
                continue
        
        print(f"\n✗ Could not verify with any algorithm")
        return None
    except Exception as e:
        print(f"\n✗ Verification error: {e}")
        return None

def analyze_supabase_relationship(anon_key, jwt_secret):
    """Analyze the relationship between Supabase anon key and JWT secret"""
    print("\n=== Supabase Key Analysis ===")
    
    # Check if anon key is itself a JWT
    parts = anon_key.split('.')
    if len(parts) == 3:
        print("Anon key appears to be a JWT token")
        header, payload = decode_jwt_parts(anon_key)
        
        if header and payload:
            # Check if it's signed with the JWT secret
            print("\nTrying to verify anon key with JWT secret...")
            verify_with_secret(anon_key, jwt_secret)
    else:
        print("Anon key is not a JWT token")
    
    # Check if JWT secret might be derived from anon key
    print("\n=== Secret Relationship ===")
    print(f"JWT Secret length: {len(jwt_secret)}")
    print(f"Anon key length: {len(anon_key)}")
    
    # Check if they share common parts
    if jwt_secret in anon_key:
        print("JWT secret is contained within anon key")
    elif anon_key in jwt_secret:
        print("Anon key is contained within JWT secret")
    else:
        print("No direct substring relationship found")

def main():
    # Get environment variables
    jwt_secret = os.getenv('JWT_SECRET', '')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY', '')
    
    print("=== JWT Debug Tool ===")
    print(f"\nJWT_SECRET present: {'Yes' if jwt_secret else 'No'}")
    print(f"SUPABASE_ANON_KEY present: {'Yes' if supabase_anon_key else 'No'}")
    
    # Test token (you can replace this with an actual token)
    test_token = input("\nEnter a JWT token to analyze (or press Enter to skip): ").strip()
    
    if test_token:
        print("\n" + "="*50)
        print("ANALYZING PROVIDED TOKEN")
        print("="*50)
        
        # Decode without verification
        header, payload = decode_jwt_parts(test_token)
        
        if header:
            # Try to verify with different secrets
            print("\n=== Verification Attempts ===")
            
            if jwt_secret:
                print("\nTrying with JWT_SECRET...")
                verify_with_secret(test_token, jwt_secret)
            
            if supabase_anon_key:
                print("\nTrying with SUPABASE_ANON_KEY...")
                verify_with_secret(test_token, supabase_anon_key)
            
            # If it's an RS algorithm, we might need a public key
            if header.get('alg', '').startswith('RS'):
                print("\nNote: Token uses RSA algorithm. Would need public key for verification.")
    
    if supabase_anon_key and jwt_secret:
        print("\n" + "="*50)
        print("ANALYZING SUPABASE CONFIGURATION")
        print("="*50)
        analyze_supabase_relationship(supabase_anon_key, jwt_secret)
    
    # Provide guidance
    print("\n" + "="*50)
    print("RECOMMENDATIONS")
    print("="*50)
    print("\n1. For Supabase JWT verification:")
    print("   - Use the SUPABASE_JWT_SECRET (not anon key) for verification")
    print("   - This is different from SUPABASE_ANON_KEY")
    print("   - Find it in Supabase Dashboard > Settings > API")
    print("\n2. Common issues:")
    print("   - Using anon key instead of JWT secret")
    print("   - Wrong algorithm (Supabase uses HS256 by default)")
    print("   - Expired tokens")
    print("\n3. Required environment variables:")
    print("   - SUPABASE_JWT_SECRET (for verification)")
    print("   - SUPABASE_ANON_KEY (for client initialization)")
    print("   - SUPABASE_URL")

if __name__ == "__main__":
    main()