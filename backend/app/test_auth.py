import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_authentication_suite():
    print("=" * 60)
    print("      CIVICVISION AI — AUTHENTICATION & RBAC TEST SUITE")
    print("=" * 60)

    # 1. Test Registration
    citizen_reg_payload = {
        "full_name": "Test Citizen User",
        "email": "citizen.test@civicvision.ai",
        "password": "Password@123",
        "role": "CITIZEN"
    }

    res_reg = client.post("/api/v1/auth/register", json=citizen_reg_payload)
    if res_reg.status_code == 201:
        print("[+] 1. Registration Test: PASSED (201 Created)")
    elif res_reg.status_code == 400 and "already exists" in res_reg.text:
        print("[+] 1. Registration Test: PASSED (Existing test user verified)")
    else:
        print(f"[-] 1. Registration Test FAILED: {res_reg.status_code} - {res_reg.text}")

    # Register Admin & Officer for RBAC testing
    admin_reg_payload = {
        "full_name": "Test Admin User",
        "email": "admin.test@civicvision.ai",
        "password": "Password@123",
        "role": "ADMIN"
    }
    client.post("/api/v1/auth/register", json=admin_reg_payload)

    officer_reg_payload = {
        "full_name": "Test Officer User",
        "email": "officer.test@civicvision.ai",
        "password": "Password@123",
        "role": "OFFICER"
    }
    client.post("/api/v1/auth/register", json=officer_reg_payload)

    # 2. Test Successful Login
    res_login_citizen = client.post("/api/v1/auth/login", json={
        "email": "citizen.test@civicvision.ai",
        "password": "Password@123"
    })
    
    assert res_login_citizen.status_code == 200, f"Login failed: {res_login_citizen.text}"
    citizen_token = res_login_citizen.json()["access_token"]
    print("[+] 2. Login Test: PASSED (JWT Token Issued)")

    # Login Admin & Officer
    res_login_admin = client.post("/api/v1/auth/login", json={"email": "admin.test@civicvision.ai", "password": "Password@123"})
    admin_token = res_login_admin.json()["access_token"]

    res_login_officer = client.post("/api/v1/auth/login", json={"email": "officer.test@civicvision.ai", "password": "Password@123"})
    officer_token = res_login_officer.json()["access_token"]

    # 3. Test Invalid Login
    res_invalid_login = client.post("/api/v1/auth/login", json={
        "email": "citizen.test@civicvision.ai",
        "password": "WrongPassword999"
    })
    assert res_invalid_login.status_code == 401, "Invalid login failed to reject"
    print("[+] 3. Invalid Login Rejection Test: PASSED (401 Unauthorized)")

    # 4. Test Protected Route Access (/me)
    headers_citizen = {"Authorization": f"Bearer {citizen_token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers_citizen)
    assert res_me.status_code == 200, f"Protected /me endpoint failed: {res_me.text}"
    assert res_me.json()["email"] == "citizen.test@civicvision.ai"
    print("[+] 4. Protected Route Access (/me): PASSED (200 OK)")

    # 5. Test Role-Based Access Control (RBAC)
    # Citizen accessing Citizen route -> 200
    res_cit_route = client.get("/api/v1/auth/test/citizen", headers=headers_citizen)
    assert res_cit_route.status_code == 200, "Citizen failed to access citizen route"

    # Citizen trying to access Admin route -> 403 Forbidden
    res_cit_admin = client.get("/api/v1/auth/test/admin", headers=headers_citizen)
    assert res_cit_admin.status_code == 403, "Citizen was illegally allowed admin route access"

    # Admin accessing Admin route -> 200
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    res_admin_route = client.get("/api/v1/auth/test/admin", headers=headers_admin)
    assert res_admin_route.status_code == 200, "Admin failed to access admin route"

    # Officer accessing Officer route -> 200
    headers_officer = {"Authorization": f"Bearer {officer_token}"}
    res_officer_route = client.get("/api/v1/auth/test/officer", headers=headers_officer)
    assert res_officer_route.status_code == 200, "Officer failed to access officer route"

    print("[+] 5. Role-Based Access Control (RBAC): PASSED (403 Forbidden on unauthorized roles)")
    print("=" * 60)
    print("      ALL AUTHENTICATION & ROLE AUTHORIZATION TESTS PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_authentication_suite()
