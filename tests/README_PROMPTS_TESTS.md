# Prompts Tests Documentation

## Overview

Testy dla nowej funkcjonalności promptów zgodne z architekturą hexagonalną i CQRS.

## Test Files

### 1. `test_prompts_domain_models.py` (12 tests)

Testy modeli domenowych (value objects) z warstwy `core/prompts/`:

**PromptDefinition tests:**
- ✓ `test_prompt_definition_value_object` - tworzenie prostego promptu
- ✓ `test_prompt_definition_composite` - tworzenie promptu kompozytowego
- ✓ `test_prompt_definition_immutability` - niezmienność (frozen dataclass)
- ✓ `test_prompt_definition_validation_empty_name` - walidacja pustej nazwy
- ✓ `test_prompt_definition_validation_empty_description` - walidacja pustego opisu
- ✓ `test_prompt_definition_validation_non_composite_without_content` - walidacja contentu
- ✓ `test_prompt_definition_validation_composite_without_includes` - walidacja includes
- ✓ `test_prompt_definition_uses_tuples` - użycie tuple zamiast list

**PromptMessage tests:**
- ✓ `test_prompt_message_value_object` - tworzenie wiadomości
- ✓ `test_prompt_message_immutability` - niezmienność
- ✓ `test_prompt_message_validation_empty_role` - walidacja roli
- ✓ `test_prompt_message_validation_empty_content` - walidacja contentu

### 2. `test_prompts_query_handler.py` (7 tests)

Testy query handlerów z warstwy aplikacji (CQRS pattern):

**GetAllPromptsQueryHandler tests:**
- ✓ `test_get_all_prompts_query_handler` - pobieranie wszystkich promptów
- ✓ `test_get_all_prompts_returns_domain_models` - zwracanie modeli domenowych
- ✓ `test_get_all_prompts_empty_list` - obsługa pustej listy
- ✓ `test_handler_delegates_to_port` - delegacja do portu (brak logiki)

**GetPromptByNameQueryHandler tests:**
- ✓ `test_get_prompt_by_name_query_handler_found` - znalezienie promptu
- ✓ `test_get_prompt_by_name_query_handler_not_found` - brak promptu
- ✓ `test_get_prompt_by_name_case_sensitivity` - case sensitivity

**Kluczowe cechy:**
- Używają `AsyncMock` do mockowania portów
- Testują dependency injection
- Weryfikują poprawność wywołań portów

### 3. `test_prompts_repository.py` (11 tests)

Testy adaptera infrastruktury (JsonPromptRepository):

**Podstawowa funkcjonalność:**
- ✓ `test_json_repository_loads_all_prompts` - ładowanie wszystkich promptów
- ✓ `test_json_repository_get_prompt_by_name` - pobieranie po nazwie
- ✓ `test_json_repository_get_nonexistent_prompt` - nieistniejący prompt

**Konwersja i walidacja:**
- ✓ `test_json_repository_converts_lists_to_tuples` - konwersja JSON array → tuple
- ✓ `test_json_repository_validates_required_fields` - walidacja pól
- ✓ `test_json_repository_default_values` - domyślne wartości

**Cache i obsługa błędów:**
- ✓ `test_json_repository_caches_prompts` - cache'owanie w pamięci
- ✓ `test_json_repository_handles_missing_directory` - brakujący katalog
- ✓ `test_json_repository_skips_invalid_json` - pomijanie błędnych plików

**Właściwości:**
- ✓ `test_json_repository_composite_prompt_properties` - prompty kompozytowe
- ✓ `test_json_repository_preserves_meta_data` - zachowanie metadanych

**Kluczowe cechy:**
- Używają `tempfile` do tworzenia testowych plików JSON
- Testują rzeczywistą implementację (nie mocki)
- Weryfikują edge cases (błędne JSON, brakujące pola, etc.)

## Running Tests

### Run all prompts tests
```bash
uv run pytest tests/test_prompts_*.py -v
```

### Run specific test file
```bash
uv run pytest tests/test_prompts_domain_models.py -v
uv run pytest tests/test_prompts_query_handler.py -v
uv run pytest tests/test_prompts_repository.py -v
```

### Run with coverage
```bash
uv run pytest tests/test_prompts_*.py \
  --cov=globkurier_mcp.core.prompts \
  --cov=globkurier_mcp.application.queries.get_prompts \
  --cov=globkurier_mcp.infrastructure.prompts \
  --cov-report=term-missing
```

### Run all project tests
```bash
uv run pytest tests/ -v
```

## Test Statistics

```
Total tests:     30
Domain models:   12
Query handlers:   7
Repository:      11

Total coverage:  96%
Status:          ✓ All passing
```

## Coverage Report

```
Module                                                        Coverage
------------------------------------------------------------------------
globkurier_mcp/application/queries/get_prompts.py            100%
globkurier_mcp/core/prompts/models.py                        100%
globkurier_mcp/core/prompts/__init__.py                      100%
globkurier_mcp/infrastructure/prompts/__init__.py            100%
globkurier_mcp/infrastructure/prompts/json_prompt_repository 95%
globkurier_mcp/core/prompts/ports.py                         78%*

* Brakujące linie w ports.py to abstrakcyjne metody (pass statements)
```

## Test Patterns

### 1. Domain Model Tests

```python
def test_domain_model_immutability():
    """Test that domain models are frozen (immutable)."""
    model = DomainModel(...)

    with pytest.raises(Exception):
        model.field = "modified"  # Should fail
```

### 2. Query Handler Tests (with Mocks)

```python
@pytest.fixture
def mock_repository():
    """Mock repository port."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_handler(mock_repository):
    """Test handler with mocked port."""
    # Arrange
    mock_repository.method.return_value = expected_data
    handler = Handler(repository=mock_repository)

    # Act
    result = await handler.handle(Query(...))

    # Assert
    assert result == expected_result
    mock_repository.method.assert_called_once()
```

### 3. Repository Tests (Integration)

```python
@pytest.fixture
def temp_data_dir():
    """Create temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        yield Path(tmpdir)

@pytest.mark.asyncio
async def test_repository(temp_data_dir):
    """Test repository with real files."""
    repository = JsonRepository(data_dir=temp_data_dir)
    result = await repository.get_all()
    assert len(result) > 0
```

## Benefits

1. **High Coverage** - 96% code coverage
2. **Hexagonal Architecture** - Tests respect layer boundaries
3. **CQRS Pattern** - Query handlers tested with mocked ports
4. **Fast Execution** - All 30 tests run in ~1 second
5. **Maintainable** - Clear naming, fixtures, and documentation
6. **Integration Tests** - Repository tests use real file I/O
7. **Unit Tests** - Domain and handler tests are isolated

## Integration with CI/CD

These tests are ready for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Prompts Tests
  run: |
    uv run pytest tests/test_prompts_*.py \
      --cov=globkurier_mcp.core.prompts \
      --cov=globkurier_mcp.application.queries.get_prompts \
      --cov=globkurier_mcp.infrastructure.prompts \
      --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Future Improvements

Możliwe rozszerzenia testów:

1. **Performance tests** - sprawdzenie cache'owania
2. **Property-based tests** - using `hypothesis` library
3. **E2E tests** - testing through MCP server
4. **Mutation testing** - using `mutmut` to verify test quality
5. **Benchmark tests** - measuring repository load times
