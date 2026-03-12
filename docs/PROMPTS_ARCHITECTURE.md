# Prompts Architecture - Hexagonal + CQRS

## Overview

System promptów został zaimplementowany zgodnie z architekturą hexagonalną (Ports & Adapters) i wzorcem CQRS (Command Query Responsibility Segregation), tak jak reszta aplikacji.

## Architecture Layers

### 1. Domain Layer (`core/prompts/`)

**Odpowiedzialność**: Definicje modeli domenowych i interfejsów (portów).

**Pliki**:
- `models.py` - Value objects:
  - `PromptDefinition` - niemodyfikowalny (frozen dataclass) model promptu
  - `PromptMessage` - pojedyncza wiadomość w sekwencji promptu
- `ports.py` - Abstrakcyjne interfejsy:
  - `PromptRepositoryPort` - definicja kontraktu dla repository

**Kluczowe zasady**:
- Domain NIE zależy od żadnej innej warstwy
- Wszystkie modele są immutable (frozen dataclass)
- Kolekcje używają tuple zamiast list (immutability)

### 2. Application Layer (`application/queries/`)

**Odpowiedzialność**: Query handlers implementujące CQRS pattern.

**Pliki**:
- `get_prompts.py`:
  - `GetAllPromptsQuery` - query bez parametrów (pobiera wszystkie prompty)
  - `GetAllPromptsQueryHandler` - handler z logiką pobierania
  - `GetPromptByNameQuery` - query z parametrem name
  - `GetPromptByNameQueryHandler` - handler wyszukujący po nazwie

**Kluczowe zasady**:
- Query objects są immutable (frozen dataclass)
- Handlers otrzymują porty przez dependency injection
- Handlers delegują operacje do portów (nie zawierają logiki biznesowej)

### 3. Infrastructure Layer (`infrastructure/prompts/`)

**Odpowiedzialność**: Implementacje portów (adapters).

**Pliki**:
- `json_prompt_repository.py`:
  - `JsonPromptRepository` - implementacja `PromptRepositoryPort`
  - Ładuje prompty z plików JSON w katalogu `data/`
  - Cache'uje załadowane prompty w pamięci

**Pliki JSON** (`infrastructure/prompts/data/`):
- `system.json` - główny prompt systemowy
- `developer.json` - zasady używania narzędzi
- `policy.json` - zasady bezpieczeństwa
- `fallback.json` - obsługa błędów
- `debug.json` - tryb deweloperski
- `complete_assistant.json` - kompozycja wszystkich promptów

**Kluczowe zasady**:
- Adapter implementuje port z domain layer
- Infrastructure zależy od domain, nie odwrotnie
- JSON jako źródło danych (łatwa edycja bez rebuildu)

### 4. MCP Layer (`infrastructure/mcp/prompts/`)

**Odpowiedzialność**: Rejestracja promptów w FastMCP.

**Pliki**:
- `prompt_registry.py`:
  - `register_prompts()` - funkcja rejestrująca prompty w MCP
  - Używa QueryBus do pobrania promptów (CQRS)
  - Obsługuje prompty proste i kompozytowe
  - Warunkowa rejestracja (debug tylko w DEBUG mode)

## Data Flow (Request Flow)

```
MCP Server Startup
  → main.py creates infrastructure
    → JsonPromptRepository (implements PromptRepositoryPort)
  → main.py creates handlers with DI
    → GetAllPromptsQueryHandler(prompt_repository)
  → main.py registers handlers in QueryBus
    → bus.register(GetAllPromptsQuery, handler.handle)
  → main.py creates MCP server
    → create_mcp_server(query_bus, settings)
  → server.py calls register_prompts()
    → register_prompts(mcp, query_bus, settings)
      → Executes GetAllPromptsQuery via QueryBus
        → QueryBus routes to GetAllPromptsQueryHandler
          → Handler calls prompt_repository.get_all_prompts()
            → JsonPromptRepository loads from JSON files
          ← Returns list[PromptDefinition]
        ← Handler returns domain models
      ← register_prompts gets prompts
      → Registers each prompt with FastMCP
        → @mcp.prompt(...) decorators
  → MCP server starts with registered prompts
```

## Dependency Injection Flow (main.py)

```python
# 1. Create infrastructure adapter
prompt_repository = JsonPromptRepository()

# 2. Create application handlers (DI: inject port)
get_all_prompts_handler = GetAllPromptsQueryHandler(
    prompt_repository=prompt_repository
)
get_prompt_by_name_handler = GetPromptByNameQueryHandler(
    prompt_repository=prompt_repository
)

# 3. Register handlers in QueryBus
query_bus = create_query_bus(
    get_all_prompts_handler=get_all_prompts_handler,
    get_prompt_by_name_handler=get_prompt_by_name_handler,
    # ... other handlers
)

# 4. Create MCP server (uses QueryBus)
mcp = create_mcp_server(query_bus=query_bus, settings=settings)
```

## Adding New Prompts

### Option 1: Add JSON file (Recommended)

1. Create new JSON file in `infrastructure/prompts/data/`:

```json
{
  "name": "new_prompt",
  "description": "Description of the prompt",
  "tags": ["tag1", "tag2"],
  "meta": {
    "category": "category_name",
    "priority": "high"
  },
  "role": "system",
  "content": "Prompt content here..."
}
```

2. Restart server - prompt will be automatically loaded and registered

### Option 2: Composite Prompt

For prompts that combine other prompts:

```json
{
  "name": "custom_assistant",
  "description": "Custom combination of prompts",
  "tags": ["composite", "custom"],
  "meta": {
    "category": "complete"
  },
  "role": "system",
  "composite": true,
  "includes": ["system", "developer"],
  "supports_user_context": true
}
```

## Testing

Run the hexagonal architecture test:

```bash
uv run python test_hexagonal_prompts.py
```

This verifies:
- Domain models (immutability, value objects)
- Port/Adapter pattern
- CQRS query execution
- Dependency injection
- Layer separation

## Benefits of This Architecture

1. **Separation of Concerns**
   - Domain logic isolated from infrastructure
   - Easy to understand each layer's responsibility

2. **Testability**
   - Each layer can be tested independently
   - Easy to mock ports for unit tests

3. **Flexibility**
   - Easy to swap JSON repository for database
   - No changes needed in domain or application layers

4. **Maintainability**
   - Prompts as JSON files (no code rebuild needed)
   - Clear structure follows existing patterns

5. **Scalability**
   - CQRS pattern allows for future optimization
   - Can add caching layer easily (decorator pattern)

## Architecture Verification

The implementation follows these principles:

✓ **Hexagonal Architecture**
  - Domain defines ports (interfaces)
  - Infrastructure implements ports (adapters)
  - Dependency flows inward (Infrastructure → Application → Domain)

✓ **CQRS Pattern**
  - Separate queries for reading data
  - Handlers process queries asynchronously
  - Query bus routes queries to handlers

✓ **Dependency Inversion**
  - High-level modules don't depend on low-level modules
  - Both depend on abstractions (ports)

✓ **Immutability**
  - Domain models are frozen dataclasses
  - Uses tuples instead of lists for collections

✓ **Clean Code**
  - Single Responsibility Principle
  - Open/Closed Principle (extensible via ports)
  - Interface Segregation (focused ports)
