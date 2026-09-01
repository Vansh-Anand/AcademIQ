from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, experiments, pipeline, evidence, status

app = FastAPI(
    title="AcademIQ Dashboard API",
    description="Backend API for AcademIQ Dashboard",
    version="1.0.0"
)

# Configure CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(status.router, prefix="/api/system/status", tags=["system-status"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])

@app.get("/")
def read_root():
    return {"message": "Welcome to AcademIQ Dashboard API"}
