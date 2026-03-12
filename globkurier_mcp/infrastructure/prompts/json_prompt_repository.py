"""JSON-based implementation of PromptRepositoryPort.

This is an infrastructure adapter that implements the domain port interface.
It loads prompts from JSON files in the data directory.
"""

import json
import logging
from pathlib import Path

from globkurier_mcp.core.prompts.models import PromptDefinition
from globkurier_mcp.core.prompts.ports import PromptRepositoryPort

logger = logging.getLogger(__name__)


class JsonPromptRepository(PromptRepositoryPort):
    """JSON file-based implementation of PromptRepositoryPort.

    This adapter implements the port defined in the domain layer.
    It loads prompts from JSON files in the data directory.
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize repository with data directory.

        Args:
            data_dir: Path to directory containing JSON prompt files.
                     If None, uses default data/ subdirectory.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"

        self._data_dir = data_dir
        self._prompts: dict[str, PromptDefinition] | None = None
        logger.debug(f"Initialized JsonPromptRepository with data_dir={data_dir}")

    async def get_all_prompts(self) -> list[PromptDefinition]:
        """Load all prompts from JSON files.

        Returns:
            List of all prompt definitions

        Raises:
            ValueError: If JSON files cannot be loaded or parsed
        """
        if self._prompts is None:
            await self._load_prompts()
        assert self._prompts is not None

        return list(self._prompts.values())

    async def get_prompt_by_name(self, name: str) -> PromptDefinition | None:
        """Get a specific prompt by name.

        Args:
            name: Prompt name to search for

        Returns:
            PromptDefinition if found, None otherwise
        """
        if self._prompts is None:
            await self._load_prompts()
        assert self._prompts is not None

        return self._prompts.get(name)

    async def _load_prompts(self) -> None:
        """Load all prompts from JSON files in data directory.

        Raises:
            ValueError: If data directory doesn't exist or JSON is invalid
        """
        if not self._data_dir.exists():
            raise ValueError(f"Prompts data directory not found: {self._data_dir}")

        self._prompts = {}

        for json_file in self._data_dir.glob("*.json"):
            try:
                prompt = self._load_prompt_from_file(json_file)
                self._prompts[prompt.name] = prompt
                logger.debug(f"Loaded prompt '{prompt.name}' from {json_file.name}")

            except (ValueError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load prompt from {json_file}: {e}")
                # Don't fail completely, just skip this file
                continue

        logger.info(f"Loaded {len(self._prompts)} prompts from {self._data_dir}")

    def _load_prompt_from_file(self, file_path: Path) -> PromptDefinition:
        """Load a single prompt from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            PromptDefinition instance

        Raises:
            ValueError: If JSON is invalid or missing required fields
            json.JSONDecodeError: If file contains invalid JSON
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Validate required fields
        if "name" not in data:
            raise ValueError(f"Prompt file {file_path} missing 'name' field")
        if "description" not in data:
            raise ValueError(f"Prompt file {file_path} missing 'description' field")

        # Convert list to tuple for immutability
        tags = tuple(data.get("tags", []))
        includes = tuple(data.get("includes", []))

        # Create domain model
        return PromptDefinition(
            name=data["name"],
            description=data["description"],
            tags=tags,
            meta=data.get("meta", {}),
            role=data.get("role", "system"),
            content=data.get("content"),
            composite=data.get("composite", False),
            includes=includes,
            supports_user_context=data.get("supports_user_context", False),
        )
