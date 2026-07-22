# Quickstart - Validación de Alta y Configuración de Unidades de Emergencia

Guía de validación end-to-end contract-first para CU-O54, CU-O56, CU-O57, CU-O58 y CU-O59.

## Prerequisitos

- Contrato: `contracts/alta-unidades.openapi.yaml`
- Spec y plan en `specs/003-operational/Red-Operativa/alta-unidades/`
- Módulo **autenticacion-y-rbac** operativo (login JWT, roles Administrador y Operador de emergencias)
- Un `Dim_Cliente` y un `Dim_Condado` existentes para poblar `idcliente` / `idcondado`
- Migración cruzada de `despacho-inteligente` aplicada (`idcondado` reemplazando `zonacobertura`) — ver `research.md` Decision 8

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | UC | Rol |
|--------|------|-----|-----|
| POST | `/api/v1/red-operativa/unidades` | O54 | Administrador |
| POST | `/api/v1/red-operativa/unidades/importacion-lote` | O56 | Administrador |
| GET | `/api/v1/red-operativa/unidades/{id}` | — | Administrador / Operador |
| PATCH | `/api/v1/red-operativa/unidades/{id}` | O57 | Administrador |
| POST | `/api/v1/red-operativa/unidades/{id}/baja` | O58 | Administrador |
| POST | `/api/v1/red-operativa/unidades/{id}/reactivar` | O58 | Administrador |
| POST | `/api/v1/red-operativa/unidades/{id}/disponibilidad` | O59 | Operador de emergencias |

Convenciones (`api-standards.md`): envelope `{data, meta}` / `{error, detail, code}`; `Idempotency-Key` en todo POST/PATCH de escritura.

**Resultado esperado**: contrato alineado con spec y `data-model.md`, sin `zonacobertura` residual.

## 2) Validar flujo backend (Vista → Servicio → Repositorio)

### Escenario A — Alta individual y duplicado de placa (O54, CA-CAM-001/002)

1. Login como Administrador → JWT.
2. `POST /red-operativa/unidades` con `placa="ABC-123"` → `201`, `activo=true`.
3. Repetir con la misma `placa` → `409 Conflict`.

**Resultado esperado**: unidad visible vía Pinot tras el evento Kafka; segundo intento rechazado antes de publicar evento.

### Escenario B — Importación en lote todo-o-nada (O56, CA-CAM-003)

1. Subir archivo con 50 filas, una con `placa` duplicada.
2. `POST /red-operativa/unidades/importacion-lote` → `200`, `insertadas=0`, `fallidas=[{fila, motivo}]`.
3. Confirmar que ninguna unidad del archivo quedó insertada.

### Escenario C — Edición bloqueada por despacho activo (O57, CA-CAM-004/005)

1. Crear un despacho activo (`Fact_Despacho` sin `fechahoraretiro`) para una unidad — vía módulo `despacho-inteligente`.
2. `PATCH .../{id}` cambiando `tipounidademergencia` sin `confirmar_edicion_critica=true` → `409`.
3. Repetir con `confirmar_edicion_critica=true` → `200`.

### Escenario D — Baja, reactivación y unicidad de placa (O58, CA-CAM-006/007)

1. `POST .../{id}/baja` con `motivo` → `200`, `activo=false`; `Fact_BajaUnidad` poblado.
2. Registrar otra unidad activa con la misma `placa` que la dada de baja.
3. `POST .../{id}/reactivar` sobre la unidad original → `409` (placa ya en uso por otra unidad activa).
4. Dar de baja la segunda unidad y reintentar reactivación de la primera → `200`.

### Escenario E — Disponibilidad externa con alerta (O59, CA-CAM-008/009)

1. Login como Operador de emergencias → JWT.
2. Con un despacho activo sin retirar sobre la unidad, `POST .../{id}/disponibilidad` con `estadonuevo="Activa"` → `422` (alerta, no bloqueo duro).
3. Sin despacho activo, mismo request → `200`; `idusuario` registrado es el del Operador, no el de la unidad.

## 3) Validar migración cruzada de `despacho-inteligente`

1. Confirmar que `unidad_emergencia_repository.py::list_candidatas_por_condado` usa `idcondado` directo (sin cast de `zonacobertura`).
2. Confirmar que `disponibilidad_unidad_service.py::consultar()` expone `idcondado` en vez de `zonacobertura`.
3. Ejecutar la suite de tests existente de `despacho-inteligente` — debe seguir en verde tras la migración.

## 4) Validar frontend (Angular)

1. Login Administrador → navegar a `red-operativa/alta-unidades/catalogo` → alta individual y en lote visibles.
2. `AdministradorRedOperativaGuard` bloquea el acceso a un usuario con rol distinto.
3. Login Operador de emergencias → solo `disponibilidad-externa/` accesible; `OperadorDisponibilidadGuard` bloquea catálogo/edición/baja.
4. Componentes sin lógica de negocio: verificar que validaciones (placa duplicada, confirmación de edición crítica) viven en `UnidadEmergenciaFacadeService`, no en el componente.

## Criterios de éxito

- Los 5 escenarios (A–E) pasan contra el contrato OpenAPI.
- Ningún repositorio de `red_operativa` escribe directo a Pinot (solo vía `KafkaWriter`).
- Tests de `despacho-inteligente` en verde tras la migración de `idcondado`.
- Cobertura de tests backend/frontend según `.specify/docs/architecture/testing.md`.

## Evidencia de performance (ejecutada 2026-07-21)

| Prueba | Umbral | Resultado |
|---|---|---|
| `test_duplicado_placa_p95.py` (RNF-CAM-001) | <1s | ✅ PASS |
| `test_importacion_lote_p95.py` (RNF-CAM-002, 500 filas) | ≤30s | ✅ PASS |

**Suite completa**: `pytest apps/red_operativa -q` → 62/62 en verde. `pytest apps/despacho -q` (post-migración) → 90/90 en verde. Suite global del proyecto: 570/573 (los 3 fallos son un bug preexistente de colisión de `conftest.py` en `apps/cuentas_clientes`, no relacionado con este módulo).

Frontend: sin Chrome/Karma disponibles en el entorno de esta sesión; validado con `tsc --noEmit` (limpio en `tsconfig.app.json` y `tsconfig.spec.json`) y `ng build --configuration=development` (build de producción exitoso, chunk `alta-unidades-routes` generado sin errores).
