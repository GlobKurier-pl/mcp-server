"""Tests for prompts domain models - value objects and immutability."""

import pytest

from globkurier_mcp.core.prompts.models import PromptDefinition, PromptMessage


def test_prompt_definition_value_object():
    """Test PromptDefinition value object creation."""
    # Valid simple prompt
    prompt = PromptDefinition(
        name="test_prompt",
        description="Test prompt description",
        tags=("test", "example"),
        meta={"category": "test", "priority": "low"},
        role="system",
        content="This is test content",
    )

    assert prompt.name == "test_prompt"
    assert prompt.description == "Test prompt description"
    assert prompt.tags == ("test", "example")
    assert prompt.role == "system"
    assert prompt.content == "This is test content"
    assert prompt.composite is False


def test_prompt_definition_composite():
    """Test composite prompt definition."""
    composite_prompt = PromptDefinition(
        name="composite_test",
        description="Composite prompt",
        tags=("composite",),
        meta={"category": "complete"},
        role="system",
        composite=True,
        includes=("prompt1", "prompt2"),
        supports_user_context=True,
    )

    assert composite_prompt.composite is True
    assert composite_prompt.includes == ("prompt1", "prompt2")
    assert composite_prompt.supports_user_context is True
    assert composite_prompt.content is None


def test_prompt_definition_immutability():
    """Test PromptDefinition is immutable (frozen dataclass)."""
    prompt = PromptDefinition(
        name="test",
        description="Test",
        tags=("test",),
        meta={},
        role="system",
        content="Content",
    )

    # Should not be able to modify frozen dataclass
    with pytest.raises(Exception):
        prompt.name = "modified"  # type: ignore

    with pytest.raises(Exception):
        prompt.content = "modified content"  # type: ignore


def test_prompt_definition_validation_empty_name():
    """Test validation fails for empty name."""
    with pytest.raises(ValueError, match="Prompt name cannot be empty"):
        PromptDefinition(
            name="",
            description="Test",
            tags=(),
            meta={},
            role="system",
            content="Content",
        )


def test_prompt_definition_validation_empty_description():
    """Test validation fails for empty description."""
    with pytest.raises(ValueError, match="Prompt description cannot be empty"):
        PromptDefinition(
            name="test",
            description="",
            tags=(),
            meta={},
            role="system",
            content="Content",
        )


def test_prompt_definition_validation_non_composite_without_content():
    """Test validation fails for non-composite prompt without content."""
    with pytest.raises(ValueError, match="Non-composite prompt .* must have content"):
        PromptDefinition(
            name="test",
            description="Test",
            tags=(),
            meta={},
            role="system",
            content=None,
            composite=False,
        )


def test_prompt_definition_validation_composite_without_includes():
    """Test validation fails for composite prompt without includes."""
    with pytest.raises(ValueError, match="Composite prompt .* must include other prompts"):
        PromptDefinition(
            name="test",
            description="Test",
            tags=(),
            meta={},
            role="system",
            composite=True,
            includes=(),
        )


def test_prompt_message_value_object():
    """Test PromptMessage value object creation."""
    message = PromptMessage(
        role="system",
        content="This is a test message",
    )

    assert message.role == "system"
    assert message.content == "This is a test message"


def test_prompt_message_immutability():
    """Test PromptMessage is immutable (frozen dataclass)."""
    message = PromptMessage(role="system", content="Content")

    # Should not be able to modify frozen dataclass
    with pytest.raises(Exception):
        message.role = "user"  # type: ignore

    with pytest.raises(Exception):
        message.content = "modified"  # type: ignore


def test_prompt_message_validation_empty_role():
    """Test validation fails for empty role."""
    with pytest.raises(ValueError, match="Prompt message role cannot be empty"):
        PromptMessage(role="", content="Content")


def test_prompt_message_validation_empty_content():
    """Test validation fails for empty content."""
    with pytest.raises(ValueError, match="Prompt message content cannot be empty"):
        PromptMessage(role="system", content="")


def test_prompt_definition_uses_tuples():
    """Test that PromptDefinition uses tuples for immutability."""
    prompt = PromptDefinition(
        name="test",
        description="Test",
        tags=("tag1", "tag2"),
        meta={},
        role="system",
        content="Content",
    )

    # Tags should be tuple, not list
    assert isinstance(prompt.tags, tuple)

    # Includes should be tuple, not list
    composite = PromptDefinition(
        name="composite",
        description="Test",
        tags=(),
        meta={},
        role="system",
        composite=True,
        includes=("prompt1", "prompt2"),
    )
    assert isinstance(composite.includes, tuple)
