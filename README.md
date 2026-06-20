# TAXOS AI — AI Financial OS for India

[![Vercel](https://vercelbadge.vercel.app/api/prabhatbiswas201186/taxos-ai)](https://taxos-ai.vercel.app)

**Live:** https://taxos-ai.vercel.app  
**GitHub:** https://github.com/prabhatbiswas201186/taxos-ai

---

## Stack
- Frontend: Vanilla SPA, Chart.js, Three.js, Tailwind CDN
- Backend: FastAPI + Python
- Database: Supabase PostgreSQL (ready to connect)
- AI: Google Gemini (free tier) + local engines
- Deploy: Vercel (frontend) + Railway (backend)
- PWA: Installable on desktop + mobile

## Modules (17)
Tax AI, GST AI, Compliance AI, AI CFO, AI Auditor, Business Consultant, Fraud Detection, Legal AI, HR Compliance, Fundraising Advisor, Business Health Engine, Collections Agent, Procurement Manager, Government Benefits, Global Expansion, AI Chat / CFO, Financial Statements

## Local Dev
```bash
# backend
cd backend
pip install -r requirements.txt
python src/main.py

# frontend (open directly)
open index.html
```

## Deploy
```
scripts\deploy.bat
```

## API Docs
FastAPI OpenAPI: `/docs` (when backend running)
