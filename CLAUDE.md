# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for GlobKurier API built as an educational playground for learning modern architecture patterns. The project implements Hexagonal Architecture, Clean Architecture, CQRS, and Domain-Driven Design principles.

## Build & Development Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
python -m globkurier_mcp.main

# Run all tests
pytest

# Run tests with coverage
pytest --cov=globkurier_mcp

# Run specific test file
pytest tests/test_domain_models.py -v

# Run single test
pytest tests/test_domain_models.py::test_shipment_id_value_object -v

# Type checking
mypy globkurier_mcp

# Linting
ruff check globkurier_mcp

# Auto-fix linting issues
ruff check globkurier_mcp --fix
```

## Architecture: Hexagonal with CQRS

This codebase uses strict layered architecture with dependency inversion. Understanding the flow is critical:

### Layer Dependencies (ALWAYS enforce these rules)
```
core (Domain)          ← Does NOT depend on anything
    ↑
application (Use Cases) ← Depends ONLY on core
    ↑
infrastructure (Adapters) ← Depends on core + application
```

**Critical Rule**: `core/` NEVER imports from `application/` or `infrastructure/`. If you see such an import, it's a bug.

### Request Flow (example: get_shipment_status)

```
MCP Tool (infrastructure/mcp/tools/)
  → Creates Query object (frozen dataclass)
    → QueryBus.execute() (application/bus/)
      → Routes to QueryHandler (application/queries/)
        → Calls Port interface (core/.../ports.py) - Abstract method
          [Dependency Inversion happens here]
          → Implemented by Adapter (infrastructure/http/)
            → Makes HTTP request to external API
          ← Returns Domain Model (core/.../models.py)
        ← Handler maps Domain Model → DTO (application/dto/)
      ← Returns DTO
    ← Tool serializes DTO to dict
  ← MCP returns JSON
```

### Key Components

**Ports (core/.../ports.py)**: Abstract interfaces that define what the domain needs from external systems. These are implemented by infrastructure adapters.

**Adapters (infrastructure/)**: Concrete implementations of ports. Example: `GlobKurierHttpClient` implements `ShipmentTrackingPort`.

**DTOs (application/dto/)**: Data Transfer Objects for serialization. Domain models are NEVER exposed outside application layer.

**QueryBus (application/bus/)**: Routes queries to handlers. In `main.py`, handlers are registered to the bus during dependency injection.

**Value Objects**: Immutable (frozen dataclass) domain primitives like `ShipmentId`, `TrackingEvent`.

**Aggregate Roots**: Main domain entities like `ShipmentStatus` that contain business logic.

## Dependency Injection Pattern

All wiring happens in `main.py`:

1. Load configuration (`get_settings()`)
2. Create infrastructure adapters (implements ports)
3. Inject ports into application handlers
4. Register handlers in QueryBus
5. Pass QueryBus to MCP server
6. Run server

When adding new features, follow this same pattern in `main.py`.

## Adding New Features

### New Query (Read Operation)

1. Define Query in `application/queries/new_feature.py`:
   - Query class (frozen dataclass with input parameters)
   - QueryHandler class (receives port in `__init__`, implements `async def handle()`)
   - Handler must map Domain Model → DTO in `_map_to_dto()` method

2. Register in QueryBus:
   - Update `application/bus/dispatcher.py`
   - Add handler parameter to `create_query_bus()`
   - Call `bus.register(QueryType, handler.handle)`

3. Create MCP Tool in `infrastructure/mcp/server.py`:
   - Add `@mcp.tool` decorated function
   - Call `query_bus.execute(Query(...))`

4. Wire in `main.py`:
   - Instantiate handler with required ports
   - Pass to `create_query_bus()`

### New Bounded Context

Create new directory in `core/` (e.g., `core/pricing/`):
- `models.py` - Domain models, value objects, aggregates
- `ports.py` - Abstract interfaces for external dependencies
- `services.py` - Domain services (optional)
- `__init__.py` - Export public API

Mirror structure in `application/` for DTOs, queries, commands.

Implement adapters in `infrastructure/` that implement the ports.

### New Adapter (e.g., caching layer)

Create class in `infrastructure/` that:
- Implements existing Port interface from `core/`
- Can wrap another adapter (decorator pattern)
- Is dependency-injected in `main.py`

Example: `CachedShipmentTracking` wraps `GlobKurierHttpClient`.

## Testing Patterns

**Domain Tests**: Pure business logic, no mocking needed. Test value objects, aggregates, domain services.

**Application Tests**: Mock ports using `AsyncMock()`. Verify:
- Query/Command creation
- Port calls with correct parameters
- Domain → DTO mapping

**Infrastructure Tests**: Test actual adapters. May use real HTTP calls or mocking libraries like `respx`.

## Configuration

Uses Pydantic Settings loaded from `.env`. All settings in `config/settings.py`.

Configuration is loaded once at startup via `get_settings()` (cached with `@lru_cache`).

## Logging

The application uses Python's built-in `logging` module with configurable file and console output.

### Logging Configuration (via `.env`)

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_PATH=/var/log/globkurier-mcp/app.log  # Leave empty for console-only
LOG_FILE_MAX_BYTES=10485760  # 10MB per file
LOG_FILE_BACKUP_COUNT=5  # Number of rotated backup files
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_REQUESTS=true  # Enable HTTP request/response logging
```

### What Gets Logged

**Application Startup** (`main.py`):
- Configuration loaded
- Components initialized
- Server startup with host/port/transport

**Query Handlers** (`application/queries/`):
- Query execution start/completion
- Result summaries (status, event count, etc.)

**HTTP Client** (`infrastructure/http/`):
- Outgoing HTTP requests (when `LOG_REQUESTS=true`)
- Response status codes
- Response bodies at DEBUG level
- HTTP errors with details
- Request failures with error messages

**Log Levels**:
- `DEBUG`: Detailed request/response bodies, component initialization
- `INFO`: Request summaries, successful operations, startup messages
- `WARNING`: Shipment not found, recoverable errors
- `ERROR`: HTTP errors, request failures
- `CRITICAL`: Application-level failures

### Log File Behavior

- **Rotation**: When log file reaches `LOG_FILE_MAX_BYTES`, it rotates to `.log.1`, `.log.2`, etc.
- **Retention**: Keeps `LOG_FILE_BACKUP_COUNT` backup files, deletes oldest
- **Directory Creation**: Parent directories created automatically if they don't exist
- **Console Always On**: Console logging always enabled regardless of file logging

### Viewing Logs

```bash
# Tail live logs
tail -f /var/log/globkurier-mcp/app.log

# View last 100 lines
tail -n 100 /var/log/globkurier-mcp/app.log

# Search for errors
grep "ERROR" /var/log/globkurier-mcp/app.log

# Watch specific shipment
grep "GK160825421616" /var/log/globkurier-mcp/app.log
```

### Adding Logging to New Code

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.info("Operation started")
logger.debug(f"Details: {some_data}")
logger.warning("Recoverable issue")
logger.error("Operation failed", exc_info=True)  # Includes traceback
logger.exception("Unexpected error")  # Auto-includes exception info
```

Logging is set up in `infrastructure/logging/config.py` and initialized early in `main.py`.

## Common Pitfalls to Avoid

1. **Don't bypass layers**: MCP tools must use QueryBus, not call adapters directly
2. **Don't leak domain models**: Always map to DTOs before returning from application layer
3. **Don't import upwards**: `core/` cannot import from `application/` or `infrastructure/`
4. **Don't forget DI**: New handlers must be wired in `main.py`
5. **Don't mutate value objects**: They're frozen dataclasses for a reason
6. **Don't put business logic in handlers**: It belongs in domain models/services
7. **Don't return domain exceptions to MCP**: Catch and convert to appropriate response format

## Bounded Contexts (Current)

**shipping/** (✅ Implemented)
- Tracking shipments from GlobKurier API
- Domain: ShipmentId, TrackingEvent, ShipmentStatus
- Port: ShipmentTrackingPort
- Query: GetShipmentStatusQuery
- Adapter: GlobKurierHttpClient

**pricing/, orders/, products/** (Planned)
- Follow same pattern as shipping/

## Important Files

- `main.py` - Dependency injection root, study this to understand wiring
- `application/bus/dispatcher.py` - QueryBus implementation
- `core/shipping/ports.py` - Example of port definition
- `infrastructure/http/globkurier_client.py` - Example adapter implementation with request/response logging
- `application/queries/get_shipment_status.py` - Example query handler with DTO mapping and logging
- `infrastructure/logging/config.py` - Logging setup with file rotation
- `config/settings.py` - All application settings including logging configuration

## MCP Server Details

Server runs on `http://127.0.0.1:9000` by default (configurable via `.env`).

Available tools:
- `ping` - Health check
- `get_shipment_status` - Track shipment by order number

Transport modes: http, sse, stdio (configurable via `MCP_TRANSPORT`)
