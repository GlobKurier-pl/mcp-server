"""GlobKurier MCP Server - Hexagonal Architecture Implementation.

This package implements a Model Context Protocol (MCP) server for GlobKurier API
using Clean Architecture and CQRS principles.

Architecture layers:
- core: Domain models, value objects, and ports (business logic)
- application: Use cases, DTOs, queries, commands, and bus (orchestration)
- infrastructure: HTTP clients, MCP tools, external adapters (implementation details)
- config: Settings and configuration
"""

from globkurier_mcp.main import main

__version__ = "0.2.0"
__all__ = ["main"]
