# GitHub Copilot Instructions

This file provides guidance to GitHub Copilot when working with code in this repository.

## Project Overview

LENS (Lineage & Enterprise eXplainer Service) is an open-source service that transforms technical lineage and metadata into human-readable explanations. It sits on top of existing data catalogs and lineage platforms, providing APIs to answer questions about data lineage, system dependencies, and impact analysis.

**Status**: Early exploratory phase. Expect breaking changes to APIs and data structures.

## Repository Structure

This is a **mono-repo** containing backend and frontend components:

- **`backend/lens-io/`**: Unified Python package combining core functionality and API service
  - PyPI: `lens`
  - Import: `from lens import ...` (library) or `from lens.api import ...` (API)
  - Git tags: `v*` (e.g., `v1.0.0`)
  - Contains:
    - `lens.lineage` - Lineage models, schemas, and repository
    - `lens.db` - Database session management
    - `lens.api` - FastAPI application layer

- **`frontend/`** (future): Next.js React application

The package uses dynamic versioning with git tags and hatch-vcs.

## Core Concepts

LENS is designed around three main layers:

1. **Metadata Integration Layer**
   - Connectors to lineage stores (graph DB or vendor API), data catalogs, and optional report registries
   - Normalizes metadata into a simple graph model for reasoning

2. **LENS Service API**
   - Stateless service exposing endpoints like:
     - `GET /explanations/lineage?asset_id=...`
     - `GET /explanations/impact?asset_id=...`
   - Orchestrates metadata retrieval, graph summarization, and LLM calls

3. **Client Integrations**
   - UI buttons/panels in existing catalog or lineage tools
   - Optional CLI or web UI for experimentation

## Technology Stack

- **Python**: 3.12
- **Package Manager**: pixi (conda-based environment and task management)
- **Build System**: hatch with hatch-vcs for dynamic versioning from git tags
- **Web Framework**: FastAPI with uvicorn server
- **Data Validation**: Pydantic v2
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0 ORM and Alembic for migrations
- **Task Queue**: Celery with Flower for monitoring
- **Message Broker & Cache**: Redis 7 (for Celery broker and caching)
- **Development Tools**:
  - Linting & Formatting: ruff (>=0.8.0)
  - Type Checking: pyright (>=1.1.0) with strict mode
  - Testing: pytest (>=8.0.0) with pytest-cov, pytest-asyncio
  - Changelog: git-cliff (>=2.11.0) for conventional commit changelog generation
- **Containerization**: Docker Compose for local development services
- **LLM Integration**: TBD - will use LLMs to generate narratives from graph-shaped metadata

## Key Design Principles

- **Metadata-First**: Works only with metadata, never touches raw data
- **Adapter Pattern**: Integrates with existing tools via connectors/adapters
- **Stateless Service**: API designed to be stateless for easy scaling
- **Narrative Generation**: Converts technical graphs into structured text (executive summary, technical summary, upstream/downstream highlights)

## Setup and Installation

### Prerequisites

- [pixi](https://pixi.sh) package manager installed (v0.20.0 or later recommended)
- [Docker](https://www.docker.com/) and Docker Compose (for local PostgreSQL and Redis)
- Git (for version control and hatch-vcs version generation)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/millsks/project-lens.git
cd project-lens

# Install all dependencies (creates .pixi environment)
pixi install

# Copy environment variables template and configure as needed
cp .env.example .env
# Edit .env if you need custom database credentials or ports

# Start PostgreSQL and Redis using Docker Compose
pixi run docker-up

# Verify services are running
pixi run docker-ps

# Run initial tests to verify setup
pixi run -e dev test
```

**Important Notes**:

- Most development commands (lint, format, typecheck, test, build) require the `dev` environment
- Use `pixi run -e dev <command>` or activate the dev shell with `pixi shell -e dev`
- The main application can be run in the default environment with `pixi run dev`
- Version number is dynamically generated from git tags using hatch-vcs

## Docker Services

The project uses Docker Compose to manage PostgreSQL and Redis for local development.

### Docker Compose Commands

```bash
# Start all services (PostgreSQL + Redis) in detached mode
pixi run docker-up

# Stop all services
pixi run docker-down

# View logs from all services
pixi run docker-logs

# Check status of services
pixi run docker-ps

# Restart all services
pixi run docker-restart

# Stop services and remove volumes (⚠️ deletes all data)
pixi run docker-clean
```

### Service Details

**PostgreSQL**:

- Image: `postgres:16-alpine`
- Default Port: `5432`
- Default Credentials: `lens` / `lens_dev_password`
- Database: `lens`
- Data persisted in Docker volume `postgres_data`

**Redis**:

- Image: `redis:7-alpine`
- Default Port: `6379`
- Default Password: `lens_dev_password`
- Data persisted in Docker volume `redis_data`

**Environment Configuration**:

- Copy `.env.example` to `.env` and customize as needed
- All connection strings and credentials are configurable via `.env`

## Common Commands

### Development Server

```bash
# Run FastAPI development server with auto-reload
pixi run dev
```

### Code Quality

```bash
# Format code
pixi run -e dev format

# Check linting
pixi run -e dev lint

# Type checking
pixi run -e dev typecheck
```

### Testing

```bash
# Run all tests
pixi run -e test test

# Run tests with coverage
pixi run -e test test-cov
```

### Building

```bash
# Build the lens package
pixi run -e dev build

# Output will be in backend/lens-io/dist/
# Note: Version is determined from git tags via hatch-vcs
#       Tags should match: v* (e.g., v1.0.0)
```

### Changelog Management

```bash
# Generate full changelog and write to CHANGELOG.md
pixi run -e dev changelog

# Preview unreleased changes
pixi run -e dev changelog-unreleased

# View latest release notes
pixi run -e dev changelog-latest

# Preview next release (with version bump)
pixi run -e dev release-preview
```

**Commit Message Convention**: This project uses [Conventional Commits](https://www.conventionalcommits.org/) with the following types:

- `feat:` - New features (⭐ Features)
- `fix:` - Bug fixes (🐛 Bug Fixes)
- `docs:` - Documentation changes (📚 Documentation)
- `perf:` - Performance improvements (⚡ Performance)
- `refactor:` - Code refactoring (🚜 Refactor)
- `style:` - Code style/formatting (🎨 Styling)

## Code Style and Standards

### Python Style

- Follow PEP 8 with 100 character line length
- Use type hints consistently (pyright strict mode)
- Prefer pathlib over os.path
- Use async/await for I/O operations
- Format with ruff: `pixi run -e dev format`

### Testing

- Write tests for all new features
- Use pytest fixtures for common setup
- Async tests use pytest-asyncio
- Target meaningful coverage, not just high percentages
- Run tests: `pixi run -e dev test`

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation only
- `perf:` - Performance improvements
- `refactor:` - Code refactoring
- `style:` - Formatting, missing semicolons, etc.
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

Format: `type(optional-scope): description`

Example: `feat(api): add lineage explanation endpoint`

## Project Structure

```text
project-lens/
├── backend/
│   ├── lens/              # Unified Python package
│   │   ├── pyproject.toml # Package config with hatch-vcs (root = "../..")
│   │   ├── src/lens/      # Python module
│   │   │   ├── __init__.py
│   │   │   ├── _version.py    # Auto-generated (git-ignored)
│   │   │   ├── lineage/   # Lineage models, schemas, repository
│   │   │   ├── db/        # Database session management
│   │   │   └── api/       # FastAPI application
│   │   │       ├── __init__.py
│   │   │       └── main.py
│   │   ├── alembic/       # Database migrations
│   │   ├── scripts/       # Utility scripts (e.g., seed data)
│   │   ├── tests/         # Package tests
│   │   │   └── test_main.py
│   │   └── README.md      # Package documentation
│   └── README.md          # Backend overview
├── frontend/              # (Future) Next.js application
├── pixi.toml              # Workspace-level config and tasks
├── pixi.lock              # Lock file for reproducible environments
├── docker-compose.yml     # Shared services (PostgreSQL, Redis)
├── .env.example           # Environment variables template
└── README.md              # Project documentation
```

## Configuration Files

- **pixi.toml**: Pixi environment, dependency management, and task definitions
  - Defines both default and `dev` environments
  - Includes tasks for development, testing, Docker management, and changelog generation
  - Multi-platform support: osx-arm64, linux-64, osx-64, win-64
- **pyproject.toml**: Python project metadata and tool configurations
  - Build system: hatch with hatch-vcs for git-based versioning
  - Tool configs: ruff (lint/format), pyright (typecheck), pytest, coverage, git-cliff
  - Project metadata: dependencies, URLs, classifiers
- **pixi.lock**: Auto-generated lock file for reproducible builds (commit to version control)
  - Marked as binary in .gitattributes to prevent merge conflicts
- **docker-compose.yml**: Local development services (PostgreSQL 16, Redis 7)
  - Includes health checks and persistent volumes
  - Configurable via environment variables
- **.env.example**: Template for environment variables (commit to version control)
- **.env**: Local environment configuration (git-ignored, copy from .env.example)
- **.gitattributes**: Git attributes configuration (pixi.lock handling)
- **.python-version**: Python version specification for tools like pyenv

### Database Migrations (Alembic)

```bash
# Show current migration status
pixi run alembic current
```

### Celery Tasks

```bash
# Start Celery worker
pixi run celery -A lens.tasks worker --loglevel=info

# Start Flower monitoring UI
pixi run celery -A lens.tasks flower
```

## Environment Setup

1. Install dependencies: `pixi install`
2. Copy environment config: `cp .env.example .env`
3. Start Docker services: `pixi run docker-up`
4. Run tests: `pixi run -e dev test`

**Note**: Most dev commands require the `dev` environment. Use `pixi run -e dev <command>` or activate the shell with `pixi shell -e dev`.

## Development Workflow

1. Create feature branch: `git checkout -b feat/your-feature`
2. Make changes following existing patterns
3. Run quality checks: format, lint, typecheck, test
4. Commit with conventional message
5. Push and create pull request

## Current Development Phase

**Completed**:

- ✅ Project structure and build configuration
- ✅ Development environment setup
- ✅ Docker services (PostgreSQL, Redis)
- ✅ Basic FastAPI application with health endpoints
- ✅ Testing framework
- ✅ Code quality tools
- ✅ Conventional commits and changelog automation

**Next Steps**:

1. Define core data models for lineage graphs
2. Implement database schema with Alembic migrations
3. Create metadata adapter interfaces
4. Develop API endpoints for lineage queries
5. Add LLM integration for narrative generation
6. Build example adapters for common tools

## Important Notes

- Version is dynamically generated from git tags (hatch-vcs)
- pixi.lock is marked as binary in .gitattributes
- Database credentials in .env.example are for development only
- LLM integration details are TBD
- Celery tasks are not yet implemented

## License

Apache-2.0
