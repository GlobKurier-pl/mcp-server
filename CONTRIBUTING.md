# Developer Guide

This project is an educational playground for learning modern architecture patterns: Hexagonal Architecture, Clean Architecture, CQRS and DDD. For a deep dive into the architecture see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone <repository-url>
cd globkurier-api-mcp

uv sync

cp .env.example .env
```

## Running

```bash
python -m globkurier_mcp.main
# or
globkurier-mcp
```

Server starts at `http://127.0.0.1:9000` by default.

## Configuration

Edit `.env`:

```bash
# GlobKurier API
GLOBKURIER_API_BASE_URL=https://api.globkurier.pl
GLOBKURIER_DEFAULT_LANGUAGE=pl

# MCP Server
MCP_HOST=127.0.0.1
MCP_PORT=9000
MCP_TRANSPORT=http

# HTTP Client
HTTP_TIMEOUT=10.0
```

## Testing

```bash
# All tests
pytest

# With coverage
pytest --cov=globkurier_mcp

# Type checking
mypy globkurier_mcp

# Linting
ruff check globkurier_mcp

# Auto-fix lint issues
ruff check globkurier_mcp --fix
```

## Architecture Overview

```
globkurier_mcp/
├── core/           # Domain layer — business logic, ports (interfaces)
├── application/    # Use cases — queries, commands, DTOs, QueryBus
├── infrastructure/ # Adapters — HTTP client, MCP server
└── main.py         # Dependency injection root
```

Dependency rule: `infrastructure` → `application` → `core`. The `core` layer never imports from outer layers.

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed diagrams and data flow.

## Adding a New Query (read operation)

1. **Define the Query and Handler** in `application/queries/`:

```python
from dataclasses import dataclass
from globkurier_mcp.core.shipping.ports import ShipmentTrackingPort

@dataclass(frozen=True)
class MyNewQuery:
    param: str

class MyNewQueryHandler:
    def __init__(self, port: ShipmentTrackingPort):
        self._port = port

    async def handle(self, query: MyNewQuery):
        # call port, map domain model → DTO
        pass
```

2. **Register in QueryBus** (`application/bus/dispatcher.py`)

3. **Add an MCP tool** (`infrastructure/mcp/server.py`)

4. **Wire in `main.py`** — instantiate the handler and pass to `create_query_bus()`

## Adding a New Adapter

1. Define a Port (interface) in `core/<context>/ports.py`
2. Implement it in `infrastructure/`
3. Inject it in `main.py`

## Development Rules

- **Never bypass layers** — MCP tools must use QueryBus, not call adapters directly
- **Never expose domain models** — always map to DTOs before leaving the application layer
- **No upward imports** — `core/` cannot import from `application/` or `infrastructure/`
- **Value objects are immutable** — they are frozen dataclasses
- **Business logic belongs in the domain** — not in handlers or adapters