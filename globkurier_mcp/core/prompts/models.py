"""Domain models for prompt management.

This module contains value objects and domain models for the prompts bounded context.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptDefinition:
    """Value object representing a prompt definition.

    This is a domain model that represents a prompt with all its metadata.
    Immutable by design (frozen dataclass).
    """

    name: str
    description: str
    tags: tuple[str, ...]  # Immutable tuple instead of set
    meta: dict[str, Any]  # Metadata like category, priority, language, etc.
    role: str  # Usually "system" or "user"
    content: str | None = None  # None for composite prompts
    composite: bool = False  # Whether this is a composite prompt
    includes: tuple[str, ...] = ()  # Names of included prompts (for composite)
    supports_user_context: bool = False  # Whether prompt accepts user context

    def __post_init__(self) -> None:
        """Validate prompt definition."""
        if not self.name:
            raise ValueError("Prompt name cannot be empty")
        if not self.description:
            raise ValueError("Prompt description cannot be empty")
        if not self.composite and not self.content:
            raise ValueError(f"Non-composite prompt '{self.name}' must have content")
        if self.composite and not self.includes:
            raise ValueError(f"Composite prompt '{self.name}' must include other prompts")


@dataclass(frozen=True)
class PromptMessage:
    """Value object representing a single prompt message.

    This is used to construct complete prompts from definitions.
    """

    role: str
    content: str

    def __post_init__(self) -> None:
        """Validate prompt message."""
        if not self.role:
            raise ValueError("Prompt message role cannot be empty")
        if not self.content:
            raise ValueError("Prompt message content cannot be empty")
