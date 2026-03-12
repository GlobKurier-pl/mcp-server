"""MCP Prompts module for GlobKurier AI Assistant.

This module provides automatic prompt registration with the FastMCP server
using CQRS pattern through QueryBus.
"""

from globkurier_mcp.infrastructure.mcp.prompts.prompt_registry import register_prompts

__all__ = [
    "register_prompts",
]
