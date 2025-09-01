from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, csv as csv_router, dashboard
from app.database import engine
from app import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="DashAgent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(csv_router.router, tags=["csv"])
app.include_router(dashboard.router, tags=["dashboard"])


@app.get("/")
def read_root():
    return {"message": "DashAgent API is running!"}