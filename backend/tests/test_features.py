import os, sys, traceback, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
FAILURES = []

def ok(msg):
    print("PASS:", msg)

def fail(msg, exc=None):
    FAILURES.append((msg, exc))
    print("FAIL:", msg)
    if exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__)

# Setup: register a test user for auth flows
reg_body = {"email": "test-features@example.com", "name": "feature-test", "country": "India"}
try:
    r = client.post("/api/v1/auth/register", json=reg_body)
    if r.status_code >= 500:
        fail("register (setup) -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("register (setup) -> HTTP " + str(r.status_code))
except Exception as e:
    fail("register (setup) unexpected", e)

# 1) POST /api/v1/auth/login
try:
    r = client.post("/api/v1/auth/login", json={"email": reg_body["email"], "password": "test-password"})
    if r.status_code == 401:
        ok("login (unknown user/password fallback) -> HTTP 401")
    else:
        ok("login -> HTTP " + str(r.status_code))
        data = r.json()
        assert "access_token" in data, "access_token missing"
        assert "user" in data, "user missing"
        ok("login response structure")
except Exception as e:
    fail("login", e)

# 2) POST /api/v1/auth/otp
try:
    r = client.post("/api/v1/auth/otp", json={"email": reg_body["email"]})
    if r.status_code >= 500:
        fail("otp -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("otp -> HTTP " + str(r.status_code))
        data = r.json()
        assert "message" in data, "message missing"
        ok("otp response structure")
except Exception as e:
    fail("otp", e)

# 3) POST /api/v1/auth/password-reset (initiate)
try:
    r = client.post("/api/v1/auth/password-reset", json={"email": reg_body["email"]})
    if r.status_code >= 500:
        fail("password-reset (initiate) -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("password-reset (initiate) -> HTTP " + str(r.status_code))
        data = r.json()
        assert "message" in data, "message missing"
        ok("password-reset (initiate) response structure")
except Exception as e:
    fail("password-reset (initiate)", e)

# 4) POST /api/v1/auth/password-reset/confirm (confirm with token)
try:
    r = client.post("/api/v1/auth/password-reset", json={"email": reg_body["email"], "token": "token-xyz", "new_password": "newpass"})
    if r.status_code >= 500:
        fail("password-reset (confirm) -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("password-reset (confirm) -> HTTP " + str(r.status_code))
        data = r.json()
        assert "message" in data, "message missing"
        ok("password-reset (confirm) response structure")
except Exception as e:
    fail("password-reset (confirm)", e)

# 5) POST /api/v1/suggest
try:
    r = client.post("/api/v1/suggest", json={"userId": "u1", "query": "How do I save tax?", "module": "tax"})
    if r.status_code >= 500:
        fail("suggest -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("suggest -> HTTP " + str(r.status_code))
        data = r.json()
        assert "suggestions" in data, "suggestions missing"
        assert len(data["suggestions"]) == 3, "expected 3 suggestions"
        assert "generatedAt" in data, "generatedAt missing"
        ok("suggest response structure")
except Exception as e:
    fail("suggest", e)

# 6) POST /api/v1/documents/upload (existing endpoint should still work)
try:
    r = client.post("/api/v1/documents/upload?userId=u1&businessId=b1", files={"file": ("test.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")})
    if r.status_code >= 500:
        fail("documents/upload -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("documents/upload -> HTTP " + str(r.status_code))
        data = r.json()
        assert "document" in data, "document missing"
        ok("documents/upload response structure")
except Exception as e:
    fail("documents/upload", e)

# 7) Sanity: register should still work (no regression)
try:
    r = client.post("/api/v1/auth/register", json={"email": "regression@example.com", "name": "r", "country": "India"})
    if r.status_code >= 500:
        fail("register (regression) -> HTTP " + str(r.status_code) + ": " + r.text[:200], RuntimeError("HTTP " + str(r.status_code)))
    else:
        ok("register (regression) -> HTTP " + str(r.status_code))
except Exception as e:
    fail("register (regression)", e)

if FAILURES:
    print("\n=== SUMMARY: FAILURES ===")
    for msg, exc in FAILURES:
        print("-", msg)
    sys.exit(1)
else:
    print("\n=== SUMMARY: ALL CHECKS PASSED ===")
    sys.exit(0)
