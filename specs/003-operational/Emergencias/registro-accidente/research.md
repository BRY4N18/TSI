# Phase 0 Research — Registro de Accidentes

## Decision 1: Contract-first OpenAPI para endpoints de accidentes

- **Decision:** Definir primero `contracts/registro-accidente.openapi.yaml` con todos los endpoints CU-O21/O32/O40/O41 y RF-REG-010 bajo `/api/v1/accidentes`.
- **Rationale:** Cumple constitution (API-First Compatibility) y alinea backend Django con frontend Angular antes de implementar.
- **Alternatives considered:**
  - Implementar ViewSets y documentar después (rechazado: menor trazabilidad y riesgo de drift spec↔código).
  - Contrato solo en markdown (rechazado: sin validación automática ni tipos generables).

## Decision 2: Django capas Vista → Servicio → Repositorio en `apps/accidentes/`

- **Decision:** DRF APIView/Generic views en `apps/accidentes/views/`; casos de uso en `services/`; acceso Pinot/Kafka en `core/repositories/accidentes/`.
- **Rationale:** Patrón vinculante en `architectural-patterns.md` y consistencia con `cuentas_clientes`.
- **Alternatives considered:**
  - Lógica en serializers/views (rechazado: viola mantenibilidad y testabilidad).
  - App monolítica `emergencias/` (rechazado: `project-structure.md` separa `accidentes/` y `despacho/`).

## Decision 3: Escritura exclusiva vía Kafka (sin INSERT directo a Pinot)

- **Decision:** Toda mutación (`Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente`, puentes climáticas/físicas, `Dim_NotaAccidente`) publica evento al topic Kafka de la tabla correspondiente.
- **Rationale:** Regla vinculante del proyecto; Pinot es solo lectura desde Django.
- **Alternatives considered:**
  - Escritura directa a Pinot para “velocidad” (rechazado: viola arquitectura).
  - Dual-write Pinot+Kafka (rechazado: inconsistencia y complejidad operativa).

## Decision 4: Autenticación JWT + RBAC por rol (dependencia `autenticacion-y-rbac`)

- **Decision:** Endpoints protegidos con `Authorization: Bearer`; permisos DRF por rol canónico `Operador de emergencias` (O21/O32/O41/edición) y `Unidad de emergencia` (O40). Validación JWT + estado de sesión en cada request.
- **Rationale:** Spec y skill `api-authentication`; reutiliza permisos/interceptor ya definidos en Cuentas-Clientes.
- **Alternatives considered:**
  - Solo validación de firma JWT (rechazado: tokens revocados seguirían vigentes).
  - Autorización solo en frontend (rechazado: riesgo de seguridad).

## Decision 5: Proveedor de geocodificación inversa

- **Decision:** Servicio `GeocodificacionInversaService` con adaptador HTTP a **Nominatim (OpenStreetMap)** en backend, con cache TTL corto y timeout 1.5s; resolución de `idcalle` contra dimensiones geográficas en Pinot.
- **Rationale:** Sin vendor lock-in, costo cero para proyecto individual, suficiente para meta RNF-REG-002 (95% urbano / 100m) con validación post-proceso contra `Dim_Calle`.
- **Alternatives considered:**
  - Google Maps Geocoding API (rechazado en esta fase: costo y credenciales adicionales).
  - Geocodificación solo en frontend (rechazado: inconsistente con RF-REG-006 y cobertura operativa server-side).

## Decision 6: Validaciones RF-REG-003 en servicio dedicado con respuesta estructurada

- **Decision:** `ValidacionAccidenteService` ejecuta validaciones síncronas (<2s RNF-REG-005); advertencias en array `advertencias[]`; bloqueos solo para rango GPS global inválido; `forzarAdvertencias=true` en POST permite persistir en BORRADOR.
- **Rationale:** Alinea clarificaciones de promoción condicional BORRADOR→REPORTADO y respuestas 409/422 del spec.
- **Alternatives considered:**
  - Validación asíncrona post-201 (rechazado: operador necesita feedback inmediato en camino crítico).

## Decision 7: Angular — servicios tipados + guards por rol

- **Decision:** `AccidenteApiService` y `GeocodificacionApiService` en `modules/accidentes/services/`; `OperadorEmergenciasGuard` y `UnidadEmergenciaGuard` (o `RoleGuard` parametrizado); rutas lazy `accidentes.routes.ts`.
- **Rationale:** Patrón establecido en auth; componentes sin lógica de dominio (`architectural-patterns.md`).
- **Alternatives considered:**
  - Llamadas HTTP directas en componentes (rechazado).
  - Un solo guard genérico sin separación operador/unidad (rechazado: menor claridad para O40).

## Decision 8: Cobertura operativa vía lectura de regiones en Producción

- **Decision:** `CoberturaOperativaService` consulta `Dim_RegionOperativa` + `Dim_RegionOperativaEstadoRegion` (spec `incorporacion-regional`) para validar `Dim_EstadoRegion` resuelto desde GPS.
- **Rationale:** Clarificación aprobada en spec; evita bounding boxes ad hoc.
- **Alternatives considered:**
  - Lista fija de países (rechazado: no escala multi-región).

## Tie-Breaker (constitution)

- **Conflicto:** Performance Efficiency (validaciones <2s) vs Maintainability (múltiples servicios).
- **Prioridad:** Maintainability (servicios separados por caso de uso) sin sacrificar Safety — validaciones en camino crítico permanecen síncronas con timeout estricto.
- **Safety:** no aplica override; el flujo mantiene fail-safe (registro bloqueado solo por GPS global inválido).
