# LENS – Lineage & Enterprise eXplainer Service

LENS is an open-source service that turns **technical lineage and metadata** into **clear, human-readable explanations**.

It sits on top of your existing **data catalog** and **lineage platform** and provides simple APIs to answer questions like:

- "How is this report produced end-to-end?"
- "What systems and datasets feed this table?"
- "What breaks if we change or deprecate this object?"

> LENS is currently in early development and not yet production-ready.

## Repository Structure

This is a **mono-repo** containing backend and frontend components:

- **`backend/lens-io/`** - Unified Python package
  - Install: `pip install lens`
  - Library usage: `from lens.lineage import LineageRepository`
  - API service: `uvicorn lens.api.main:app`
  - Contains core functionality (models, business logic, database) and API service

- **`frontend/`** (planned) - Next.js React application

The package uses dynamic versioning with git tags (e.g., `v1.0.0`).

### Features (Planned)

- **Lineage Explainer**
  - Summarize upstream lineage for a given asset (report, table, view, dataset).
  - Highlight key systems, hops, and domains in plain language.

- **Impact Analysis**
  - List and explain downstream impacts of changing or removing an asset.
  - Surface "critical" downstream objects (e.g., tagged as regulatory, financial, or tier-1).

- **Metadata-First Design**
  - Works only with **metadata** (schemas, lineage, catalog entries) – not raw data.
  - Integrates with your existing catalog / lineage tools via adapters.

- **LLM-Orchestrated Narratives**
  - Uses large language models (LLMs) to turn graph-shaped metadata into structured text:
    - Executive summary
    - Technical summary
    - Upstream / downstream highlights

### High-Level Architecture (Conceptual)

LENS is designed around three main components:

1. **Metadata Integration Layer**
   - Connectors to:
     - Lineage store (graph DB or vendor API)
     - Data catalog / business glossary
     - Optional report registry
   - Normalizes metadata into a simple graph model that LENS can reason over.

2. **LENS Service API**
   - Stateless service exposing endpoints such as:
     - `GET /explanations/lineage?asset_id=...`
     - `GET /explanations/impact?asset_id=...`
   - Orchestrates metadata retrieval, graph summarization, and LLM calls.

3. **Client Integrations**
   - Buttons / panels in your existing catalog or lineage UI (e.g., "Explain Lineage").
   - Optional CLI or simple web UI for experimentation.

### Status

LENS is in an **early, exploratory phase**. The current goals are to:

- Solidify the **core data model** for lineage and impact.
- Provide a minimal **reference implementation** of the LENS API.
- Add **example adapters** for common catalog/lineage tools (where licenses allow).

Breaking changes to APIs and data structures are expected while the project stabilizes.

### Getting Started

Documentation and code are still being organized. At a high level, the project will expose:

- A core Python/TypeScript library for:
  - Loading lineage graphs
  - Converting them into LENS’s internal model
- A reference LENS service (e.g., FastAPI/Express-based) you can deploy in your environment.

Planned steps (subject to change):

1. Clone the repository:

   ```bash
   git clone https://github.com/millsks/project-lens.git
   cd project-lens
   ```

2. Set up a virtual environment / dependencies.
3. Configure a simple metadata source (e.g., local JSON lineage sample).
4. Start the LENS service in local/dev mode.
5. Call the sample endpoints using `curl` or a REST client.

Full installation and configuration instructions will be added as the project matures.

### Contributing

Contributions are welcome once the initial structure is in place.

In the meantime, you can help by:

- Opening issues to discuss:
  - Use cases
  - Data models
  - Integration scenarios
- Sharing feedback on:
  - API shape
  - Output formats
  - Guardrails and governance needs

A `CONTRIBUTING.md` guide and code of conduct will be added as the project evolves.

### License

LENS is licensed under the **Apache License, Version 2.0**.

See the [`LICENSE`](LICENSE) file for details.
