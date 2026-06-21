from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os, json, uuid, re
from pathlib import Path
from supabase import create_client, Client

app = FastAPI(title="TAXOS AI Backend", version="1.0.0")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
ALLOW_CREDENTIALS = os.environ.get("ALLOW_CREDENTIALS", "true").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELS ===
class UserProfile(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    phone: Optional[str] = None
    businessName: Optional[str] = None
    industry: Optional[str] = None
    legalStructure: Optional[str] = None
    country: str = "India"
    state: str = ""
    gstin: Optional[str] = None
    pan: Optional[str] = None
    turnover: Optional[float] = None
    employeeCount: Optional[int] = None

class TaxAnalysisRequest(BaseModel):
    userId: str
    income: float
    deductions: Dict[str, float]
    regime: str  # old or new
    fy: str

class GSTReconcileRequest(BaseModel):
    userId: str
    gstr1: List[Dict[str, Any]] = []
    gstr3b: List[Dict[str, Any]] = []
    purchaseRegister: List[Dict[str, Any]] = []

class CashFlowRequest(BaseModel):
    userId: str
    revenueHistory: List[Dict[str, Any]]
    expenseHistory: List[Dict[str, Any]]
    period: str = "365d"

class ComplianceCheckRequest(BaseModel):
    userId: str
    businessId: str
    filings: Dict[str, Any] = {}

class InvoiceUploadRequest(BaseModel):
    userId: str
    businessId: str
    filename: str
    fileType: str
    fileSize: int

class LoginRequest(BaseModel):
    email: str
    password: str

class OTPRequest(BaseModel):
    email: str

class PasswordResetRequest(BaseModel):
    email: str
    token: str = ""
    new_password: str = ""

class SuggestRequest(BaseModel):
    userId: str
    query: str
    context: str = ""
    module: str = "general"

class ChatRequest(BaseModel):
    userId: str
    message: str
    module: str = "general"
    context: str = ""

# === INDIAN TAX REGULATIONS DATABASE ===
INDIA_REGULATIONS = {
    "fy_2025_26": {
        "old_regime": {
            "sections": {
                "80C": {"limit": 150000, "items": ["ppf", "elss", "life_insurance", "nsc", "home_loan_principal"]},
                "80D": {"limit": 25000, "items": ["health_insurance_self"], "senior_citizen_limit": 50000},
                "80DD": {"limit": 75000, "items": ["disability_dependent"]},
                "80E": {"limit": None, "items": ["education_loan_interest"]},
                "80G": {"limit": None, "items": ["donations"], "max_deduction_pct": "100%"},
                "24b": {"limit": 200000, "items": ["home_loan_interest"]},
                "80CCD1B": {"limit": 50000, "items": ["nps_additional"]},
                "80CCD2": {"limit": None, "items": ["employer_nps"], "employer_limit_pct": "10% of basic"},
                "hra_exemption": {"calculation": "min(actual_hra, rent_paid, 50%_of_basic_for_metros)"},
            },
            "standard_deduction": 50000,
            "rebate_87A": {"limit": 500000, "rebate": 12500},
            "surcharge_thresholds": [5000000, 10000000, 20000000, 50000000],
        },
        "new_regime": {
            "standard_deduction": 75000,
            "surcharge_thresholds": [5000000, 10000000, 20000000, 50000000],
            "rebate_87A": {"limit": 1200000, "rebate": 25000},
            "tax_slabs": [
                {"upto": 400000, "rate": 0},
                {"upto": 800000, "rate": 0.05},
                {"upto": 1200000, "rate": 0.10},
                {"upto": 1600000, "rate": 0.15},
                {"upto": 2000000, "rate": 0.20},
                {"upto": 2400000, "rate": 0.25},
                {"above": 2400000, "rate": 0.30},
            ],
        }
    }
}

GST_RATES = {
    "essential_goods": 0,
    "standard": [0.05, 0.12, 0.18],
    "luxury": [0.28],
    "special_rate": 0.03,  # for precious metals etc
}

COMPLIANCE_CALENDAR = {
    "gst": {
        "gstr1_monthly": {"due_date": "11th of next month", "penalty": "50 per day", "max_penalty": "20000"},
        "gstr3b_monthly": {"due_date": "20th of next month", "penalty": "50 per day", "max_penalty": "20000"},
        "gstr1_quarterly": {"due_date": "13th of month after quarter", "penalty": "50 per day"},
        "gstr3b_quarterly": {"due_date": "24th of month after quarter", "penalty": "50 per day"},
        "annual_return": {"due_date": "31st December of next FY", "penalty": "100 per day"},
    },
    "income_tax": {
        "advance_tax": {"due_dates": ["15-Jun", "15-Sep", "15-Dec", "15-Mar"], "penalty": "1% per month u/s 234C"},
        "itr_filing": {"due_date": "31-July (individuals)", "penalty": "5000 under 139(1)"},
        "itr_filing_audit": {"due_date": "31-October", "penalty": "25000 under 139(1)"},
    },
    "tds": {
        "q1": {"due_date": "31-Jul", "penalty": "200 per day u/s 271H"},
        "q2": {"due_date": "31-Oct", "penalty": "200 per day u/s 271H"},
        "q3": {"due_date": "31-Jan", "penalty": "200 per day u/s 271H"},
        "q4": {"due_date": "31-May", "penalty": "200 per day u/s 271H"},
    },
    "pf_esi": {
        "pf_payment": {"due_date": "15th of next month", "penalty": "Damages @ 5% + interest"},
        "esi_payment": {"due_date": "15th of next month", "penalty": "various"},
    }
}

# === IN-MEMORY STORES ===
users: Dict[str, Dict] = {}
profiles: Dict[str, Dict] = {}
invoices: Dict[str, List[Dict]] = {}
expenses: Dict[str, List[Dict]] = {}
tax_records: Dict[str, List[Dict]] = {}
compliance_tasks: Dict[str, List[Dict]] = {}
documents: Dict[str, Dict] = {}
chat_sessions: Dict[str, List[Dict]] = {}
forecasts: Dict[str, Dict] = {}
audit_findings: Dict[str, List[Dict]] = {}

UPLOAD_DIR = Path("/tmp/uploads") if os.environ.get("VERCEL") else Path("./uploads")
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
APP_CONFIG = {
  "allowedFileTypes": [".pdf", ".csv", ".xlsx", ".jpg", ".jpeg", ".png"],
  "uploadMaxSize": 10 * 1024 * 1024,
}

# === SUPABASE CLIENT (optional) ===
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
supabase_client: Optional[Client] = None
try:
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception:
    supabase_client = None

class IndianTaxEngine:
    @staticmethod
    def calculate_old_regime_income_tax(total_income: float, deductions_claimed: float, fy: str = "2025-26") -> Dict:
        taxable_income = max(0, total_income - deductions_claimed - 50000)
        tax = 0
        if taxable_income <= 250000:
            tax = 0
        elif taxable_income <= 500000:
            tax = (taxable_income - 250000) * 0.05
        elif taxable_income <= 1000000:
            tax = 12500 + (taxable_income - 500000) * 0.20
        elif taxable_income <= 2000000:
            tax = 112500 + (taxable_income - 1000000) * 0.30
        else:
            tax = 412500 + (taxable_income - 2000000) * 0.30

        rebate = 0
        if total_income <= 500000:
            rebate = min(tax, 12500)
        tax_after_rebate = max(0, tax - rebate)

        surcharge = 0
        if taxable_income > 5000000 and taxable_income <= 10000000:
            surcharge = tax_after_rebate * 0.10
        elif taxable_income > 10000000 and taxable_income <= 20000000:
            surcharge = tax_after_rebate * 0.15
        elif taxable_income > 20000000:
            surcharge = tax_after_rebate * 0.25

        cess = (tax_after_rebate + surcharge) * 0.04
        total_tax = tax_after_rebate + surcharge + cess
        return {
            "regime": "old",
            "total_income": total_income,
            "deductions_claimed": deductions_claimed,
            "taxable_income": round(taxable_income, 2),
            "tax_before_rebate": round(tax, 2),
            "rebate_87A": round(rebate, 2),
            "tax_after_rebate": round(tax_after_rebate, 2),
            "surcharge": round(surcharge, 2),
            "cess": round(cess, 2),
            "total_tax": round(total_tax, 2),
            "effective_rate": round(total_tax / total_income * 100, 2) if total_income > 0 else 0,
        }

    @staticmethod
    def calculate_new_regime_income_tax(total_income: float, fy: str = "2025-26") -> Dict:
        # FY 2025-26 new regime (default)
        slabs = [
            (0, 400000, 0),
            (400000, 800000, 0.05),
            (800000, 1200000, 0.10),
            (1200000, 1600000, 0.15),
            (1600000, 2000000, 0.20),
            (2000000, 2400000, 0.25),
            (2400000, float('inf'), 0.30),
        ]

        tax = 0
        for lower, upper, rate in slabs:
            if total_income > lower:
                taxable_amount = min(total_income, upper) - lower
                tax += taxable_amount * rate

        standard_deduction = 75000
        # Rebate under 87A: full rebate if taxable income <= 12L
        if total_income <= 1200000:
            rebate = min(tax, 25000)
            tax_after_rebate = max(0, tax - rebate)
        else:
            rebate = 0
            tax_after_rebate = tax

        surcharge = 0
        if total_income > 5000000 and total_income <= 10000000:
            surcharge = tax_after_rebate * 0.10
        elif total_income > 10000000 and total_income <= 20000000:
            surcharge = tax_after_rebate * 0.15
        elif total_income > 20000000:
            surcharge = tax_after_rebate * 0.25

        cess = (tax_after_rebate + surcharge) * 0.04
        total_tax = tax_after_rebate + surcharge + cess

        # Ensure tax is never negative; income floor prevents arbitrary negatives
        total_tax = max(0, total_tax)

        return {
            "regime": "new",
            "total_income": total_income,
            "standard_deduction": standard_deduction,
            "taxable_income": round(total_income - standard_deduction, 2),
            "tax_before_rebate": round(tax, 2),
            "rebate_87A": round(rebate, 2),
            "tax_after_rebate": round(tax_after_rebate, 2),
            "surcharge": round(surcharge, 2),
            "cess": round(cess, 2),
            "total_tax": round(total_tax, 2),
            "effective_rate": round(total_tax / total_income * 100, 2) if total_income > 0 else 0,
        }

    @staticmethod
    def find_optimization_opportunities(income: float, current_regime: str, deductions: Dict[str, float], age: int = 30) -> List[Dict]:
        opportunities = []
        old_tax = IndianTaxEngine.calculate_old_regime_income_tax(income, sum(deductions.values()))
        new_tax = IndianTaxEngine.calculate_new_regime_income_tax(income)

        if new_tax["total_tax"] < old_tax["total_tax"]:
            opportunities.append({
                "type": "regime_switch",
                "priority": "high",
                "title": "Switch to New Tax Regime",
                "description": "New regime saves ₹{:,.0f}/year".format(old_tax["total_tax"] - new_tax["total_tax"]),
                "savings": old_tax["total_tax"] - new_tax["total_tax"],
                "complexity": "low",
            })

        if deductions.get("80C", 0) < 150000:
            gap = 150000 - deductions["80C"]
            opportunities.append({
                "type": "80c_optimization",
                "priority": "high",
                "title": "Maximize 80C Investments",
                "description": "Increase 80C investments by ₹{:,.0f} to save ₹{:,.0f} in tax".format(gap, gap * 0.30),
                "savings": gap * 0.30,
                "complexity": "low",
            })

        if deductions.get("80D", 0) < 25000:
            opportunities.append({
                "type": "80d_optimization",
                "priority": "medium",
                "title": "Maximize 80D Health Insurance",
                "description": "Add ₹{:,.0f} health insurance to save ₹{:,.0f}".format(25000 - deductions.get("80D", 0), (25000 - deductions.get("80D", 0)) * 0.30),
                "savings": (25000 - deductions.get("80D", 0)) * 0.30,
                "complexity": "low",
            })

        if not deductions.get("80CCD1B") and income > 2500000:
            opportunities.append({
                "type": "nps_optimization",
                "priority": "high",
                "title": "NPS Additional Investment (80CCD1B)",
                "description": "Invest ₹50,000 in NPS to save ₹15,000 in tax",
                "savings": 50000 * 0.30,
                "complexity": "medium",
            })

        return opportunities

# === AI ENGINE (Mock + Real-ready) ===
class AIEngine:
    @staticmethod
    def analyze_tax(request: TaxAnalysisRequest) -> Dict:
        old = IndianTaxEngine.calculate_old_regime_income_tax(
            request.income, sum(request.deductions.values())
        )
        new = IndianTaxEngine().calculate_new_regime_income_tax(request.income)
        opportunities = IndianTaxEngine.find_optimization_opportunities(
            request.income, request.regime, request.deductions
        )

        return {
            "userId": request.userId,
            "regimeComparison": {"old": old, "new": new},
            "recommendation": "old" if old["total_tax"] <= new["total_tax"] else "new",
            "savings": abs(old["total_tax"] - new["total_tax"]),
            "optimizationOpportunities": opportunities,
            "actionItems": [o["title"] for o in opportunities],
            "generatedAt": datetime.now().isoformat(),
        }

    @staticmethod
    def reconcile_gst(request: GSTReconcileRequest) -> Dict:
        issues = []
        itc_lost = 0.0

        gstr1_set = {inv.get("invoice_number") for inv in request.gstr1}
        gstr3b_set = {inv.get("invoice_number") for inv in request.gstr3b}
        purchase_set = {inv.get("invoice_number") for inv in request.purchaseRegister}

        missing_in_gstr1 = gstr3b_set - gstr1_set
        for inv_no in missing_in_gstr1:
            issues.append({
                "type": "gstr1_missing",
                "severity": "high",
                "invoice": inv_no,
                "description": f"Invoice {inv_no} in GSTR-3B but not in GSTR-1",
            })

        missing_itc = purchase_set - gstr3b_set
        for inv_no in missing_itc:
            inv = next((i for i in request.purchaseRegister if i.get("invoice_number") == inv_no), {})
            itc_amount = inv.get("igst", 0) + inv.get("cgst", 0) + inv.get("sgst", 0)
            issues.append({
                "type": "itc_missed",
                "severity": "medium",
                "invoice": inv_no,
                "description": f"Missed ITC of ₹{itc_amount:,.2f} on {inv_no}",
                "amountAtRisk": itc_amount,
            })
            itc_lost += itc_amount

        return {
            "userId": request.userId,
            "totalIssues": len(issues),
            "issues": issues,
            "totalITCLost": round(itc_lost, 2),
            "riskScore": min(100, len(issues) * 15),
            "recommendations": [
                "File amendments for missing GSTR-1 entries",
                "Claim missed ITC in next GSTR-3B within time limit",
                "Set up automated matching to prevent future gaps",
            ],
            "generatedAt": datetime.now().isoformat(),
        }

    @staticmethod
    def forecast_cashflow(request: CashFlowRequest) -> Dict:
        rev_data = request.revenueHistory
        exp_data = request.expenseHistory

        if not rev_data:
            return {"error": "Insufficient data"}

        avg_revenue = sum(r.get("amount", 0) for r in rev_data) / len(rev_data)
        avg_expenses = sum(e.get("amount", 0) for e in exp_data) / len(exp_data) if exp_data else avg_revenue * 0.6
        monthly_surplus = avg_revenue - avg_expenses

        periods = {"30d": 1, "90d": 3, "180d": 6, "365d": 12}
        months = periods.get(request.period, 3)

        projections = []
        current_surplus = monthly_surplus
        for m in range(months):
            current_surplus *= (1 + (0.02 if m % 2 == 0 else -0.01))  # slight growth, seasonal dip
            projections.append({
                "month": (datetime.now().replace(day=1) + timedelta(days=30 * m)).strftime("%b %Y"),
                "projectedRevenue": round(avg_revenue * (1 + 0.01 * m), 2),
                "projectedExpenses": round(avg_expenses * (1 + 0.005 * m), 2),
                "surplus": round(current_surplus, 2),
            })

        total_surplus = sum(p["surplus"] for p in projections)
        return {
            "userId": request.userId,
            "period": request.period,
            "avgMonthlyRevenue": round(avg_revenue, 2),
            "avgMonthlyExpenses": round(avg_expenses, 2),
            "projections": projections,
            "totalProjectedSurplus": round(total_surplus, 2),
            "burnRateDays": round(avg_expenses / (avg_revenue - avg_expenses) * 30, 1) if avg_revenue > avg_expenses else -1,
            "generatedAt": datetime.now().isoformat(),
        }

    @staticmethod
    def detect_anomalies(user_id: str, expenses: List[Dict], invoices: List[Dict]) -> List[Dict]:
        findings = []
        amounts = [e["amount"] for e in expenses]
        avg = sum(amounts) / len(amounts) if amounts else 0
        std = (sum((x - avg) ** 2 for x in amounts) / len(amounts)) ** 0.5 if amounts else 0

        for exp in expenses:
            if std > 0 and abs(exp["amount"] - avg) > 2 * std:
                findings.append({
                    "type": "unusual_expense",
                    "severity": "medium",
                    "description": f"Expense of ₹{exp['amount']:,.2f} is {abs(exp['amount'] - avg) / std:.1f} standard deviations from mean",
                    "amountAtRisk": exp["amount"],
                    "status": "open",
                    "createdAt": datetime.now().isoformat(),
                })

        amounts_inv = [inv["totalAmount"] for inv in invoices]
        inv_dict = {}
        for inv in invoices:
            inv_dict.setdefault(inv.get("invoiceNumber", inv.get("id")), []).append(inv)
        for inv_no, inv_list in inv_dict.items():
            if len(inv_list) > 1:
                findings.append({
                    "type": "duplicate_invoice",
                    "severity": "high",
                    "description": f"Possible duplicate invoice: {inv_no}",
                    "status": "open",
                    "createdAt": datetime.now().isoformat(),
                })

        return findings

    @staticmethod
    def chat(user_id: str, message: str, context: str = "") -> Dict:
        return {
            "user_id": user_id,
            "response": f"Based on your {context}, here's what I can tell you: {message}\n\nFor detailed analysis, connect your bank accounts and upload your documents.",
            "module": "general",
            "followups": [
                "Would you like a GST reconciliation?",
                "Do you want to compare tax regimes?",
                "Show me compliance deadlines",
            ],
            "generatedAt": datetime.now().isoformat(),
        }

# === ROUTES ===

@app.post("/api/v1/auth/login")
def login(req: LoginRequest):
    if supabase_client:
        try:
            result = supabase_client.auth.sign_in_with_password({"email": req.email, "password": req.password})
            return {
                "access_token": result.session.access_token,
                "token_type": "bearer",
                "user": {"id": result.user.id, "email": result.user.email},
            }
        except Exception:
            raise HTTPException(401, "Invalid credentials")
    else:
        for uid, user in users.items():
            if user.get("email") == req.email:
                return {"access_token": f"token-{uid}", "token_type": "bearer", "user": user}
        raise HTTPException(401, "Invalid credentials")

@app.post("/api/v1/auth/otp")
def send_otp(req: OTPRequest):
    if supabase_client:
        try:
            result = supabase_client.auth.sign_in_with_otp({"email": req.email})
            return {"message": "OTP sent", "session": {"error": None, "data": result}}
        except Exception as e:
            raise HTTPException(400, f"Failed to send OTP: {str(e)}")
    else:
        code = str(uuid.uuid4())[:6].upper()
        users[f"otp-{code}"] = {"email": req.email, "otp": code, "createdAt": datetime.now().isoformat()}
        return {"message": "OTP sent (mock)", "code": code}

@app.post("/api/v1/auth/password-reset")
def password_reset(req: PasswordResetRequest):
    if supabase_client:
        try:
            if req.token and req.new_password:
                result = supabase_client.auth.update_user(req.token, {"password": req.new_password})
                return {
                    "message": "Password reset successful",
                    "user": {"id": result.user.id, "email": result.user.email},
                }
            else:
                supabase_client.auth.reset_password_for_email(req.email)
                return {"message": "Password reset email sent"}
        except Exception as e:
            raise HTTPException(400, f"Reset failed: {str(e)}")
    else:
        if req.token and req.new_password:
            for uid, user in users.items():
                if user.get("email") == req.email:
                    return {"message": "Password reset successful (mock)", "userId": uid}
        for uid, user in users.items():
            if user.get("email") == req.email:
                return {"message": "Password reset email sent (mock)"}
        raise HTTPException(404, "User not found")

@app.post("/api/v1/suggest")
def suggest(req: SuggestRequest):
    context = req.context or req.module
    suggestions = [
        f"Consider optimizing your {context} strategy based on your query: {req.query[:60]}",
        f"Review compliance requirements for {context}",
        f"Explore tax saving opportunities related to: {req.query[:40]}",
    ]
    return {
        "query": req.query,
        "module": req.module,
        "context": context,
        "suggestions": suggestions,
        "generatedAt": datetime.now().isoformat(),
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "taxos-backend", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/auth/register")
def register(profile: UserProfile):
    uid = str(uuid.uuid4())
    users[uid] = {"id": uid, "email": profile.email, "createdAt": datetime.now().isoformat()}
    profiles[uid] = profile.dict() | {"id": uid}
    return {"userId": uid, "email": profile.email, "name": profile.name}

@app.post("/api/v1/profile")
def save_profile(profile: UserProfile):
    uid = profile.id or str(uuid.uuid4())
    profiles[uid] = profile.dict() | {"id": uid}
    return {"success": True, "profile": profiles[uid]}

@app.get("/api/v1/profile/{user_id}")
def get_profile(user_id: str):
    if user_id not in profiles:
        raise HTTPException(404, "Profile not found")
    return profiles[user_id]

@app.post("/api/v1/tax/analyze")
def tax_analyze(req: TaxAnalysisRequest):
    return AIEngine.analyze_tax(req)

@app.post("/api/v1/gst/reconcile")
def gst_reconcile(req: GSTReconcileRequest):
    return AIEngine.reconcile_gst(req)

@app.post("/api/v1/cashflow/forecast")
def cashflow_forecast(req: CashFlowRequest):
    return AIEngine.forecast_cashflow(req)

@app.get("/api/v1/compliance/upcoming")
def compliance_upcoming(userId: str, businessId: str):
    tasks = compliance_tasks.get(businessId, [])
    now = datetime.now()
    upcoming = [t for t in tasks if datetime.fromisoformat(t["dueDate"]) > now]
    return {
        "userId": userId,
        "businessId": businessId,
        "upcomingTasks": upcoming[:10],
        "upcoming": len(upcoming),
    }

@app.post("/api/v1/compliance/check")
def compliance_check(req: ComplianceCheckRequest):
    tasks = compliance_tasks.get(req.businessId, [])
    now = datetime.now()
    upcoming = [t for t in tasks if datetime.fromisoformat(t["dueDate"]) > now]
    overdue = [t for t in tasks if datetime.fromisoformat(t["dueDate"]) <= now and t["status"] != "completed"]

    score = 100 - len(overdue) * 15
    score = max(0, min(100, score))

    return {
        "userId": req.userId,
        "businessId": req.businessId,
        "complianceScore": score,
        "totalTasks": len(tasks),
        "upcoming": len(upcoming),
        "overdue": len(overdue),
        "overdueTasks": overdue,
        "upcomingTasks": upcoming[:10],
        "rating": "Excellent" if score >= 90 else "Good" if score >= 75 else "At Risk" if score >= 60 else "Critical",
    }

@app.post("/api/v1/compliance/generate-tasks")
def generate_tasks(businessId: str, legalStructure: str, state: str):
    tasks = []
    now = datetime.now()
    if legalStructure in ["private_limited", "llp"]:
        for quarter in [4, 7, 10, 1]:
            d = now.replace(month=quarter, day=15) if quarter > now.month else now.replace(year=now.year+1, month=quarter, day=15)
            tasks.append({
                "id": str(uuid.uuid4()),
                "businessId": businessId,
                "title": "TDS Payment Q" + str((quarter//3 + ((quarter%3) > 0 and 1 or 0)) or 1),
                "type": "tds",
                "dueDate": d.isoformat(),
                "status": "upcoming",
                "reminderDays": [30, 15, 7, 3],
            })
        for quarter in [4, 7, 10, 1]:
            d = now.replace(month=quarter+1, day=30) if quarter < 12 else now.replace(year=now.year+1, month=1, day=30)
            if quarter == 1: d = d.replace(month=10, year=d.year-1)
            tasks.append({
                "id": str(uuid.uuid4()),
                "businessId": businessId,
                "title": "GSTR-3B Q" + str(quarter//3),
                "type": "gstr",
                "dueDate": d.isoformat(),
                "status": "upcoming",
                "reminderDays": [20, 10, 5],
            })

    compliance_tasks[businessId] = tasks
    return {"tasksGenerated": len(tasks)}

@app.post("/api/v1/documents/upload")
async def upload_document(userId: str = Form(...), businessId: str = Form(...), file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    if ext not in APP_CONFIG["allowedFileTypes"]:
        raise HTTPException(400, f"File type {ext} not allowed. Allowed: {APP_CONFIG['allowedFileTypes']}")

    size = 0
    dest = UPLOAD_DIR / f"{file_id}{ext}"
    with open(dest, "wb") as f:
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > APP_CONFIG["uploadMaxSize"]:
                raise HTTPException(400, "File too large (max 10MB)")
            f.write(chunk)

    doc = {
        "id": file_id,
        "userId": userId,
        "businessId": businessId,
        "filename": file.filename,
        "fileUrl": f"/api/v1/documents/{file_id}{ext}",
        "fileType": ext,
        "fileSize": size,
        "category": "other",
        "tags": [],
        "createdAt": datetime.now().isoformat(),
    }
    documents[file_id] = doc
    return {"document": doc}

@app.get("/api/v1/documents/{filename}")
def get_document(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)

@app.post("/api/v1/invoices")
def create_invoice(invoice: Dict):
    inv_id = str(uuid.uuid4())
    inv = {
        "id": inv_id,
        "userId": invoice["userId"],
        "businessId": invoice["businessId"],
        "invoiceNumber": invoice.get("invoiceNumber", f"INV-{datetime.now().strftime('%Y%m%d')}-{inv_id[:6]}"),
        "clientName": invoice.get("clientName", ""),
        "amount": invoice.get("amount", 0),
        "taxAmount": invoice.get("taxAmount", 0),
        "totalAmount": invoice.get("totalAmount", invoice.get("amount", 0)),
        "date": invoice.get("date", datetime.now().isoformat()),
        "dueDate": invoice.get("dueDate", (datetime.now() + timedelta(days=30)).isoformat()),
        "status": invoice.get("status", "draft"),
        "ocrData": invoice.get("ocrData", {}),
        "createdAt": datetime.now().isoformat(),
    }

    uid = invoice["userId"]
    if uid not in invoices:
        invoices[uid] = []
    invoices[uid].append(inv)

    # Trigger anomaly detection
    user_expenses = expenses.get(uid, [])
    user_invoices = invoices.get(uid, [])
    findings = AIEngine.detect_anomalies(uid, user_expenses, user_invoices)
    if findings:
        if uid not in audit_findings:
            audit_findings[uid] = []
        audit_findings[uid].extend(findings)

    return {"invoice": inv}

@app.get("/api/v1/invoices/{user_id}")
def get_invoices(user_id: str, status: Optional[str] = None):
    user_invs = invoices.get(user_id, [])
    if status:
        user_invs = [i for i in user_invs if i["status"] == status]
    return {"invoices": user_invs, "count": len(user_invs)}

@app.post("/api/v1/expenses")
def add_expense(expense: Dict):
    exp_id = str(uuid.uuid4())
    e = {
        "id": exp_id,
        "userId": expense["userId"],
        "businessId": expense["businessId"],
        "amount": expense.get("amount", 0),
        "category": expense.get("category", "other"),
        "description": expense.get("description", ""),
        "vendorName": expense.get("vendorName"),
        "gstin": expense.get("gstin"),
        "date": expense.get("date", datetime.now().isoformat()),
        "isGstEligible": expense.get("isGstEligible", False),
        "itcClaimed": expense.get("itcClaimed", False),
        "ocrData": expense.get("ocrData", {}),
        "createdAt": datetime.now().isoformat(),
    }
    uid = expense["userId"]
    if uid not in expenses:
        expenses[uid] = []
    expenses[uid].append(e)
    return {"expense": e}

@app.get("/api/v1/expenses/{user_id}")
def get_expenses(user_id: str, category: Optional[str] = None):
    user_exp = expenses.get(user_id, [])
    if category:
        user_exp = [e for e in user_exp if e["category"] == category]
    total = sum(e["amount"] for e in user_exp)
    return {"expenses": user_exp, "total": total, "count": len(user_exp)}

@app.post("/api/v1/audit/analyze")
def audit_scan(userId: str, businessId: str):
    user_invs = invoices.get(userId, [])
    user_exp = expenses.get(userId, [])
    findings = AIEngine.detect_anomalies(userId, user_exp, user_invs)
    if userId not in audit_findings:
        audit_findings[userId] = []
    audit_findings[userId].extend(findings)

    total = len(findings)
    score = 100 - sum(15 for f in findings if f["severity"] in ["high", "critical"]) - sum(5 for f in findings if f["severity"] == "medium")
    score = max(0, min(100, score))

    return {
        "userId": userId,
        "riskScore": score,
        "riskLevel": "Low" if score >= 80 else "Medium" if score >= 60 else "High" if score >= 40 else "Critical",
        "totalFindings": total,
        "findings": findings,
        "summary": f"Found {total} issues. Risk score: {score}/100.",
    }

@app.get("/api/v1/audit/findings/{user_id}")
def get_audit_findings(user_id: str):
    return {"findings": audit_findings.get(user_id, [])}

@app.post("/api/v1/chat")
def chat_with_ai(req: ChatRequest):
    session_id = f"{req.userId}-{req.module}"
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    response = AIEngine.chat(req.userId, req.message, req.context)
    chat_sessions[session_id].append({"role": "user", "content": req.message, "timestamp": datetime.now().isoformat()})
    chat_sessions[session_id].append({"role": "assistant", "content": response["response"], "timestamp": datetime.now().isoformat()})

    return response

@app.get("/api/v1/chat/history/{user_id}")
def get_chat_history(user_id: str):
    return {"sessions": chat_sessions}

@app.get("/api/v1/regulations/india")
def get_india_regulations():
    return {"regulations": INDIA_REGULATIONS, "gstRates": GST_RATES, "complianceCalendar": COMPLIANCE_CALENDAR}

@app.get("/api/v1/dashboard/{user_id}")
def dashboard(user_id: str):
    profile = profiles.get(user_id, {})
    user_invs = invoices.get(user_id, [])
    user_exp = expenses.get(user_id, [])
    revenue = sum(i["totalAmount"] for i in user_invs)
    expenses_total = sum(e["amount"] for e in user_exp)
    pending = [i for i in user_invs if i["status"] == "pending"]
    overdue = [i for i in user_invs if i["status"] == "overdue"]
    findings = audit_findings.get(user_id, [])

    compliance_tasks_list = compliance_tasks.get(profile.get("id", ""), [])
    pf = IndianTaxEngine.calculate_new_regime_income_tax(max(0, revenue - expenses_total))

    return {
        "profile": profile,
        "financials": {
            "revenue": revenue,
            "expenses": expenses_total,
            "profit": revenue - expenses_total,
            "pendingInvoices": len(pending),
            "overdueInvoices": len(overdue),
            "totalInvoices": len(user_invs),
        },
        "taxSnapshot": {
            "estimatedTax": pf["total_tax"],
            "effectiveRate": pf["effective_rate"],
            "regime": "new",
        },
        "compliance": {
            "score": 100 - len([t for t in compliance_tasks_list if t["status"] == "overdue"]) * 15,
            "pendingTasks": len([t for t in compliance_tasks_list if t["status"] == "upcoming"]),
            "overdueTasks": len([t for t in compliance_tasks_list if t["status"] == "overdue"]),
        },
        "audit": {
            "riskLevel": "Low" if len(findings) < 3 else "Medium" if len(findings) < 7 else "High",
            "openFindings": len(findings),
        },
    }

@app.get("/api/v1/modules")
def list_modules():
    return {
        "modules": [
            {"id": "tax", "name": "Personal Tax AI", "description": "Regime optimizer, deductions finder", "status": "active"},
            {"id": "gst", "name": "GST AI", "description": "ITC reconciliation, filing prep", "status": "active"},
            {"id": "compliance", "name": "Compliance AI", "description": "Auto tracking, alerts", "status": "active"},
            {"id": "cfo", "name": "AI CFO", "description": "Cash flow forecasting", "status": "active"},
            {"id": "audit", "name": "AI Auditor", "description": "Risk scoring, findings", "status": "active"},
            {"id": "business", "name": "Business Consultant", "description": "Strategy, growth", "status": "active"},
            {"id": "fraud", "name": "Fraud Detection", "description": "Vendor, invoice, expense", "status": "active"},
            {"id": "legal", "name": "AI Legal Compliance", "description": "Contracts, licenses", "status": "active"},
            {"id": "hr", "name": "AI HR Compliance", "description": "PF, ESI, labor law", "status": "active"},
            {"id": "fundraising", "name": "AI Fundraising Advisor", "description": "Investor reports", "status": "active"},
            {"id": "health", "name": "AI Business Health", "description": "6-score health engine", "status": "active"},
            {"id": "collections", "name": "AI Collections Agent", "description": "Receivables, reminders", "status": "active"},
            {"id": "procurement", "name": "AI Procurement", "description": "Vendor optimization", "status": "active"},
            {"id": "benefits", "name": "Government Benefits", "description": "Subsidies, incentives", "status": "active"},
            {"id": "global", "name": "AI Global Expansion", "description": "Jurisdiction advisor", "status": "active"},
            {"id": "chat", "name": "AI Chat / CFO", "description": "Natural language queries", "status": "active"},
            {"id": "statements", "name": "Financial Statements", "description": "P&L, BS, CF auto-gen", "status": "active"},
        ]
    }

# === ADMIN PANEL ===
ADMIN_TOKEN=os.environ.get("ADMIN_TOKEN","change-me-admin-token")

class AdminLoginRequest(BaseModel):
    token: str

class UserUpdateRequest(BaseModel):
    userId: str
    subscription: Optional[str] = None
    activeModules: Optional[List[str]] = None
    isActive: Optional[bool] = None

class ConfigUpdateRequest(BaseModel):
    moduleAccess: Optional[Dict[str, List[str]]] = None
    globalPricing: Optional[Dict[str, Any]] = None
    maintenanceMode: Optional[bool] = None

def require_admin(auth_header: Optional[str] = None):
    token = (auth_header or "").replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Invalid admin token")
    return True

@app.post("/api/v1/admin/login")
def admin_login(req: AdminLoginRequest):
    if req.token != ADMIN_TOKEN:
        raise HTTPException(401, "Invalid admin token")
    return {"admin": True, "token": ADMIN_TOKEN}

@app.get("/api/v1/admin/users")
def admin_list_users(authorization: Optional[str] = None):
    require_admin(authorization)
    result = []
    for uid, user in users.items():
        profile = profiles.get(uid, {})
        result.append({
            "id": uid,
            "email": user.get("email"),
            "name": profile.get("name"),
            "createdAt": user.get("createdAt"),
            "subscription": profile.get("subscription", "free"),
            "isActive": profile.get("isActive", True),
            "activeModules": profile.get("activeModules", []),
        })
    return {"users": result}

@app.post("/api/v1/admin/users/update")
def admin_update_user(req: UserUpdateRequest, authorization: Optional[str] = None):
    require_admin(authorization)
    if req.userId not in profiles:
        profiles[req.userId] = {"id": req.userId}
    p = profiles[req.userId]
    if req.subscription is not None:
        p["subscription"] = req.subscription
    if req.activeModules is not None:
        p["activeModules"] = req.activeModules
    if req.isActive is not None:
        p["isActive"] = req.isActive
    return {"success": True, "profile": p}

@app.get("/api/v1/admin/stats")
def admin_stats(authorization: Optional[str] = None):
    require_admin(authorization)
    total_users = len(users)
    total_profiles = len(profiles)
    active = sum(1 for p in profiles.values() if p.get("isActive", True))
    paid = sum(1 for p in profiles.values() if p.get("subscription") in ["pro", "enterprise"])
    free = total_profiles - paid
    module_usage = {}
    for p in profiles.values():
        for m in p.get("activeModules", []):
            module_usage[m] = module_usage.get(m, 0) + 1
    return {
        "totalUsers": total_users,
        "totalProfiles": total_profiles,
        "activeUsers": active,
        "paidUsers": paid,
        "freeUsers": free,
        "moduleUsage": module_usage,
    }

@app.get("/api/v1/admin/config")
def admin_get_config(authorization: Optional[str] = None):
    require_admin(authorization)
    return {
        "modules": [
            {"id": m["id"], "name": m["name"], "enabled": True, "requiresSubscription": "free" if m["id"] in ["dashboard","tax","compliance"] else "pro"}
            for m in [
                {"id": "dashboard", "name": "Dashboard"},
                {"id": "tax", "name": "Personal Tax AI"},
                {"id": "gst", "name": "GST AI"},
                {"id": "compliance", "name": "Compliance AI"},
                {"id": "cfo", "name": "AI CFO"},
                {"id": "audit", "name": "AI Auditor"},
                {"id": "business", "name": "Business Consultant"},
                {"id": "fraud", "name": "Fraud Detection"},
                {"id": "legal", "name": "AI Legal Compliance"},
                {"id": "hr", "name": "AI HR Compliance"},
                {"id": "fundraising", "name": "AI Fundraising Advisor"},
                {"id": "health", "name": "AI Business Health"},
                {"id": "collections", "name": "AI Collections Agent"},
                {"id": "procurement", "name": "AI Procurement"},
                {"id": "benefits", "name": "Government Benefits"},
                {"id": "global", "name": "AI Global Expansion"},
                {"id": "statements", "name": "Financial Statements"},
            ]
        ],
        "subscriptionTiers": [
            {"id": "free", "name": "Free", "priceINR": 0, "priceUSD": 0, "features": ["dashboard","tax","compliance"]},
            {"id": "pro", "name": "Pro", "priceINR": 999, "priceUSD": 12, "features": ["all-except-admin"]},
            {"id": "enterprise", "name": "Enterprise", "priceINR": 2999, "priceUSD": 35, "features": ["all","admin","api"]},
        ],
        "maintenanceMode": False,
    }

@app.post("/api/v1/admin/config")
def admin_update_config(req: ConfigUpdateRequest, authorization: Optional[str] = None):
    require_admin(authorization)
    return {"success": True, "config": req.dict(exclude_none=True)}

if __name__ == "__main__":
    import uvicorn
    API_HOST = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT = int(os.environ.get("API_PORT", "8001"))
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
