"""Cherry Evals FastAPI application."""

from fastapi import FastAPI

from api.routes import health

app = FastAPI(
    title="Cherry Evals",
    description="Curated evaluation dataset search and export platform",
    version="0.1.0",
)

# Register routes
app.include_router(health.router, tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Cherry Evals API"}
