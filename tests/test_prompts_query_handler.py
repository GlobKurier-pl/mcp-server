"""Tests for prompts query handlers - demonstrating port/adapter mocking."""

from unittest.mock import AsyncMock

import pytest

from globkurier_mcp.application.queries.get_prompts import (
    GetAllPromptsQuery,
    GetAllPromptsQueryHandler,
    GetPromptByNameQuery,
    GetPromptByNameQueryHandler,
)
from globkurier_mcp.core.prompts.models import PromptDefinition


@pytest.fixture
def mock_prompt_repository():
    """Mock PromptRepositoryPort - demonstrates hexagonal architecture!"""
    return AsyncMock()


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        PromptDefinition(
            name="system",
            description="System prompt",
            tags=("core", "system"),
            meta={"category": "system", "priority": "critical"},
            role="system",
            content="You are a helpful assistant.",
        ),
        PromptDefinition(
            name="developer",
            description="Developer prompt",
            tags=("developer", "tools"),
            meta={"category": "developer", "priority": "high"},
            role="system",
            content="Use tools when possible.",
        ),
        PromptDefinition(
            name="complete_assistant",
            description="Complete assistant",
            tags=("complete", "composite"),
            meta={"category": "complete", "priority": "highest"},
            role="system",
            composite=True,
            includes=("system", "developer"),
            supports_user_context=True,
        ),
    ]


@pytest.mark.asyncio
async def test_get_all_prompts_query_handler(mock_prompt_repository, sample_prompts):
    """Test GetAllPromptsQueryHandler with mocked port."""
    # Arrange - setup mock to return sample prompts
    mock_prompt_repository.get_all_prompts.return_value = sample_prompts

    # Create handler with mocked port (dependency injection)
    handler = GetAllPromptsQueryHandler(prompt_repository=mock_prompt_repository)

    # Act - execute query
    query = GetAllPromptsQuery()
    result = await handler.handle(query)

    # Assert - verify results
    assert len(result) == 3
    assert result[0].name == "system"
    assert result[1].name == "developer"
    assert result[2].name == "complete_assistant"
    assert result[2].composite is True

    # Verify port was called correctly
    mock_prompt_repository.get_all_prompts.assert_called_once()


@pytest.mark.asyncio
async def test_get_prompt_by_name_query_handler_found(
    mock_prompt_repository, sample_prompts
):
    """Test GetPromptByNameQueryHandler when prompt is found."""
    # Arrange - setup mock to return specific prompt
    system_prompt = sample_prompts[0]
    mock_prompt_repository.get_prompt_by_name.return_value = system_prompt

    # Create handler with mocked port
    handler = GetPromptByNameQueryHandler(prompt_repository=mock_prompt_repository)

    # Act - execute query
    query = GetPromptByNameQuery(name="system")
    result = await handler.handle(query)

    # Assert - verify result
    assert result is not None
    assert result.name == "system"
    assert result.description == "System prompt"
    assert result.content == "You are a helpful assistant."

    # Verify port was called with correct name
    mock_prompt_repository.get_prompt_by_name.assert_called_once_with("system")


@pytest.mark.asyncio
async def test_get_prompt_by_name_query_handler_not_found(mock_prompt_repository):
    """Test GetPromptByNameQueryHandler when prompt is not found."""
    # Arrange - setup mock to return None
    mock_prompt_repository.get_prompt_by_name.return_value = None

    # Create handler with mocked port
    handler = GetPromptByNameQueryHandler(prompt_repository=mock_prompt_repository)

    # Act - execute query
    query = GetPromptByNameQuery(name="nonexistent")
    result = await handler.handle(query)

    # Assert - verify None is returned
    assert result is None

    # Verify port was called with correct name
    mock_prompt_repository.get_prompt_by_name.assert_called_once_with("nonexistent")


@pytest.mark.asyncio
async def test_get_all_prompts_returns_domain_models(
    mock_prompt_repository, sample_prompts
):
    """Test that handler returns domain models, not DTOs."""
    # Arrange
    mock_prompt_repository.get_all_prompts.return_value = sample_prompts
    handler = GetAllPromptsQueryHandler(prompt_repository=mock_prompt_repository)

    # Act
    query = GetAllPromptsQuery()
    result = await handler.handle(query)

    # Assert - result should be domain models
    assert all(isinstance(prompt, PromptDefinition) for prompt in result)
    assert all(hasattr(prompt, "name") for prompt in result)
    assert all(hasattr(prompt, "content") for prompt in result)


@pytest.mark.asyncio
async def test_get_prompt_by_name_case_sensitivity(mock_prompt_repository, sample_prompts):
    """Test that name search respects exact case from repository."""
    # Arrange
    system_prompt = sample_prompts[0]
    mock_prompt_repository.get_prompt_by_name.return_value = system_prompt

    handler = GetPromptByNameQueryHandler(prompt_repository=mock_prompt_repository)

    # Act
    query = GetPromptByNameQuery(name="system")
    result = await handler.handle(query)

    # Assert - should get result
    assert result is not None
    assert result.name == "system"

    # Verify exact name was passed to repository
    mock_prompt_repository.get_prompt_by_name.assert_called_once_with("system")


@pytest.mark.asyncio
async def test_handler_delegates_to_port(mock_prompt_repository, sample_prompts):
    """Test that handler properly delegates to the port (no business logic)."""
    # Arrange
    mock_prompt_repository.get_all_prompts.return_value = sample_prompts
    handler = GetAllPromptsQueryHandler(prompt_repository=mock_prompt_repository)

    # Act
    await handler.handle(GetAllPromptsQuery())

    # Assert - handler should delegate to port, not implement logic
    mock_prompt_repository.get_all_prompts.assert_called_once()
    # No additional processing should happen - handler is thin layer


@pytest.mark.asyncio
async def test_get_all_prompts_empty_list(mock_prompt_repository):
    """Test handler behavior with empty prompt list."""
    # Arrange - repository returns empty list
    mock_prompt_repository.get_all_prompts.return_value = []

    handler = GetAllPromptsQueryHandler(prompt_repository=mock_prompt_repository)

    # Act
    query = GetAllPromptsQuery()
    result = await handler.handle(query)

    # Assert - should return empty list, not None
    assert result == []
    assert isinstance(result, list)
