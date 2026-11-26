from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app import config
from app.routes import auth, academic, timetable, optimization, workflow, export

app = FastAPI(title="AI Timetable Optimization", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, academic.router, timetable.router, optimization.router, workflow.router, export.router):
    app.include_router(r)

@app.exception_handler(Exception)
async def unhandled(_, exc):  # never leak internals
    return JSONResponse({"detail": "Internal server error"}, status_code=500)

@app.get("/health")
def health(): return {"status": "ok"}
