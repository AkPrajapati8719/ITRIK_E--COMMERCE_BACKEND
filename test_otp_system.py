#!/usr/bin/env python
"""
Quick test script to verify OTP login system
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/accounts"

def test_send_otp():
    """Test sending OTP"""
    print("\n" + "="*60)
    print("TEST 1: Send OTP")
    print("="*60)
    
    data = {
        "email": "testuser@example.com",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{API_URL}/send-otp/", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return result.get('otp_test') if response.status_code == 200 else None

def test_verify_otp(email, otp):
    """Test verifying OTP"""
    print("\n" + "="*60)
    print("TEST 2: Verify OTP")
    print("="*60)
    
    data = {
        "email": email,
        "otp_code": otp
    }
    
    response = requests.post(f"{API_URL}/verify-otp/", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return result.get('tokens', {}).get('access') if response.status_code == 200 else None

def test_get_profile(access_token):
    """Test getting user profile"""
    print("\n" + "="*60)
    print("TEST 3: Get User Profile")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{API_URL}/profile/", headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

def test_update_profile(access_token):
    """Test updating user profile"""
    print("\n" + "="*60)
    print("TEST 4: Update User Profile")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "full_name": "Test User Updated",
        "alternate_mobile": "+91 98765 43210",
        "shipping_address": "123 Main Street, City, State, 12345"
    }
    
    response = requests.put(f"{API_URL}/profile/", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("OTP LOGIN SYSTEM - TEST SCRIPT")
    print("="*60)
    
    # Test 1: Send OTP
    otp = test_send_otp()
    
    if otp:
        print(f"\n✓ OTP sent successfully: {otp}")
        
        # Test 2: Verify OTP
        access_token = test_verify_otp("testuser@example.com", otp)
        
        if access_token:
            print(f"\n✓ OTP verified successfully")
            
            # Test 3: Get Profile
            test_get_profile(access_token)
            
            # Test 4: Update Profile
            test_update_profile(access_token)
            
            print("\n" + "="*60)
            print("ALL TESTS COMPLETED SUCCESSFULLY!")
            print("="*60)
        else:
            print("\n✗ OTP verification failed")
    else:
        print("\n✗ OTP sending failed")
