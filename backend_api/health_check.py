#!/usr/bin/env python3
"""
Daily Journal API Health Check Script
Monitors API health and provides status information
"""
import requests
import sys
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10
CHECK_INTERVAL = 30  # seconds

def check_health():
    """Check basic health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return True, data.get('message', 'Healthy')
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, str(e)

def check_detailed_health():
    """Check detailed health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            services = data.get('services', {})
            return True, status, services
        else:
            return False, f"HTTP {response.status_code}", {}
    except requests.exceptions.RequestException as e:
        return False, str(e), {}

def check_api_info():
    """Get API information"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/info", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, {}
    except requests.exceptions.RequestException:
        return False, {}

def format_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def print_status(healthy, message, detailed_info=None):
    """Print health status with formatting"""
    timestamp = format_timestamp()
    status_icon = "✅" if healthy else "❌"
    status_text = "HEALTHY" if healthy else "UNHEALTHY"
    
    print(f"[{timestamp}] {status_icon} API Status: {status_text}")
    print(f"Message: {message}")
    
    if detailed_info:
        print("Services:")
        for service, status in detailed_info.items():
            service_icon = "✅" if status == "healthy" else "❌"
            print(f"  {service_icon} {service}: {status}")
    
    print("-" * 50)

def main():
    """Main health check function"""
    print("Daily Journal API Health Monitor")
    print("=" * 50)
    
    # Check if monitoring mode or single check
    monitoring = len(sys.argv) > 1 and sys.argv[1] == "--monitor"
    
    while True:
        # Basic health check
        healthy, message = check_health()
        
        # Detailed health check
        detailed_healthy, detailed_status, services = check_detailed_health()
        
        # API info
        info_success, api_info = check_api_info()
        
        # Print status
        print_status(healthy and detailed_healthy, message, services)
        
        # Show API info on first run
        if info_success and api_info:
            print(f"API Version: {api_info.get('version', 'unknown')}")
            print(f"Features: {len(api_info.get('features', []))} available")
            print("-" * 50)
        
        # Exit if not monitoring
        if not monitoring:
            sys.exit(0 if healthy and detailed_healthy else 1)
        
        # Wait for next check
        try:
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\nHealth monitoring stopped.")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Daily Journal API Health Check")
        print("")
        print("Usage:")
        print("  python health_check.py           # Single health check")
        print("  python health_check.py --monitor # Continuous monitoring")
        print("  python health_check.py --help    # Show this help")
        print("")
        print("Exit codes:")
        print("  0 - API is healthy")
        print("  1 - API is unhealthy")
    else:
        main()
