# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import csv as csv_router, dashboard, analytics

from app.db.database import Base, engine
from app.config.settings import settings
from app.routers.auth_routes import router as auth_router
from app.routers.user_routes import router as user_router
from app.routers.profile_routes import router as profile_router
from app.routers.session_routes import router as session_router
from app.routers.agent_routes import router as agent_router
from app.utils.response import setup_exception_handlers

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="DashAgent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://194.233.69.219:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(csv_router.router, tags=["csv"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(analytics.router, tags=["analytics"])
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(profile_router)
app.include_router(session_router)
app.include_router(agent_router)

setup_exception_handlers(app)

@app.get("/")
def read_root():
    return {"message": "DashAgent API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
