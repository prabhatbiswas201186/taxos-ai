import os, sys, traceback
from pathlib import Path

# Ensure backend src is importable
sys.path.insert(0, str(Path("C:/Users/prabh/taxos-ai/backend/src").resolve()))

from fastapi.testclient import TestClient
from main import app, IndianTaxEngine

client = TestClient(app)

FAILURES = []

def ok(msg):
    print("PASS:", msg)

def fail(msg, exc=None):
    FAILURES.append((msg, exc))
    print("FAIL:", msg)
    if exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__)

# 1) Module-level import must not fail
if 'IndianTaxEngine' not in globals() or 'app' not in globals():
    fail("Top-level import failed: IndianTaxEngine or app missing")
else:
    ok("Top-level import (main + IndianTaxEngine)")

# 2) Engine basic calls
try:
    old = IndianTaxEngine.calculate_old_regime_income_tax(800000, 100000)
    ok("IndianTaxEngine.calculate_old_regime_income_tax")
except Exception as e:
    fail("IndianTaxEngine.calculate_old_regime_income_tax", e)

try:
    new = IndianTaxEngine.calculate_new_regime_income_tax(800000)
    ok("IndianTaxEngine.calculate_new_regime_income_tax")
except Exception as e:
    fail("IndianTaxEngine.calculate_new_regime_income_tax", e)

try:
    opps = IndianTaxEngine.find_optimization_opportunities(800000, "old", {"80C": 50000, "80D": 0})
    ok("IndianTaxEngine.find_optimization_opportunities")
except Exception as e:
    fail("IndianTaxEngine.find_optimization_opportunities", e)

# 3) FastAPI routes via TestClient POST body
endpoints = [
    ("POST", "/health", None),
    ("POST", "/api/v1/auth/register", {"email":"test@example.com","name":"t","country":"India"}),
    ("POST", "/api/v1/profile", {"email":"p@example.com","name":"t","country":"India"}),
    ("POST", "/api/v1/tax/analyze", {"userId":"u1","income":800000,"deductions":{"80C":50000},"regime":"old","fy":"2025-26"}),
    ("POST", "/api/v1/gst/reconcile", {"userId":"u1","gstr1":[],"gstr3b":[],"purchaseRegister":[]}),
    ("POST", "/api/v1/cashflow/forecast", {"userId":"u1","revenueHistory":[],"expenseHistory":[],"period":"365d"}),
    ("POST", "/api/v1/compliance/check", {"userId":"u1","businessId":"b1","filings":{}}),
    ("POST", "/api/v1/compliance/generate-tasks", None),  # query params (form-encoded -> None body)
    ("POST", "/api/v1/invoices", {"userId":"u1","businessId":"b1"}),
    ("POST", "/api/v1/expenses", {"userId":"u1","businessId":"b1"}),
    ("POST", "/api/v1/audit/analyze", None),  # query params
    ("POST", "/api/v1/chat", {"userId":"u1","message":"hi"}),
]

# Endpoints that expect params in query / form instead of JSON body
query_endpoints = {
    "/api/v1/compliance/generate-tasks": {"businessId":"b1","legalStructure":"private_limited","state":"KA"},
    "/api/v1/audit/analyze": {"userId":"u1","businessId":"b1"},
}

for method, path, body in endpoints:
    try:
        if method == "GET":
            r = client.get(path)
        else:
            if path in query_endpoints:
                r = client.post(path, data=query_endpoints[path])
            else:
                r = client.post(path, json=body)
        status = r.status_code
        if status >= 500:
            fail(f"/post {path} -> HTTP {status}: {r.text[:300]}", RuntimeError(f"HTTP {status}"))
        else:
            ok(f"/post {path} -> HTTP {status}")
    except NameError as e:
        fail(f"/post {path} NameError", e)
    except KeyError as e:
        fail(f"/post {path} KeyError", e)
    except TypeError as e:
        fail(f"/post {path} TypeError", e)
    except Exception as e:
        fail(f"/post {path} unexpected", e)

# 4) GET list endpoints
for path in ["/api/v1/profile/u1","/api/v1/expenses/u1","/api/v1/invoices/u1","/api/v1/audit/findings/u1","/api/v1/chat/history/u1","/api/v1/regulations/india","/api/v1/modules","/api/v1/dashboard/u1"]:
    try:
        r = client.get(path)
        if r.status_code >= 500:
            fail(f"/get {path} -> HTTP {r.status_code}: {r.text[:300]}")
        else:
            ok(f"/get {path} -> HTTP {r.status_code}")
    except Exception as e:
        fail(f"/get {path} unexpected", e)

if FAILURES:
    print("\n=== SUMMARY: FAILURES ===")
    for msg, exc in FAILURES:
        print("-", msg)
    sys.exit(1)
else:
    print("\n=== SUMMARY: ALL CHECKS PASSED ===")
    sys.exit(0)
