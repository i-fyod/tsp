"""
Test script for FastAPI KR2 - All tasks
"""

import json
import subprocess
import time
import sys

# Base URL
BASE_URL = "http://localhost:8000"


def print_test(task, method, path, description):
    print(f"\n{'=' * 70}")
    print(f"TASK: {task}")
    print(f"METHOD: {method} {path}")
    print(f"DESCRIPTION: {description}")
    print(f"{'=' * 70}")


def test_task_31():
    """Test Task 3.1: User Creation"""
    print_test("3.1", "POST", "/create_user", "User creation with validation")

    # Valid user
    cmd = [
        "curl",
        "-X",
        "POST",
        f"{BASE_URL}/create_user",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(
            {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 30,
                "is_subscribed": True,
            }
        ),
    ]
    print("\n✓ Valid user:")
    subprocess.run(cmd)

    # Invalid age (negative)
    print("\n\n✗ Invalid age (negative):")
    cmd = [
        "curl",
        "-X",
        "POST",
        f"{BASE_URL}/create_user",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(
            {
                "name": "Bob",
                "email": "bob@example.com",
                "age": -5,
                "is_subscribed": False,
            }
        ),
    ]
    subprocess.run(cmd)

    # Invalid email
    print("\n\n✗ Invalid email:")
    cmd = [
        "curl",
        "-X",
        "POST",
        f"{BASE_URL}/create_user",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps({"name": "Charlie", "email": "invalid-email", "age": 25}),
    ]
    subprocess.run(cmd)


def test_task_32():
    """Test Task 3.2: Product Search"""
    print_test(
        "3.2", "GET", "/product/{id} & /products/search", "Product retrieval and search"
    )

    # Get product by ID
    print("\n✓ Get product by ID (123):")
    subprocess.run(["curl", f"{BASE_URL}/product/123"])

    # Get non-existent product
    print("\n\n✗ Non-existent product (999):")
    subprocess.run(["curl", f"{BASE_URL}/product/999"])

    # Search with keyword
    print("\n\n✓ Search with keyword 'phone':")
    subprocess.run(["curl", f"{BASE_URL}/products/search?keyword=phone"])

    # Search with category
    print("\n\n✓ Search with keyword 'phone' and category 'Electronics':")
    subprocess.run(
        [
            "curl",
            f"{BASE_URL}/products/search?keyword=phone&category=Electronics&limit=5",
        ]
    )

    # Search with limit
    print("\n\n✓ Search with keyword 'phone' limited to 2 results:")
    subprocess.run(["curl", f"{BASE_URL}/products/search?keyword=phone&limit=2"])


def test_task_51():
    """Test Task 5.1: Basic Cookie Auth"""
    print_test("5.1", "POST /login & GET /user", "Basic cookie-based authentication")

    # Login
    print("\n✓ Login with valid credentials:")
    result = subprocess.run(
        [
            "curl",
            "-X",
            "POST",
            f"{BASE_URL}/login",
            "-d",
            "username=user123&password=password123",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)

    # Extract cookie from response (would need parsing in real scenario)
    print("\n\n✗ Login with invalid credentials:")
    subprocess.run(
        [
            "curl",
            "-X",
            "POST",
            f"{BASE_URL}/login",
            "-d",
            "username=user123&password=wrongpassword",
        ]
    )


def test_task_54():
    """Test Task 5.4: Headers Extraction"""
    print_test(
        "5.4", "GET", "/headers", "Extract User-Agent and Accept-Language headers"
    )

    # Valid headers
    print("\n✓ With valid headers:")
    subprocess.run(
        [
            "curl",
            f"{BASE_URL}/headers",
            "-H",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "-H",
            "Accept-Language: en-US,en;q=0.9,es;q=0.8",
        ]
    )

    # Missing User-Agent
    print("\n\n✗ Missing User-Agent:")
    subprocess.run(
        ["curl", f"{BASE_URL}/headers", "-H", "Accept-Language: en-US,en;q=0.9"]
    )

    # Invalid Accept-Language format
    print("\n\n✗ Invalid Accept-Language format:")
    subprocess.run(
        [
            "curl",
            f"{BASE_URL}/headers",
            "-H",
            "User-Agent: Mozilla/5.0",
            "-H",
            "Accept-Language: ,,,",
        ]
    )


def test_task_55():
    """Test Task 5.5: CommonHeaders Model"""
    print_test(
        "5.5", "GET", "/info & /headers_v2", "CommonHeaders model with reusable headers"
    )

    # GET /info
    print("\n✓ GET /info with CommonHeaders:")
    result = subprocess.run(
        [
            "curl",
            f"{BASE_URL}/info",
            "-H",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "-H",
            "Accept-Language: en-US,en;q=0.9",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print("\nResponse Headers:")
    print(result.stderr)

    # GET /headers_v2
    print("\n\n✓ GET /headers_v2 with CommonHeaders:")
    subprocess.run(
        [
            "curl",
            f"{BASE_URL}/headers_v2",
            "-H",
            "User-Agent: Mozilla/5.0",
            "-H",
            "Accept-Language: fr-FR,fr;q=0.9",
        ]
    )


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║         FastAPI КР2 - Integration Test Suite                       ║
    ║                                                                    ║
    ║  Make sure kr2_app.py is running on http://localhost:8000          ║
    ║  Run: python kr2_app.py (in separate terminal)                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Check if server is running
        subprocess.run(
            ["curl", "-s", f"{BASE_URL}/docs"],
            capture_output=True,
            check=True,
            timeout=2,
        )
    except Exception as e:
        print(f"ERROR: Server not running at {BASE_URL}")
        print(f"Start the server with: python kr2_app.py")
        sys.exit(1)

    print("\n✓ Server is running!")
    print("\nRunning tests...\n")

    test_task_31()
    print("\n\n" + "█" * 70)

    test_task_32()
    print("\n\n" + "█" * 70)

    test_task_51()
    print("\n\n" + "█" * 70)

    test_task_54()
    print("\n\n" + "█" * 70)

    test_task_55()

    print("\n\n" + "=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
