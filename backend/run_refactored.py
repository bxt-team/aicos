#!/usr/bin/env python3
"""
Script to run the refactored backend application
"""
import subprocess
import sys
import os

def main():
    """Run the refactored application"""
    print("Starting refactored 7 Cycles Backend...")
    print("-" * 50)
    
    # Check if running in the backend directory
    if not os.path.exists("app.py"):
        print("Error: Please run this script from the backend directory")
        sys.exit(1)
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work properly.")
        print("-" * 50)
    
    try:
        # Run the application with uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()