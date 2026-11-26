# Architecture
React (Vite, Tailwind, Recharts, Axios) → REST/JSON + JWT → FastAPI → SQLAlchemy → MySQL.
The optimisation engine (`backend/app/algorithms`) is pure Python/NumPy/pymoo and is independent of the web layer:
`data_loader.build_problem()` turns DB rows into a `Problem`; `optimization_service` runs jobs (FastAPI BackgroundTasks) and stores results.
Authorization is enforced server-side in `authentication/security.py` (roles) and `services/access.py` (HOD department scope, faculty/student row scope).
Workflow: generate → select solution (draft version) → submit (per-department approval records) → HOD approve/reject → admin publish (re-validated; hard violations block publication) → incremental repair creates a new draft version and never touches the published one.
