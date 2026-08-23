# Estrategia de Testing — Tráfico Seguro Integral (TSI)
**Ubicación de este archivo:** `.specify/docs/architecture/testing.md`
**Última actualización:** 2026-07-09

---

## Marco Normativo

Esta documentación es referenciada por la [Constitución del proyecto](/specify/memory/constitution.md) (ISO/IEC 25010:2023, Mantenibilidad → Testabilidad). Define los umbrales concretos, herramientas, y procedimientos de testing del sistema.

**Reglas adicionales vinculantes:**
- Todo caso de uso del camino crítico (registro → validación → asignación unidad → despacho → seguimiento → cierre) debe tener un test de integración.
- No se acepta código sin al menos un test asociado (unitario o de integración).
- Los umbrales de cobertura y latencia documentados aquí son donde los principios de la constitución (III: Real-Time Performance Efficiency, VII: Maintainability) se vuelven criterios medibles concretos.

## Pirámide de Testing

```
         /\
        /E2E\           <-- Playwright: 4 suites en e2e/tests/
       /------\
      /  API   \        <-- pytest + DRF TestClient: ~180 tests
     /----------\
    /  Service   \      <-- pytest + mocks: ~200 tests
   /--------------\
  /  Repositorio   \    <-- pytest + mock Pinot/Kafka: ~120 tests
 /------------------\
/   Unit (servicios) \   <-- pytest + mocks puros: ~200 tests
|----------------------|
```

## Cobertura Objetivo

| Capa | Cobertura mínima | Prioridad |
|------|------------------|-----------|
| Repositorios (`core/repositories/`) | 85% | Crítica |
| Servicios (`apps/*/services/`) | 80% | Alta |
| Vistas/API (`apps/*/views.py`) | 75% | Alta |
| Cadena crítica de despacho | 95% | Crítica |
| Middleware | 70% | Media |
| Frontend — Unitario (componentes, servicios) | ≥ 80% | Alta |
| Frontend — End-to-end (flujos críticos) | Cubrir camino crítico | Alta |
| **Reglas adversariales** (`PG-*`) | Ver `specs/Global/PlanPruebas/traceability.md` | Crítica |
| **Total sistema** | **80%** | Constitucional |

## Stack de Testing

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| `pytest` | >=8.2 | Test runner principal (backend) |
| `pytest-django` | >=4.8 | Integración Django |
| `pytest-cov` | >=5.0 | Cobertura de código |
| `unittest.mock` | stdlib | Mocking de dependencias externas |
| `cryptography` | >=42.0 | Generación de JWT RS256 para tests |
| Jasmine | — | Test runner unitario frontend (Angular) |
| Karma | — | Ejecutor de tests frontend en navegador |
| Playwright | — | Tests end-to-end frontend. **Ya en uso**: `e2e/playwright.config.ts` y 4 suites en `e2e/tests/`. Hasta 2026-08-23 esta tabla decía «Cypress (futuro)», que nunca llegó a usarse |
| Locust / k6 | — | Pruebas de carga y performance de endpoints críticos |

## Marcadores de Tests (markers)

| Marker | Propósito | Duración esperada |
|--------|-----------|-------------------|
| `unit` | Tests rápidos sin dependencias externas | <100ms cada uno |
| `repository` | Tests de repositorio con Pinot/Kafka mockeados | <200ms cada uno |
| `service` | Tests de servicios con repos mockeados | <200ms cada uno |
| `api` | Tests de endpoints REST con DRF TestClient | <500ms cada uno |
| `critical_path` | Tests de la cadena crítica de despacho | <1s cada uno |
| `integration` | Tests con Pinot/Kafka reales (docker-compose) | ~10s cada uno |
| `slow` | Tests que requieren >1s de ejecución | Variable |

## Convenciones de Nomenclatura

```python
# Archivos
test_{modulo}.py          # test_user_repository.py, test_auth_api.py

# Clases
Test{NombreClase}          # TestUserService, TestAccidentAPI

# Métodos
test_{accion}_cuando_{condicion}  # test_create_user_when_duplicate_email_raises
```

## Patrón AAA (Arrange-Act-Assert)

Todos los tests siguen el patrón Arrange-Act-Assert:

```python
def test_find_by_id_when_exists_returns_user(self, mock_pinot):
    # Arrange
    mock_pinot.return_value = [{"idusuario": 1, "nombres": "Test"}]

    # Act
    result = self.repo.find_by_id(1)

    # Assert
    assert result is not None
    assert result["nombres"] == "Test"
```

## Fixtures Compartidas

Definidas en `backend/conftest.py`:

| Fixture | Propósito |
|---------|-----------|
| `mock_pinot` | Parchea `pinot.query()` con MagicMock |
| `mock_kafka` | Parchea `_get_producer()` con MagicMock |
| `mock_redis` | Parchea redis.Redis con dict en memoria |
| `api_client` | DRF APIClient configurado |
| `auth_headers` | Genera JWT RS256 real para autenticación |
| `any_dict` | Matcher para verificar parcialmente dicts |

## Ejecución de Tests

```bash
# Backend — Tests rápidos (unit + mock integration)
pytest -m "not integration"

# Backend — Todos los tests
pytest

# Backend — Reporte de cobertura
pytest --cov --cov-report=html

# Backend — Tests de un módulo específico
pytest apps/cuentas_clientes/tests/ -v

# Backend — Tests del camino crítico
pytest -m critical_path -v

# Backend — Tests de integración real (requiere docker-compose)
pytest -m integration -v

# Frontend — Tests unitarios (Jasmine + Karma)
ng test

# Frontend — Tests end-to-end (Playwright, desde e2e/)
npx playwright test
```

## Thresholds de Rendimiento

| Operación | P95 máximo | Herramienta de medición |
|-----------|------------|------------------------|
| Consulta Pinot simple (SELECT con filtro) | 100ms | PerfTrace en tests |
| Consulta Pinot con JOIN | 300ms | PerfTrace en tests |
| Publicación Kafka (send + flush) | 50ms | Test timing |
| Login completo (JWT + Redis) | 200ms | Test timing |
| Registro de accidente completo | 500ms | Test timing |

## Pruebas de Carga

Además de los thresholds de rendimiento unitarios (PerfTrace), se definen pruebas de carga sobre endpoints críticos usando **Locust** o **k6**:

| Herramienta | Propósito | Threshold |
|-------------|-----------|-----------|
| Locust / k6 | Simulación de carga concurrente sobre la API | Latencia P95 ≤ 100ms en despacho |

Estas pruebas validan el comportamiento del sistema bajo estrés y complementan los micro-benchmarks definidos en los thresholds de rendimiento.

## Integración Continua (Futuro)

Los tests se ejecutarán en GitHub Actions con:
- `pytest -m "unit"` en cada push
- `pytest -m "not integration"` en cada PR
- `pytest` completo pre-deploy
- `pytest -m integration` semanal
- `ng test` en cada push (frontend unitario)
- Reporte de cobertura publicado como artifact

## Glosario

Los términos técnicos y de dominio se centralizan en el [glosario del proyecto](../glossary.md).
