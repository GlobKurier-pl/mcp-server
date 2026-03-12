"""Prompt registration for GlobKurier MCP server.

This module handles automatic registration of all assistant prompts
with the FastMCP server using CQRS pattern through QueryBus.
"""

import asyncio
import logging
from typing import cast

from fastmcp import FastMCP
from fastmcp.prompts.prompt import Message
from mcp.types import PromptMessage, Role

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.get_prompts import GetAllPromptsQuery
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.core.prompts.models import PromptDefinition

logger = logging.getLogger(__name__)


def register_prompts(mcp: FastMCP, query_bus: QueryBus, settings: Settings) -> None:
    """Register all GlobKurier assistant prompts with MCP server.

    Uses CQRS pattern - loads prompts via QueryBus instead of direct access.
    Debug prompt is only registered when log_level is DEBUG.

    Args:
        mcp: FastMCP server instance
        query_bus: Query bus for executing queries
        settings: Application settings (used to check if debug mode is enabled)
    """
    # Load all prompts via QueryBus (CQRS pattern)
    all_prompts_list: list[PromptDefinition] = asyncio.run(
        query_bus.execute(GetAllPromptsQuery())
    )

    if not all_prompts_list:
        logger.warning("No prompts loaded via QueryBus")
        return

    # Convert to dict for easier lookup
    all_prompts = {prompt.name: prompt for prompt in all_prompts_list}

    # Register each prompt
    registered_count = 0
    for prompt_name, prompt_def in all_prompts.items():
        # Skip debug prompt if not in debug mode
        if prompt_name == "debug" and settings.log_level != "DEBUG":
            logger.debug("Skipping debug prompt (not in DEBUG mode)")
            continue

        # Handle composite prompts specially
        if prompt_def.composite:
            _register_composite_prompt(mcp, prompt_def, all_prompts, settings)
        else:
            _register_simple_prompt(mcp, prompt_def)

        registered_count += 1

    logger.info(f"Registered {registered_count} prompts with MCP server")


def _register_simple_prompt(mcp: FastMCP, prompt_def: PromptDefinition) -> None:
    """Register a simple (non-composite) prompt.

    Args:
        mcp: FastMCP server instance
        prompt_def: PromptDefinition domain model to register
    """

    @mcp.prompt(
        name=prompt_def.name,
        description=prompt_def.description,
        tags=set(prompt_def.tags),  # Convert tuple back to set for FastMCP
        meta=prompt_def.meta,
    )
    def prompt_function() -> list[PromptMessage]:
        """Dynamically created prompt function."""
        # Convert domain PromptDefinition to FastMCP Message
        return [
            Message(
                content=prompt_def.content or "",
                role=cast(Role, prompt_def.role),
            )
        ]

    logger.debug(f"Registered simple prompt: {prompt_def.name}")


def _register_composite_prompt(
    mcp: FastMCP,
    prompt_def: PromptDefinition,
    all_prompts: dict[str, PromptDefinition],
    settings: Settings,
) -> None:
    """Register a composite prompt that includes other prompts.

    Args:
        mcp: FastMCP server instance
        prompt_def: PromptDefinition domain model to register
        all_prompts: Dictionary of all loaded prompts
        settings: Application settings (for conditional inclusion)
    """

    @mcp.prompt(
        name=prompt_def.name,
        description=prompt_def.description,
        tags=set(prompt_def.tags),  # Convert tuple back to set for FastMCP
        meta=prompt_def.meta,
    )
    def composite_prompt_function(user_context: str = "") -> list[PromptMessage]:
        """Dynamically created composite prompt function.

        Args:
            user_context: Optional user context to append

        Returns:
            List of Message instances
        """
        messages = []

        # Add all included prompts
        for included_name in prompt_def.includes:
            # Skip debug if not in debug mode
            if included_name == "debug" and settings.log_level != "DEBUG":
                continue

            if included_name not in all_prompts:
                logger.warning(
                    f"Composite prompt '{prompt_def.name}' includes '{included_name}', "
                    f"but it's not loaded"
                )
                continue

            included_prompt = all_prompts[included_name]
            # Convert domain model to FastMCP Message
            messages.append(
                Message(
                    content=included_prompt.content or "",
                    role=cast(Role, included_prompt.role),
                )
            )

        # Add debug prompt if in debug mode (even if not in includes list)
        if settings.log_level == "DEBUG" and "debug" in all_prompts:
            if "debug" not in prompt_def.includes:
                debug_prompt = all_prompts["debug"]
                messages.append(
                    Message(
                        content=debug_prompt.content or "",
                        role=cast(Role, debug_prompt.role),
                    )
                )

        # Add user context if supported and provided
        if prompt_def.supports_user_context and user_context:
            messages.append(
                Message(content=f"Kontekst: {user_context}", role="user")
            )

        return messages

    logger.debug(f"Registered composite prompt: {prompt_def.name}")
