import requests, json, sys

BASE = "https://taxos-ai.vercel.app"
API = f"{BASE}/api/v1"

results = []

def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

# 1. Health
r = requests.get(f"{BASE}/health", timeout=15)
check("health", r.status_code == 200, f"status={r.status_code}")

# 2. Modules
r = requests.get(f"{API}/modules", timeout=15)
check("modules", r.status_code == 200 and "modules" in r.json(), f"status={r.status_code}")

# 3. Tax analysis (POST JSON body)
r = requests.post(f"{API}/tax/analyze", json={"userId":"u1","income":1200000,"deductions":{"80C":150000},"regime":"old","fy":"2025-26"}, timeout=15)
check("tax/analyze", r.status_code == 200 and "regimeComparison" in r.json(), f"status={r.status_code}")

# 4. GST reconcile
r = requests.post(f"{API}/gst/reconcile", json={"userId":"u1","gstr1":[],"gstr3b":[],"purchaseRegister":[]}, timeout=15)
check("gst/reconcile", r.status_code == 200 and "totalIssues" in r.json(), f"status={r.status_code}")

# 5. Compliance check
r = requests.post(f"{API}/compliance/check", json={"userId":"u1","businessId":"b1","filings":{}}, timeout=15)
check("compliance/check", r.status_code == 200 and "complianceScore" in r.json(), f"status={r.status_code}")

# 6. Cashflow forecast
r = requests.post(f"{API}/cashflow/forecast", json={"userId":"u1","revenueHistory":[{"amount":150000}],"expenseHistory":[{"amount":90000}],"period":"365d"}, timeout=15)
check("cashflow/forecast", r.status_code == 200 and "projections" in r.json(), f"status={r.status_code}")

# 7. Chat endpoint - JSON body (frontend style)
r = requests.post(f"{API}/chat", json={"userId":"u1","message":"test hello","module":"general"}, timeout=15)
check("chat (json body)", r.status_code == 200 and "response" in r.json(), f"status={r.status_code} body={r.text[:80]}")

# 8. Chat endpoint - query params (backend now only accepts JSON body, so this should not be 200 for production)
r = requests.post(f"{API}/chat?userId=u1&message=test&module=general", timeout=15)
check("chat (query params)", r.status_code != 200, f"status={r.status_code} (expected non-200, endpoint uses JSON body)")

# 9. Regulations
r = requests.get(f"{API}/regulations/india", timeout=15)
check("regulations/india", r.status_code == 200 and "regulations" in r.json(), f"status={r.status_code}")

# 10. Audit analyze (query params as used by frontend)
r = requests.post(f"{API}/audit/analyze?userId=u1&businessId=b1", timeout=15)
check("audit/analyze (query)", r.status_code == 200 and "riskScore" in r.json(), f"status={r.status_code}")

# 11. Dashboard
r = requests.get(f"{API}/dashboard/u1", timeout=15)
check("dashboard", r.status_code == 200 and "financials" in r.json(), f"status={r.status_code}")

# 12. Supabase readable?
r = requests.get("https://kjkwruzkfrxfwaokzqbs.supabase.co/rest/v1/profiles?select=count", headers={"apikey":"sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE","Authorization":"Bearer sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE"}, timeout=15)
check("supabase profiles readable", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")

# 13. Supabase documents table readable?
r = requests.get("https://kjkwruzkfrxfwaokzqbs.supabase.co/rest/v1/documents?select=count", headers={"apikey":"sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE","Authorization":"Bearer sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE"}, timeout=15)
check("supabase documents readable", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")

# 14. Supabase chat_history readable?
r = requests.get("https://kjkwruzkfrxfwaokzqbs.supabase.co/rest/v1/chat_history?select=count", headers={"apikey":"sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE","Authorization":"Bearer sb_publishable_jA8qt1LWb95oQYnUh-59fA_klPe8kXE"}, timeout=15)
check("supabase chat_history readable", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")

# 15. Admin login
r = requests.post(f"{API}/admin/login", json={"token":"change-me-admin-token"}, timeout=15)
check("admin/login", r.status_code == 200, f"status={r.status_code}")

# 16. Admin users list (needs auth)
r = requests.get(f"{API}/admin/users", headers={"Authorization":"Bearer change-me-admin-token"}, timeout=15)
check("admin/users", r.status_code == 200 and "users" in r.json(), f"status={r.status_code}")

# 17. Admin stats
r = requests.get(f"{API}/admin/stats", headers={"Authorization":"Bearer change-me-admin-token"}, timeout=15)
check("admin/stats", r.status_code == 200 and "totalUsers" in r.json(), f"status={r.status_code}")

# 18. Admin config
r = requests.get(f"{API}/admin/config", headers={"Authorization":"Bearer change-me-admin-token"}, timeout=15)
check("admin/config", r.status_code == 200 and "modules" in r.json(), f"status={r.status_code}")

passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
print(f"\n=== SUMMARY: {passed} passed, {failed} failed out of {len(results)} ===")
sys.exit(0 if failed == 0 else 1)
