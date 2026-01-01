# LENS Backend

This directory contains the Python package for LENS (Lineage & Enterprise eXplainer Service).

## Package

### lens

Unified Python package providing both library functionality and API service:

**Core Components:**
- `lens.lineage` - Data models (Pydantic, SQLAlchemy), schemas, and repository for lineage graph
- `lens.db` - Database session management and configuration
- `lens.api` - FastAPI application with HTTP endpoints

**Additional:**
- Database migrations (Alembic)
- Utility scripts (seed data, etc.)
- Celery tasks for async processing (future)

**Location**: `backend/lens-io/`
**PyPI**: `lens`
**Import**: `from lens import ...` or `from lens.lineage import ...`

## Versioning

The package uses dynamic versioning with git tags:

- Tags should match `v*` (e.g., `v1.0.0`)
- Versions are automatically generated from git tags using hatch-vcs

## Development

For development setup and contribution guidelines, see the main [README.md](../README.md) in the repository root.

## Where to Add Code

- **`lens.lineage`** - Lineage models, schemas, graph algorithms, repository
- **`lens.db`** - Database session management, connection pooling
- **`lens.api`** - FastAPI routes, endpoints, middleware, authentication
- **`lens/alembic`** - Database migration files
- **`lens/scripts`** - Utility scripts for data seeding, maintenance, etc.

## License

Apache License, Version 2.0 - See LICENSE file in the repository root for details.
