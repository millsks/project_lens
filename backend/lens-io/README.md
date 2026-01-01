# LENS – Lineage & Enterprise eXplainer Service

LENS is a unified Python package that transforms technical lineage and metadata into human-readable explanations.

## Installation

```bash
pip install lens
```

## Usage

### As a Library

```python
from lens.lineage import LineageRepository
from lens.lineage.models import LineageNode, NodeType

# Use the lineage repository to query lineage graphs
# (Requires database connection configured via environment)
```

### As a Service

```bash
# Run the FastAPI application
uvicorn lens.api.main:app --reload

# Or use the convenient package reference
uvicorn lens.api:app --reload
```

The API will be available at `http://localhost:8000` with automatic documentation at `/docs`.

## Package Structure

- **`lens.lineage`** - Core lineage models, schemas, and repository
- **`lens.db`** - Database session management
- **`lens.api`** - FastAPI application and HTTP endpoints

## Development

See the main [project README](../../README.md) for development setup and contribution guidelines.

## License

Apache License, Version 2.0 - See [LICENSE](../../LICENSE) file for details.
