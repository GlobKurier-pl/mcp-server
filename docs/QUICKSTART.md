# Quick Start Guide

## Instalacja

```bash
# 1. Sklonuj repozytorium
cd globkurier-api-mcp

# 2. Zainstaluj zależności za pomocą uv
uv sync

# 3. Skopiuj konfigurację
cp .env.example .env
```

## Uruchomienie

```bash
# Uruchom serwer MCP
python -m globkurier_mcp.main
```

Serwer wystartuje na `http://127.0.0.1:9000`

## Pierwsze kroki

### Testowanie połączenia

```bash
# Uruchom ping
curl -X POST http://127.0.0.1:9000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ping"
    },
    "id": 1
  }'
```

### Pobieranie statusu przesyłki

```bash
curl -X POST http://127.0.0.1:9000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_shipment_status",
      "arguments": {
        "order_number": "GK123456789000",
        "language": "pl"
      }
    },
    "id": 2
  }'
```

## Testowanie

```bash
# Uruchom wszystkie testy
pytest

# Z pokryciem kodu
pytest --cov=globkurier_mcp

# Tylko testy domenowe
pytest tests/test_domain_models.py -v

# Type checking
mypy globkurier_mcp

# Linting
ruff check globkurier_mcp
```

## Rozwój

### Dodaj nową query

1. Stwórz plik `application/queries/my_new_query.py`:

```python
from dataclasses import dataclass
from globkurier_mcp.core.shipping.ports import ShipmentTrackingPort

@dataclass(frozen=True)
class MyNewQuery:
    param: str

class MyNewQueryHandler:
    def __init__(self, port: ShipmentTrackingPort):
        self._port = port

    async def handle(self, query: MyNewQuery):
        # Implementacja
        pass
```

2. Zarejestruj w QueryBus (`application/bus/dispatcher.py`)
3. Dodaj MCP tool (`infrastructure/mcp/server.py`)

### Struktura plików

```
📁 globkurier_mcp/
├── 📁 config/           # Ustawienia (Pydantic Settings)
├── 📁 core/             # Domain Layer (logika biznesowa)
│   └── 📁 shipping/     # Bounded context: shipping
├── 📁 application/      # Use cases, DTO, CQRS
│   ├── 📁 dto/
│   ├── 📁 queries/
│   ├── 📁 commands/
│   └── 📁 bus/
├── 📁 infrastructure/   # Adaptery (HTTP, MCP)
│   ├── 📁 http/
│   └── 📁 mcp/
└── main.py              # Entrypoint + DI
```

## Następne kroki

1. Przeczytaj `docs/ARCHITECTURE.md` dla głębszego zrozumienia
2. Zobacz testy w `tests/` jako przykłady użycia
3. Dodaj własne bounded contexts w `core/`
4. Zaimplementuj Commands dla operacji zapisu

## Troubleshooting

### Import errors
```bash
# Upewnij się że jesteś w głównym katalogu projektu
python -c "import globkurier_mcp; print('OK')"
```

### Port zajęty
```bash
# Zmień port w .env
MCP_PORT=9001
```

### Problemy z zależnościami
```bash
# Zainstaluj ponownie
uv sync --reinstall
```
