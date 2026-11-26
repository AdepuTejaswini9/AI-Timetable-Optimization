#!/usr/bin/env bash
# One-shot dev setup (Linux/macOS). Requires Python 3.10+, Node 18+, MySQL 8 running.
set -e
python3 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
[ -f backend/.env ] || cp backend/.env.example backend/.env
(cd frontend && npm install && cp -n .env.example .env || true)
echo "Edit backend/.env (DATABASE_URL, SECRET_KEY), load database/schema.sql + database/seed.sql, then:"
echo "  cd backend && uvicorn app.main:app --reload      and      cd frontend && npm run dev"
