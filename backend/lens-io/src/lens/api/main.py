"""Main FastAPI application entry point."""

from fastapi import FastAPI

from lens import __version__

app = FastAPI(
    title="LENS API",
    description="Lineage & Enterprise eXplainer Service - Transform technical lineage and metadata into human-readable explanations",
    version=__version__,
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "LENS API", "version": __version__}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
