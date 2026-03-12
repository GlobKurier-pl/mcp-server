<!-- mcp-name: io.github.globkurier/globkurier-api-mcp -->

# GlobKurier MCP Server

> [Polska wersja dokumentacji](./README.pl.md)

[Model Context Protocol](https://modelcontextprotocol.io/) server for the [GlobKurier](https://www.globkurier.pl) API. Enables AI assistants (Claude, Cursor, Cline and others) to track shipments, search shipping products and generate purchase links.

## Installation

### Recommended: Hosted server (no local installation)

```json
{
  "mcpServers": {
    "globkurier": {
      "type": "http",
      "url": "https://mcp.globkurier.pl/mcp"
    }
  }
}
```

### Alternative: Run locally via `uvx`

```json
{
  "mcpServers": {
    "globkurier": {
      "command": "uvx",
      "args": ["globkurier-api-mcp"]
    }
  }
}
```

Paste the configuration into your MCP client settings file:

| Client | Settings file |
|---|---|
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%\Claude\claude_desktop_config.json` (Windows) |
| **Cursor** | `.cursor/mcp.json` in your project or `~/.cursor/mcp.json` globally |
| **Cline** | Extension settings in VS Code |

## Available Tools

| Tool | Description |
|---|---|
| `get_shipment_status` | Track a shipment by order number |
| `search_products` | Search shipping products (DPD, InPost, DHL, FedEx, UPS, GLS and more) |
| `get_product_addons` | Get available add-ons for a product |
| `get_search_url` | Generate a purchase link for a shipment |

## Available Resources

| Resource | Description |
|---|---|
| `globkurier://countries` | List of supported countries |
| `globkurier://countries/{iso_code}` | Country details by ISO code |

---

For developer documentation see [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT

## Author

p.karbowniczek@globkurier.pl