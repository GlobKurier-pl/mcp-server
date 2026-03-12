# GlobKurier MCP Server

> [English documentation](./README.md)

Serwer [Model Context Protocol](https://modelcontextprotocol.io/) dla API [GlobKurier](https://www.globkurier.pl). Umożliwia asystentom AI (Claude, Cursor, Cline i innym) śledzenie przesyłek, wyszukiwanie produktów wysyłkowych oraz generowanie linków do zakupu.

## Instalacja

### Zalecane: Hostowany serwer (bez instalacji lokalnej)

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

### Alternatywnie: Uruchomienie lokalne przez `uvx`

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

Wklej konfigurację do pliku ustawień swojego klienta MCP:

| Klient | Plik ustawień |
|---|---|
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%\Claude\claude_desktop_config.json` (Windows) |
| **Cursor** | `.cursor/mcp.json` w katalogu projektu lub `~/.cursor/mcp.json` globalnie |
| **Cline** | Ustawienia rozszerzenia w VS Code |

## Dostępne narzędzia

| Narzędzie | Opis |
|---|---|
| `get_shipment_status` | Śledź przesyłkę po numerze zamówienia |
| `search_products` | Szukaj produktów wysyłkowych (DPD, InPost, DHL, FedEx, UPS, GLS i inne) |
| `get_product_addons` | Pobierz dostępne dodatki do produktu |
| `get_search_url` | Wygeneruj link do zakupu przesyłki |

## Dostępne zasoby

| Zasób | Opis |
|---|---|
| `globkurier://countries` | Lista obsługiwanych krajów |
| `globkurier://countries/{iso_code}` | Szczegóły kraju po kodzie ISO |

---

Dokumentacja dla deweloperów: [CONTRIBUTING.md](./CONTRIBUTING.md).

## Licencja

MIT

## Autor

p.karbowniczek@globkurier.pl