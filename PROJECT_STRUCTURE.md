# Project Structure

This document maps the main folders and files in the repo.


## Frontend (Next.js App Router)

- `app/` — Main frontend folder
  - `globals.css`, `maritime.css`, `maritime-effects.css` — global and maritime styles
  - `layout.tsx` — App layout
  - `page.tsx` — Landing page
  - `chat/page.tsx` — AI chat assistant
  - `documents/page.tsx` — Document upload & viewer
  - `weather/page.tsx` — Weather dashboard & forecasts
  - `recommendations/page.tsx` — Smart recommendations & routing
  - `ports/page.tsx` — Ports listing & details
  - `settings/page.tsx` — User/system settings
  - `api/` — Next.js API routes (e.g. `process-document`)

- `components/` — React UI components
  - `sof-viewer.tsx` — SOF event viewer/editor
  - `weather-*` — Weather widgets
  - `port-*` — Port list/card/detail components
  - ...other shared UI components

- `lib/` — Shared frontend libraries/utilities
- `hooks/` — Custom React hooks
- `public/` — Static assets (images, icons, etc.)
- `styles/` — Global and modular stylesheets
- `types/` — Shared TypeScript types/interfaces

## Backend (FastAPI)

- `backend/` — Main backend folder
  - `main.py` — FastAPI entry point/services
  - `sof_processor.py` — SOF parser & laytime analysis
  - `services.py` — Azure/external integrations
  - `database.py` — SQLAlchemy models (documents, chat, weather, recommendations, APISettings)
  - `config.py` — Environment/config management
  - `requirements.txt` — Python dependencies
  - `alembic.ini` — Alembic migration config
  - `ports.db` — Sample SQLite DB
  - `setup_postgres.py` — PostgreSQL setup script
  - `migrate_to_postgres.sh`/`.bat` — DB migration scripts
  - `query/` — SQL queries/scripts
  - `test_*.py` — Backend/unit/integration tests

## Database & Migrations

- PostgreSQL (production), SQLite (dev)
- Alembic for migrations (`alembic.ini`, migration scripts)
- `setup_postgres.py`, `migrate_to_postgres.sh`/`.bat` — DB/user creation & migration

## AI Providers

- Groq (preferred), OpenRouter, OpenAI, HuggingFace
- Automatic selection via `.env`/`backend/.env` (`GROQ_API_KEY` preferred)

## CI/CD & GitHub

- `.github/workflows/ci.yml` — GitHub Actions workflow
- `.gitignore` — Ignore files for Git
- `CODEOWNERS` — Repo ownership

## Documentation

- `README.md` — Project overview & setup
- `PROJECT_STRUCTURE.md` — This file (repo map)
- `AUTHENTICATION_GUIDE.md`, `API_SETUP_GUIDE.md`, `MAPLIBRE_PROFESSIONAL_SETUP.md`, etc. — Feature guides

## Developer Notes

- Configs: `.env` (root/backend), see `backend/.env.template`
- Run backend: `uvicorn main:app --reload --port 8000`
- Run frontend: `npm run dev`
- DB: PostgreSQL for production, SQLite for dev/testing
- All major flows (frontend, backend, AI, DB, CI) are mapped above
