#!/usr/bin/env python3
"""
Test script for LED controller threading implementation.
This script tests the API endpoints without needing a browser.
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_status():
    """Test the status endpoint."""
    print("\n--- Testing Status Endpoint ---")
    response = requests.get(f"{BASE_URL}/api/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_list_effects():
    """Test listing available effects."""
    print("\n--- Testing List Effects Endpoint ---")
    response = requests.get(f"{BASE_URL}/api/effects")
    print(f"Status: {response.status_code}")
    print(f"Available effects: {response.json()['effects']}")
    return response.json()

def test_effect(effect_name, duration=5):
    """Test starting an effect."""
    print(f"\n--- Testing Effect: {effect_name} ---")
    response = requests.get(f"{BASE_URL}/control_led/{effect_name}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print(f"Effect '{effect_name}' started, running for {duration} seconds...")
        time.sleep(duration)
        
        # Check status while running
        status = test_status()
        print(f"Current effect running: {status.get('current_effect')}")
    
    return response.json()

def test_stop():
    """Test stopping all effects."""
    print("\n--- Testing Stop ---")
    response = requests.get(f"{BASE_URL}/control_led/stop")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def main():
    """Run all tests."""
    print("=" * 60)
    print("LED Controller Threading Test Suite")
    print("=" * 60)
    print("\nMake sure the Flask app is running on localhost:5000")
    print("Press Ctrl+C at any time to exit\n")
    
    try:
        # Test initial status
        test_status()
        
        # List available effects
        test_list_effects()
        
        # Test heartbeat effect
        test_effect("heart", duration=5)
        
        # Test wave effect (will auto-stop heartbeat)
        test_effect("wave", duration=5)
        
        # Test flame effect
        test_effect("flame", duration=5)
        
        # Stop all effects
        test_stop()
        
        # Check final status
        test_status()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask app.")
        print("Make sure the app is running: python main.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        test_stop()  # Try to stop effects before exiting
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
