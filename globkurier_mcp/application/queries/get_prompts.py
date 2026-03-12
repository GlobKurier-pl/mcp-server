"""Query for retrieving prompt definitions.

This module implements CQRS pattern for prompt retrieval.
"""

import logging
from dataclasses import dataclass

from globkurier_mcp.core.prompts.models import PromptDefinition
from globkurier_mcp.core.prompts.ports import PromptRepositoryPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetAllPromptsQuery:
    """Query to retrieve all available prompts.

    This is a query object in CQRS pattern - immutable and carries no logic.
    """

    pass  # No parameters needed


@dataclass(frozen=True)
class GetPromptByNameQuery:
    """Query to retrieve a specific prompt by name.

    Attributes:
        name: Prompt name to retrieve
    """

    name: str


class GetAllPromptsQueryHandler:
    """Handler for GetAllPromptsQuery.

    Follows CQRS pattern - separates query handling from business logic.
    Uses dependency injection to receive repository port.
    """

    def __init__(self, prompt_repository: PromptRepositoryPort):
        """Initialize handler with repository dependency.

        Args:
            prompt_repository: Implementation of PromptRepositoryPort
        """
        self._prompt_repository = prompt_repository

    async def handle(self, query: GetAllPromptsQuery) -> list[PromptDefinition]:
        """Handle the query by retrieving all prompts.

        Args:
            query: The query to handle

        Returns:
            List of all prompt definitions
        """
        logger.debug("Handling GetAllPromptsQuery")

        # Delegate to repository (port)
        prompts = await self._prompt_repository.get_all_prompts()

        logger.info(f"Retrieved {len(prompts)} prompts")
        return prompts


class GetPromptByNameQueryHandler:
    """Handler for GetPromptByNameQuery.

    Follows CQRS pattern - separates query handling from business logic.
    Uses dependency injection to receive repository port.
    """

    def __init__(self, prompt_repository: PromptRepositoryPort):
        """Initialize handler with repository dependency.

        Args:
            prompt_repository: Implementation of PromptRepositoryPort
        """
        self._prompt_repository = prompt_repository

    async def handle(self, query: GetPromptByNameQuery) -> PromptDefinition | None:
        """Handle the query by retrieving a specific prompt.

        Args:
            query: The query to handle

        Returns:
            PromptDefinition if found, None otherwise
        """
        logger.debug(f"Handling GetPromptByNameQuery for '{query.name}'")

        # Delegate to repository (port)
        prompt = await self._prompt_repository.get_prompt_by_name(query.name)

        if prompt:
            logger.info(f"Found prompt '{query.name}'")
        else:
            logger.warning(f"Prompt '{query.name}' not found")

        return prompt
