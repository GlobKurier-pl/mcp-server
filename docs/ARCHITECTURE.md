# Architektura projektu - szczegółowa dokumentacja

## Diagram architektury warstwowej

```
┌─────────────────────────────────────────────────────────────────┐
│                      INTERFACE LAYER                             │
│                                                                   │
│  ┌────────────────────┐         ┌──────────────────────┐        │
│  │   MCP Server       │         │   HTTP Endpoints     │        │
│  │   (FastMCP)        │         │   (future)           │        │
│  └────────┬───────────┘         └──────────────────────┘        │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ Calls Tools
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MCP Tools                                               │   │
│  │  • get_shipment_status_tool()                            │   │
│  │  • (future tools...)                                     │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│                     │ Uses QueryBus                              │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HTTP Adapters (implements Ports)                        │   │
│  │  • GlobKurierHttpClient → ShipmentTrackingPort           │   │
│  │  • (future: DB, Cache, etc.)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            │ Implements
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Query Bus (CQRS)                                        │   │
│  │  Routes queries to handlers                              │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Query Handlers                                          │   │
│  │  • GetShipmentStatusQueryHandler                         │   │
│  │    - Uses Ports (interfaces)                             │   │
│  │    - Maps Domain → DTO                                   │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│  ┌──────────────────┴──────────────────────────────────────┐   │
│  │  DTOs (Data Transfer Objects)                           │   │
│  │  • ShipmentStatusDto                                     │   │
│  │  • TrackingEventDto                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            │ Uses
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER (CORE)                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Ports (Interfaces)                                      │   │
│  │  • ShipmentTrackingPort                                  │   │
│  │  • (future: PricingPort, OrderPort)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Domain Models                                           │   │
│  │  • ShipmentStatus (Aggregate Root)                       │   │
│  │  • ShipmentId (Value Object)                             │   │
│  │  • TrackingEvent (Value Object)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Domain Services                                         │   │
│  │  • ShipmentTrackingService                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Flow

```
MCP Tool
  → QueryBus.execute(Query)
    → QueryHandler.handle(Query)
      → Port.get_shipment_status()  ← Interface (defined in Domain)
        ↑
        │ Implemented by
        └── HttpClient (Infrastructure)
      ← Domain Model (ShipmentStatus)
    ← DTO (ShipmentStatusDto)  ← Mapped in Application Layer
  ← Dict (serialized)
```

## Zasady warstwowe

### 1. Domain Layer (core/)
- **NIE ZALEŻY** od żadnej innej warstwy
- Definiuje porty (interfejsy)
- Zawiera logikę biznesową
- Immutable gdzie to możliwe

### 2. Application Layer (application/)
- Zależy **TYLKO** od Domain
- Orkiestruje use cases
- Mapuje Domain ↔ DTO
- Nie zna szczegółów infrastruktury

### 3. Infrastructure Layer (infrastructure/)
- Zależy od Domain i Application
- Implementuje porty
- Zawiera szczegóły techniczne
- Adaptery do zewnętrznych systemów

## Data Flow (przykład: get_shipment_status)

```
1. MCP Request
   └─> get_shipment_status(order_number="GK123", language="pl")

2. MCP Tool (Infrastructure)
   └─> Creates: GetShipmentStatusQuery(order_number="GK123", language="pl")

3. QueryBus (Application)
   └─> Routes to: GetShipmentStatusQueryHandler

4. QueryHandler (Application)
   ├─> Creates: ShipmentId("GK123")  [Value Object]
   └─> Calls: tracking_port.get_shipment_status(shipment_id, "pl")

5. HttpClient (Infrastructure - implements Port)
   ├─> HTTP GET: /v1/order/tracking?orderNumber=GK123
   ├─> Receives: JSON response
   └─> Maps to: ShipmentStatus [Domain Model]

6. QueryHandler (Application)
   ├─> Receives: ShipmentStatus [Domain Model]
   └─> Maps to: ShipmentStatusDto [DTO]

7. MCP Tool (Infrastructure)
   ├─> Receives: ShipmentStatusDto
   └─> Serializes to: dict

8. MCP Response
   └─> Returns: JSON to client
```

## Bounded Contexts (current + future)

### shipping/ (✅ Implemented)
- **Domain**: ShipmentId, TrackingEvent, ShipmentStatus
- **Ports**: ShipmentTrackingPort
- **Queries**: GetShipmentStatusQuery
- **Adapters**: GlobKurierHttpClient

### pricing/ (Future)
- **Domain**: PriceId, PriceQuote
- **Ports**: PricingCalculatorPort
- **Queries**: CalculateShippingPriceQuery
- **Adapters**: GlobKurierPricingClient

### orders/ (Future)
- **Domain**: Order, OrderId, OrderStatus
- **Ports**: OrderManagementPort
- **Commands**: CreateOrderCommand, CancelOrderCommand
- **Adapters**: GlobKurierOrderClient

## Testing Strategy

### Domain Layer Tests
```python
# Test pure business logic
def test_shipment_is_delivered():
    shipment = ShipmentStatus(status="delivered", ...)
    assert shipment.is_delivered() is True
```

### Application Layer Tests
```python
# Test with mocked ports
@pytest.mark.asyncio
async def test_query_handler(mock_port):
    mock_port.get_status.return_value = domain_model
    handler = QueryHandler(tracking_port=mock_port)
    result = await handler.handle(query)
    # Verify DTO mapping
```

### Infrastructure Layer Tests
```python
# Integration tests
@pytest.mark.asyncio
async def test_http_client_real_api():
    client = GlobKurierHttpClient(settings)
    result = await client.get_shipment_status(...)
    # Verify API integration
```

## Extensibility Examples

### Dodanie nowego adaptera (np. Mock dla testów)

```python
# 1. Port już istnieje w Domain
class ShipmentTrackingPort(ABC):
    ...

# 2. Nowy adapter w Infrastructure
class MockShipmentTrackingClient(ShipmentTrackingPort):
    async def get_shipment_status(...) -> ShipmentStatus:
        return ShipmentStatus(...)  # Mock data

# 3. Wstrzyknij w main.py
tracking_client = MockShipmentTrackingClient()  # Zamiast HttpClient
```

### Dodanie cache'owania

```python
# Infrastructure: Decorator pattern
class CachedShipmentTracking(ShipmentTrackingPort):
    def __init__(self, port: ShipmentTrackingPort, cache: Cache):
        self._port = port
        self._cache = cache

    async def get_shipment_status(...) -> ShipmentStatus:
        cached = await self._cache.get(shipment_id)
        if cached:
            return cached
        result = await self._port.get_shipment_status(...)
        await self._cache.set(shipment_id, result)
        return result

# Wstrzyknij:
http_client = GlobKurierHttpClient(...)
cached_client = CachedShipmentTracking(http_client, redis_cache)
```

## Design Patterns używane

1. **Hexagonal Architecture** - separacja core od infrastruktury
2. **Ports & Adapters** - interfejsy + implementacje
3. **CQRS** - QueryBus, Command/Query separation
4. **Repository Pattern** - (future: DataPort)
5. **Dependency Injection** - main.py wstrzykuje zależności
6. **Factory Pattern** - create_query_bus(), create_mcp_server()
7. **DTO Pattern** - mapowanie między warstwami
8. **Value Object** - ShipmentId, TrackingEvent
9. **Aggregate Root** - ShipmentStatus

## Korzyści architektury

1. **Łatwe testowanie** - mockowanie na poziomie portów
2. **Wymienność adapterów** - HTTP → gRPC bez zmian w core
3. **Niezależność** - domain nie zna infrastruktury
4. **Czytelność** - jasny podział odpowiedzialności
5. **Skalowalność** - łatwe dodawanie bounded contexts
6. **Maintainability** - zmiany w jednej warstwie nie wpływają na inne
