"""Ports (interfaces) for prompt repository.

This module defines abstract interfaces that infrastructure must implement.
Follows Dependency Inversion Principle - domain defines what it needs,
infrastructure provides the implementation.
"""

from abc import ABC, abstractmethod

from globkurier_mcp.core.prompts.models import PromptDefinition


class PromptRepositoryPort(ABC):
    """Abstract interface for prompt repository.

    This port defines what operations the domain needs from a prompt repository.
    Infrastructure layer must implement this interface.
    """

    @abstractmethod
    async def get_all_prompts(self) -> list[PromptDefinition]:
        """Retrieve all available prompt definitions.

        Returns:
            List of all prompt definitions

        Raises:
            Exception: If prompts cannot be loaded
        """
        pass

    @abstractmethod
    async def get_prompt_by_name(self, name: str) -> PromptDefinition | None:
        """Retrieve a specific prompt by name.

        Args:
            name: Prompt name to search for

        Returns:
            PromptDefinition if found, None otherwise
        """
        pass
