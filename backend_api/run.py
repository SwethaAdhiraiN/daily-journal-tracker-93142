#!/usr/bin/env python3
"""
Development startup script for Daily Journal API
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main entry point for development server"""
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Development settings
    reload = environment == "development"
    
    print(f"Starting Daily Journal API on {host}:{port}")
    print(f"Environment: {environment}")
    print(f"Reload: {reload}")
    print(f"Documentation: http://{host}:{port}/docs")
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
            reload_dirs=["src"] if reload else None
        )
    except KeyboardInterrupt:
        print("\nShutting down Daily Journal API...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
