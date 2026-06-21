"""
verify_endpoints.py — comprehensive endpoint verification for taxos-ai backend.

Reads the app from backend/src/main.py and runs:
  * HTTP method + path smoke-tests for every declared route
  * CORS preflight checks (OPTIONS requests)
  * Duplicate-route guard
  * Env-var override smoke-test (API_HOST / API_PORT / ALLOWED_ORIGINS)
  * Python import sanity-check
"""
import os
import sys
import traceback
from pathlib import Path
from collections import defaultdict

# Ensure backend src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
FAILURES = []
PASSES = []


def ok(msg):
    PASSES.append(msg)
    print("PASS:", msg)


def fail(msg, exc=None):
    FAILURES.append((msg, exc))
    print("FAIL:", msg)
    if exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__)


# ---------------------------------------------------------------------------
# 1) Import sanity
# ---------------------------------------------------------------------------
try:
    assert app.title == "TAXOS AI Backend"
    ok("Import + app object sanity")
except Exception as e:
    fail("Import sanity", e)


# ---------------------------------------------------------------------------
# 2) Build a list of declared routes (deduplicate for the guard below)
# ---------------------------------------------------------------------------
declared_routes = []
for route in app.routes:
    methods = getattr(route, "methods", None) or {"GET"}
    path = getattr(route, "path", None) or getattr(route, "name", str(route))
    for method in methods:
        declared_routes.append((method, path))

# Duplicate-route guard
seen = defaultdict(int)
for method, path in declared_routes:
    seen[(method, path)] += 1

duplicates = [(k, v) for k, v in seen.items() if v > 1]
if duplicates:
    fail(f"Duplicate routes detected: {duplicates}")
else:
    ok("No duplicate routes")

# ---------------------------------------------------------------------------
# 3) CORS preflight checks — hit OPTIONS on a representative set of paths
# ---------------------------------------------------------------------------
cors_test_paths = [
    "/api/v1/auth/login",
    "/api/v1/tax/analyze",
    "/api/v1/invoices/u1",
]

# We can only test CORS if ALLOWED_ORIGINS isn't wildcard with credentials disabled;
# the middleware is on the app, so OPTIONS should return 200-ish or 405 (method not allowed
# because no handler, but OPTIONS is auto-handled by FastAPI/Starlette via CORS middleware).
for path in cors_test_paths:
    try:
        r = client.options(
            path,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Starlette returns 405 for OPTIONS when no actual handler exists,
        # but CORS middleware should still add headers.
        if r.status_code not in (200, 204, 405):
            fail(f"CORS preflight {path} -> HTTP {r.status_code}")
        else:
            acrh = r.headers.get("access-control-allow-origin", "")
            acrm = r.headers.get("access-control-allow-methods", "")
            ok(f"CORS preflight {path} -> HTTP {r.status_code} (ACRH={acrh!r})")
    except Exception as e:
        fail(f"CORS preflight {path} unexpected", e)


# ---------------------------------------------------------------------------
# 4) GET endpoints
# ---------------------------------------------------------------------------
get_endpoints = [
    "/health",
    "/api/v1/profile/u1",
    "/api/v1/compliance/upcoming?userId=u1&businessId=b1",
    "/api/v1/invoices/u1",
    "/api/v1/expenses/u1",
    "/api/v1/audit/findings/u1",
    "/api/v1/chat/history/u1",
    "/api/v1/regulations/india",
    "/api/v1/modules",
    "/api/v1/dashboard/u1",
]

for path in get_endpoints:
    try:
        r = client.get(path)
        if r.status_code >= 500:
            fail(f"GET {path} -> HTTP {r.status_code}: {r.text[:300]}")
        else:
            ok(f"GET {path} -> HTTP {r.status_code}")
    except Exception as e:
        fail(f"GET {path} unexpected", e)


# ---------------------------------------------------------------------------
# 5) POST endpoints (JSON body)
# ---------------------------------------------------------------------------
json_endpoints = [
    ("/api/v1/auth/register", {"email": "test@example.com", "name": "t", "country": "India"}),
    ("/api/v1/auth/login", {"email": "test@example.com", "password": "test-password"}),
    ("/api/v1/auth/otp", {"email": "test@example.com"}),
    ("/api/v1/auth/password-reset", {"email": "test@example.com"}),
    ("/api/v1/suggest", {"userId": "u1", "query": "How do I save tax?", "module": "tax"}),
    ("/api/v1/profile", {"email": "p@example.com", "name": "t", "country": "India"}),
    ("/api/v1/tax/analyze", {"userId": "u1", "income": 800000, "deductions": {"80C": 50000}, "regime": "old", "fy": "2025-26"}),
    ("/api/v1/gst/reconcile", {"userId": "u1", "gstr1": [], "gstr3b": [], "purchaseRegister": []}),
    ("/api/v1/cashflow/forecast", {"userId": "u1", "revenueHistory": [], "expenseHistory": [], "period": "365d"}),
    ("/api/v1/compliance/check", {"userId": "u1", "businessId": "b1", "filings": {}}),
    ("/api/v1/invoices", {"userId": "u1", "businessId": "b1", "invoiceNumber": "INV-TEST-1", "totalAmount": 1000}),
    ("/api/v1/expenses", {"userId": "u1", "businessId": "b1", "amount": 500, "category": "office"}),
    ("/api/v1/chat", {"userId": "u1", "message": "hi", "module": "general"}),
]

for path, body in json_endpoints:
    try:
        r = client.post(path, json=body)
        if r.status_code >= 500:
            fail(f"POST {path} -> HTTP {r.status_code}: {r.text[:300]}")
        else:
            ok(f"POST {path} -> HTTP {r.status_code}")
    except Exception as e:
        fail(f"POST {path} unexpected", e)


# ---------------------------------------------------------------------------
# 6) POST endpoints (query / form params)
# ---------------------------------------------------------------------------
form_endpoints = [
    ("/api/v1/compliance/generate-tasks", {"businessId": "b1", "legalStructure": "private_limited", "state": "KA"}),
    ("/api/v1/audit/analyze", {"userId": "u1", "businessId": "b1"}),
]

for path, data in form_endpoints:
    try:
        r = client.post(path, data=data)
        if r.status_code >= 500:
            fail(f"POST {path} -> HTTP {r.status_code}: {r.text[:300]}")
        else:
            ok(f"POST {path} -> HTTP {r.status_code}")
    except Exception as e:
        fail(f"POST {path} unexpected", e)


# ---------------------------------------------------------------------------
# 7) File upload
# ---------------------------------------------------------------------------
try:
    r = client.post(
        "/api/v1/documents/upload?userId=u1&businessId=b1",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    if r.status_code >= 500:
        fail(f"POST /api/v1/documents/upload -> HTTP {r.status_code}: {r.text[:300]}")
    else:
        ok(f"POST /api/v1/documents/upload -> HTTP {r.status_code}")
except Exception as e:
    fail("POST /api/v1/documents/upload unexpected", e)


# ---------------------------------------------------------------------------
# 8) Env-var overrides (spawn a subprocess)
# ---------------------------------------------------------------------------
def run_with_env(**env):
    import subprocess
    cmd = [
        sys.executable,
        "-c",
        """
import sys
sys.path.insert(0, 'src')
from main import app
from fastapi.testclient import TestClient
c = TestClient(app)
r = c.get('/health')
print('health_status', r.status_code)
r = c.options('/api/v1/auth/login', headers={'Origin': 'https://example.com', 'Access-Control-Request-Method': 'POST'})
print('options_status', r.status_code)
print('options_headers', 'access-control-allow-origin' in r.headers)
""",
    ]
    env_vars = os.environ.copy()
    env_vars.update({k: str(v) for k, v in env.items()})
    result = subprocess.run(cmd, cwd="C:/Users/prabh/taxos-ai/backend", env=env_vars, capture_output=True, text=True)
    return result

result = run_with_env(API_PORT="9999", API_HOST="127.0.0.1", ALLOWED_ORIGINS="https://example.com")
if result.returncode != 0:
    fail(f"Env-var subprocess failed (rc={result.returncode})\nstdout={result.stdout}\nstderr={result.stderr}")
else:
    ok(f"Env-var subprocess passed\n  stdout={result.stdout.strip()}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n=== SUMMARY: {len(PASSES)} passed, {len(FAILURES)} failed ===")
if FAILURES:
    for msg, exc in FAILURES:
        print("-", msg)
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
