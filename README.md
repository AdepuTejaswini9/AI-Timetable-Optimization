# AI-Based College Timetable Generation & Clash Optimization (GA + NSGA-II + Local Search + Incremental Re-optimization)

## 1. Introduction / 2. Problem statement
Manual timetabling is slow and clash-prone. This system generates conflict-free, multi-objective-optimised timetables for a college and repairs them incrementally when a faculty member or room becomes unavailable.

## 3. Objectives
Automatic hard-constraint-feasible timetables; Pareto alternatives over soft objectives; explainable violations; role-based workflow (Admin, HOD, Faculty, Student); approval + publication; PDF/Excel export.

## 4. Existing system / 5. Proposed system
Existing: manual or spreadsheet scheduling, full regeneration on any change. Proposed: hybrid GA/NSGA-II/Local Search engine with versioned timetables and minimal-change repair.

## 6. Technologies
React + Vite + Tailwind + Axios + React Router + Recharts · FastAPI + SQLAlchemy + Pydantic + JWT + bcrypt · MySQL · NumPy + pymoo · Pandas/OpenPyXL/ReportLab · pytest.

## 7–8. Architecture & folders
See `docs/architecture.md`. `frontend/` `backend/app/{routes,models,schemas,authentication,algorithms,services,utils,database}` `database/` `tests/` `docs/`.

## 9. Database setup (MySQL 8)
```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql        # dev seed data
mysql -u root -p -e "CREATE USER 'timetable'@'localhost' IDENTIFIED BY 'timetable_pw'; GRANT ALL ON timetable_db.* TO 'timetable'@'localhost';"
```
(Alternatively let the app create tables: `cd backend && python -m app.utils.init_db --seed`.)

## 10. Backend
```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL and a long random SECRET_KEY
uvicorn app.main:app --reload --port 8000     # docs at http://localhost:8000/docs
```
## 11. Frontend
```bash
cd frontend && npm install && npm run dev      # http://localhost:5173  (VITE_API_URL in .env if backend differs)
```
## 12. Quick start without MySQL (dev only)
`DATABASE_URL=sqlite:///./dev.db python -m app.utils.init_db --seed` then run uvicorn with the same variable.

## 13. Demo logins (DEVELOPMENT ONLY – change/remove before any real use)
| Role | Email | Password |
|---|---|---|
| Admin | admin@college.edu | Admin@123 |
| HOD (CSE) | hod.cse@college.edu | Hod@123 |
| HOD (ECE) | hod.ece@college.edu | Hod@123 |
| Faculty | faculty1@college.edu … faculty10@college.edu | Faculty@123 |
| Student | student1@college.edu … student6@college.edu | Student@123 |

Seed: 2 departments, 2 HODs, 10 faculty, 10 subjects (2 labs), 5 classrooms + 2 labs, 3 sections, 6 students.
**Typical flow**: Admin → *Generate* (NSGA-II + LS) → *Compare & Pareto* → select a solution → *Approvals & Publish* → submit → HODs approve → Publish → Faculty/Students view. Then *Re-optimization* to simulate a faculty/room outage.

## 14. Algorithms
See `docs/algorithm_explanation.md`.

## 15. API (interactive docs at `/docs`)
`POST /auth/login`, `GET /auth/me` · CRUD `/departments /subjects /rooms /sections /faculty /students /hods /assignments` · `GET/PUT /faculty/{id}/availability` · `GET/PUT /config/timeslots`, `/settings` · `POST /timetable/generate`, `GET /timetable`, `GET|PUT /timetable/{id}`, `GET /timetable/{id}/conflicts`, `POST /timetable/{id}/publish|clone` · `POST /optimization/generate`, `GET /optimization/{id}/status|solutions`, `POST /optimization/{id}/select` · `POST /reoptimization/request`, `GET /reoptimization/{id}/status` · `POST /approvals/submit`, `/approvals/{id}/approve|reject` · `GET /export/timetable/{id}/pdf|excel` · leave/change requests, notifications, dashboard.

## 16. Screenshots
Not included (none were captured in the build environment). Add your own under `docs/screenshots/`.

## 17. Tests
```bash
pip install -r backend/requirements.txt
pytest            # from repo root; uses a temporary SQLite DB, never MySQL
```
## 18. Known limitations
- **MySQL was not available in the build environment**: `schema.sql`/`seed.sql` (generated from the models) and the MySQL driver path are untested; all tests and the live smoke test ran on SQLite.
- Optimisation runs in FastAPI background tasks (single process, no queue/cancel).
- Faculty–subject qualification is not modelled (substitute suggestions are same-department only).
- Hard constraints are fixed (not user-toggleable); only soft weights and the period grid are configurable.
- One college-wide timetable per version; elective/combined classes and multi-section lab batches are not modelled.
- JWT stored in localStorage (XSS trade-off); no refresh tokens / rate limiting. No screenshots; frontend has no automated UI tests.
- Soft-objective scales differ, so GA weights need tuning for real data.
