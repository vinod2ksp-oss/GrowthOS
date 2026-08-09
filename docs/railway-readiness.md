# Railway Readiness

This document is a compatibility guide only. Creating Railway services is a separate release operation.

## Backend service

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Pre-deploy command: `python -m alembic upgrade head`
- Start command: the checked-in `Procfile` uses `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Persistent volume: mount a volume and set `STORAGE_PATH` to its mount path. Uploaded files must not rely on Railway's ephemeral filesystem.

Required variables: `APP_ENV=production`, `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`, `CORS_ORIGINS`, and `STORAGE_PATH`. Set `MAX_UPLOAD_SIZE` as needed. AI remains optional; configure `AI_ENABLED`, `AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`, `AI_TIMEOUT_SECONDS`, and `AI_MAX_RETRIES` only when enabled.

The application does not call `Base.metadata.create_all()` or run Alembic at startup. Migration is an explicit pre-deploy step.

## Frontend service

- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Start command: `npm run start`; Next.js reads Railway's `PORT` variable.
- Required build variable: `NEXT_PUBLIC_API_URL=https://<backend-domain>/api/v1`

`NEXT_PUBLIC_API_URL` is embedded during the production build, so changing it requires a frontend rebuild. The localhost API fallback is development-only.
