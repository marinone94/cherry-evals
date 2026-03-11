"""Cherry Evals FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    account,
    agents,
    analytics,
    api_keys,
    billing,
    collections,
    datasets,
    examples,
    export,
    health,
    search,
)
from cherry_evals.config import settings

app = FastAPI(
    title="Cherry Evals",
    description="Search, cherry-pick, and export examples from public AI evaluation datasets.",
    version="0.1.0",
)

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "X-Api-Key", "X-Session-Id", "Content-Type"],
)

# Register routes
app.include_router(health.router, tags=["health"])
app.include_router(datasets.router)
app.include_router(examples.router)
app.include_router(search.router)
app.include_router(collections.router)
app.include_router(export.router)
app.include_router(analytics.router)
app.include_router(agents.router)
app.include_router(billing.router)
app.include_router(api_keys.router)
app.include_router(account.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Cherry Evals API"}
