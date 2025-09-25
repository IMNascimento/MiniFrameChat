#!/usr/bin/env bash
cd backend && source .venv/bin/activate 2>/dev/null || true; uvicorn app.main:app --host 127.0.0.1 --port 8899 --reload --env-file ./.env
