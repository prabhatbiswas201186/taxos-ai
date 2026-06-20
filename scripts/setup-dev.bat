@echo off
echo Setting up TAXOS AI dev environment...
python -m venv .venv
call .venv\Scripts\activate
pip install -r backend\requirements.txt
echo Done. Run: python backend\src\main.py
