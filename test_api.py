#!/usr/bin/env python3
"""
ITRIK E-Commerce API Test Script
Tests all API endpoints and functionality
Run this after starting the Django server
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_test(message):
    print(f"\n{Colors.YELLOW}→ {message}{Colors.RESET}")

# Global tokens for authenticated requests
access_token = None
refresh_token = None
test_user = {
    "mobile_number": "9876543210",
    "full_name": "Test User"
}

def test_api_home():
    """Test API home endpoint"""
    print_test("Testing API Home Endpoint")
    try:
        response = requests.get(BASE_URL.replace("/api", ""))
        data = response.json()
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "message" in data, "Missing 'message' in response"
        assert "endpoints" in data, "Missing 'endpoints' in response"
        
        print_success(f"API Home: {data['message']}")
        print_info(f"Version: {data.get('version', 'N/A')}")
        return True
    except Exception as e:
        print_error(f"API Home Error: {str(e)}")
        return False

def test_send_otp():
    """Test OTP sending"""
    global test_user
    print_test("Testing OTP Send")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/send-otp/",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        data = response.json()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data.get("success") == True, "OTP sending failed"
        
        otp = data.get("otp_test")
        print_success(f"OTP Sent Successfully")
        print_info(f"Test OTP: {otp}")
        
        return otp
    except Exception as e:
        print_error(f"OTP Send Error: {str(e)}")
        return None

def test_verify_otp(otp):
    """Test OTP verification and login"""
    global access_token, refresh_token
    print_test("Testing OTP Verification & Login")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/verify-otp/",
            json={
                "mobile_number": test_user["mobile_number"],
                "otp_code": otp
            },
            headers={"Content-Type": "application/json"}
        )
        
        data = response.json()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data.get("success") == True, "OTP verification failed"
        
        tokens = data.get("tokens", {})
        access_token = tokens.get("access")
        refresh_token = tokens.get("refresh")
        
        print_success(f"OTP Verified Successfully")
        print_success(f"Logged in as: {data['user'].get('full_name')}")
        print_info(f"Access Token: {access_token[:30]}...")
        
        return True
    except Exception as e:
        print_error(f"OTP Verification Error: {str(e)}")
        return False

def get_headers():
    """Get request headers with authentication"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

def test_get_products():
    """Test getting products"""
    print_test("Testing Get Products")
    try:
        response = requests.get(
            f"{BASE_URL}/products/",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print_success(f"Products Retrieved")
        print_info(f"Total Products: {data.get('count', 0)}")
        
        if data.get('results'):
            first_product = data['results'][0]
            print_info(f"First Product: {first_product.get('name')} - ${first_product.get('price')}")
            return first_product.get('id')
        return None
    except Exception as e:
        print_error(f"Get Products Error: {str(e)}")
        return None

def test_get_categories():
    """Test getting product categories"""
    print_test("Testing Get Categories")
    try:
        response = requests.get(
            f"{BASE_URL}/products/categories/",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print_success(f"Categories Retrieved")
        print_info(f"Total Categories: {data.get('count', 0)}")
        
        if data.get('results'):
            for cat in data['results'][:3]:
                print_info(f"- {cat.get('name')} ({cat.get('product_count', 0)} products)")
        
        return True
    except Exception as e:
        print_error(f"Get Categories Error: {str(e)}")
        return False

def test_add_to_cart(product_id):
    """Test adding item to cart"""
    print_test("Testing Add to Cart")
    try:
        if not product_id:
            print_info("Skipping - No product found")
            return None
        
        response = requests.post(
            f"{BASE_URL}/cart/add/",
            json={"product_id": product_id, "quantity": 1},
            headers=get_headers()
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, "Add to cart failed"
        
        print_success(f"Item Added to Cart")
        cart = data.get('cart', {})
        print_info(f"Cart Total: ${cart.get('total', 'N/A')}")
        
        return True
    except Exception as e:
        print_error(f"Add to Cart Error: {str(e)}")
        return False

def test_get_cart():
    """Test getting cart"""
    print_test("Testing Get Cart")
    try:
        response = requests.get(
            f"{BASE_URL}/cart/",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        cart = response.json()
        
        print_success(f"Cart Retrieved")
        print_info(f"Items in Cart: {len(cart.get('items', []))}")
        print_info(f"Cart Total: ${cart.get('total', 'N/A')}")
        
        return cart
    except Exception as e:
        print_error(f"Get Cart Error: {str(e)}")
        return None

def test_create_order():
    """Test creating an order"""
    print_test("Testing Create Order")
    try:
        response = requests.post(
            f"{BASE_URL}/orders/create/",
            json={
                "shipping_address": "123 Test St, Test City, TC 12345",
                "payment_method": "cod",
                "phone_number": "9876543210"
            },
            headers=get_headers()
        )
        
        if response.status_code == 400:
            print_info("Cart is empty - cannot create order (expected)")
            return None
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, "Order creation failed"
        
        order = data.get('order', {})
        print_success(f"Order Created Successfully")
        print_info(f"Order Number: {order.get('order_number')}")
        print_info(f"Order Total: ${order.get('total')}")
        print_info(f"Status: {order.get('status')}")
        
        return order.get('id')
    except Exception as e:
        print_error(f"Create Order Error: {str(e)}")
        return None

def test_get_orders():
    """Test getting user orders"""
    print_test("Testing Get Orders")
    try:
        response = requests.get(
            f"{BASE_URL}/orders/",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print_success(f"Orders Retrieved")
        print_info(f"Total Orders: {data.get('count', 0)}")
        
        if data.get('results'):
            for order in data['results'][:3]:
                print_info(f"- {order.get('order_number')}: ${order.get('total')} ({order.get('status')})")
        
        return True
    except Exception as e:
        print_error(f"Get Orders Error: {str(e)}")
        return False

def test_refresh_token():
    """Test token refresh"""
    print_test("Testing Token Refresh")
    try:
        response = requests.post(
            f"{BASE_URL}/token/refresh/",
            json={"refresh": refresh_token},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print_success(f"Token Refreshed")
        print_info(f"New Access Token: {data.get('access', 'N/A')[:30]}...")
        
        return True
    except Exception as e:
        print_error(f"Token Refresh Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"ITRIK E-Commerce API Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.RESET}\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: API Home
    tests_total += 1
    if test_api_home():
        tests_passed += 1
    
    # Test 2: Send OTP
    tests_total += 1
    otp = test_send_otp()
    if otp:
        tests_passed += 1
    
    # Test 3: Verify OTP
    tests_total += 1
    if otp and test_verify_otp(otp):
        tests_passed += 1
    
    if not access_token:
        print_error("Cannot continue without valid authentication")
        return
    
    # Test 4: Get Products
    tests_total += 1
    product_id = test_get_products()
    if product_id:
        tests_passed += 1
    
    # Test 5: Get Categories
    tests_total += 1
    if test_get_categories():
        tests_passed += 1
    
    # Test 6: Add to Cart
    tests_total += 1
    if product_id and test_add_to_cart(product_id):
        tests_passed += 1
    
    # Test 7: Get Cart
    tests_total += 1
    cart = test_get_cart()
    if cart:
        tests_passed += 1
    
    # Test 8: Create Order
    tests_total += 1
    order_id = test_create_order()
    if order_id or (order_id is None and cart and len(cart.get('items', [])) == 0):
        tests_passed += 1
    
    # Test 9: Get Orders
    tests_total += 1
    if test_get_orders():
        tests_passed += 1
    
    # Test 10: Refresh Token
    tests_total += 1
    if refresh_token and test_refresh_token():
        tests_passed += 1
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{Colors.RESET}")
    print(f"Tests Passed: {Colors.GREEN}{tests_passed}/{tests_total}{Colors.RESET}")
    print(f"Success Rate: {Colors.GREEN if tests_passed == tests_total else Colors.YELLOW}{(tests_passed/tests_total)*100:.1f}%{Colors.RESET}\n")
    
    if tests_passed == tests_total:
        print(f"{Colors.GREEN}✓ All tests passed! System is fully operational.{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}⚠ Some tests failed. Please review the output above.{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error: {str(e)}{Colors.RESET}\n")
