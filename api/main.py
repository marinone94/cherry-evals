"""Cherry Evals FastAPI application."""

from fastapi import FastAPI

from api.routes import analytics, collections, datasets, examples, export, health, search

app = FastAPI(
    title="Cherry Evals",
    description="Search, cherry-pick, and export examples from public AI evaluation datasets.",
    version="0.1.0",
)

# Register routes
app.include_router(health.router, tags=["health"])
app.include_router(datasets.router)
app.include_router(examples.router)
app.include_router(search.router)
app.include_router(collections.router)
app.include_router(export.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Cherry Evals API"}
