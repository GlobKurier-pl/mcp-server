"""Tests for JsonPromptRepository - infrastructure adapter tests."""

import json
import tempfile
from pathlib import Path

import pytest

from globkurier_mcp.core.prompts.models import PromptDefinition
from globkurier_mcp.infrastructure.prompts.json_prompt_repository import (
    JsonPromptRepository,
)


@pytest.fixture
def temp_prompts_dir():
    """Create temporary directory with test prompt files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # Create test prompt files
        prompts = [
            {
                "name": "test_system",
                "description": "Test system prompt",
                "tags": ["test", "system"],
                "meta": {"category": "test", "priority": "high"},
                "role": "system",
                "content": "This is a test system prompt.",
            },
            {
                "name": "test_developer",
                "description": "Test developer prompt",
                "tags": ["test", "developer"],
                "meta": {"category": "developer"},
                "role": "system",
                "content": "This is a test developer prompt.",
            },
            {
                "name": "test_composite",
                "description": "Test composite prompt",
                "tags": ["test", "composite"],
                "meta": {"category": "complete"},
                "role": "system",
                "composite": True,
                "includes": ["test_system", "test_developer"],
                "supports_user_context": True,
            },
        ]

        for prompt_data in prompts:
            file_path = data_dir / f"{prompt_data['name']}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, indent=2)

        yield data_dir


@pytest.mark.asyncio
async def test_json_repository_loads_all_prompts(temp_prompts_dir):
    """Test that repository loads all prompts from JSON files."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompts = await repository.get_all_prompts()

    # Assert
    assert len(prompts) == 3
    assert all(isinstance(p, PromptDefinition) for p in prompts)

    prompt_names = [p.name for p in prompts]
    assert "test_system" in prompt_names
    assert "test_developer" in prompt_names
    assert "test_composite" in prompt_names


@pytest.mark.asyncio
async def test_json_repository_get_prompt_by_name(temp_prompts_dir):
    """Test getting a specific prompt by name."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("test_system")

    # Assert
    assert prompt is not None
    assert prompt.name == "test_system"
    assert prompt.description == "Test system prompt"
    assert prompt.content == "This is a test system prompt."
    assert prompt.tags == ("test", "system")  # Converted to tuple
    assert prompt.composite is False


@pytest.mark.asyncio
async def test_json_repository_get_nonexistent_prompt(temp_prompts_dir):
    """Test getting a prompt that doesn't exist."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("nonexistent")

    # Assert
    assert prompt is None


@pytest.mark.asyncio
async def test_json_repository_converts_lists_to_tuples(temp_prompts_dir):
    """Test that JSON arrays are converted to tuples for immutability."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("test_composite")

    # Assert
    assert prompt is not None
    assert isinstance(prompt.tags, tuple)
    assert isinstance(prompt.includes, tuple)
    assert prompt.includes == ("test_system", "test_developer")


@pytest.mark.asyncio
async def test_json_repository_caches_prompts(temp_prompts_dir):
    """Test that repository caches loaded prompts."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act - load prompts twice
    prompts1 = await repository.get_all_prompts()
    prompts2 = await repository.get_all_prompts()

    # Assert - should return same cached data
    assert prompts1 == prompts2
    assert repository._prompts is not None  # Cache is populated


@pytest.mark.asyncio
async def test_json_repository_handles_missing_directory():
    """Test that repository raises error for missing directory."""
    # Arrange
    nonexistent_dir = Path("/nonexistent/directory/that/does/not/exist")
    repository = JsonPromptRepository(data_dir=nonexistent_dir)

    # Act & Assert
    with pytest.raises(ValueError, match="Prompts data directory not found"):
        await repository.get_all_prompts()


@pytest.mark.asyncio
async def test_json_repository_skips_invalid_json(temp_prompts_dir):
    """Test that repository skips invalid JSON files."""
    # Arrange
    invalid_file = temp_prompts_dir / "invalid.json"
    with open(invalid_file, "w") as f:
        f.write("{ invalid json content")

    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act - should skip invalid file
    prompts = await repository.get_all_prompts()

    # Assert - should still load valid prompts
    assert len(prompts) == 3  # Only valid prompts


@pytest.mark.asyncio
async def test_json_repository_validates_required_fields(temp_prompts_dir):
    """Test that repository validates required fields in JSON."""
    # Arrange - create file without required 'name' field
    invalid_prompt = {
        "description": "Missing name",
        "tags": [],
        "meta": {},
        "role": "system",
        "content": "Content",
    }

    invalid_file = temp_prompts_dir / "missing_name.json"
    with open(invalid_file, "w", encoding="utf-8") as f:
        json.dump(invalid_prompt, f)

    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act - should skip invalid file
    prompts = await repository.get_all_prompts()

    # Assert - should still load valid prompts
    assert len(prompts) == 3  # Only valid prompts


@pytest.mark.asyncio
async def test_json_repository_composite_prompt_properties(temp_prompts_dir):
    """Test that composite prompts are loaded correctly."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("test_composite")

    # Assert
    assert prompt is not None
    assert prompt.composite is True
    assert prompt.includes == ("test_system", "test_developer")
    assert prompt.supports_user_context is True
    assert prompt.content is None  # Composite prompts don't have content


@pytest.mark.asyncio
async def test_json_repository_preserves_meta_data(temp_prompts_dir):
    """Test that metadata is preserved correctly."""
    # Arrange
    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("test_system")

    # Assert
    assert prompt is not None
    assert prompt.meta["category"] == "test"
    assert prompt.meta["priority"] == "high"


@pytest.mark.asyncio
async def test_json_repository_default_values(temp_prompts_dir):
    """Test that repository applies default values for optional fields."""
    # Arrange - create minimal prompt (only required fields)
    minimal_prompt = {
        "name": "minimal",
        "description": "Minimal prompt",
        "content": "Content",
    }

    minimal_file = temp_prompts_dir / "minimal.json"
    with open(minimal_file, "w", encoding="utf-8") as f:
        json.dump(minimal_prompt, f)

    repository = JsonPromptRepository(data_dir=temp_prompts_dir)

    # Act
    prompt = await repository.get_prompt_by_name("minimal")

    # Assert - default values applied
    assert prompt is not None
    assert prompt.tags == ()  # Default empty tuple
    assert prompt.meta == {}  # Default empty dict
    assert prompt.role == "system"  # Default role
    assert prompt.composite is False  # Default
    assert prompt.includes == ()  # Default empty tuple
    assert prompt.supports_user_context is False  # Default
