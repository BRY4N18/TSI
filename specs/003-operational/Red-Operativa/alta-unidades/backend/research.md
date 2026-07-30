# Phase 0 Research - Alta y Configuración de Unidades de Emergencia

**Delta 2026-07-24 / mapa 2026-07-29:** actor **Proveedor**; CU-O59 eliminado (disponibilidad → CU-O30); ver `flujoscorreguidos/flujo-red-operativa-canonico.md`.

## Decision 1: Contract-first con OpenAPI para endpoints de unidades

- Decision: Definir primero contrato OpenAPI 3.0 en `contracts/alta-unidades.openapi.yaml` para todos los endpoints bajo `/api/v1/red-operativa/unidades/...`.
- Rationale: Cumple API-first (`api-standards.md`) y permite generar/validar tipos TypeScript y tests de contrato antes de implementar vistas DRF, consistente con `gestion-cuentas` y `registro-accidente` ya implementados.
- Alternatives considered:
  - Implementar vistas DRF primero y documentar después (rechazado: alto riesgo de desalineación frontend/backend).

## Decision 2: Endpoints REST y semántica HTTP

- Decision:
  - `GET /red-operativa/unidades` — listado de flota propia (catálogo FE).
  - `POST /red-operativa/unidades` — CU-O54, alta individual (`Idempotency-Key`); actor Proveedor; `idcliente` desde JWT.
  - `POST /red-operativa/unidades/importacion-lote` — CU-O56, todo-o-nada unidades + credenciales + liga `idusuario` (`Idempotency-Key`).
  - `GET /red-operativa/unidades/{idunidademergencia}` — detalle (solo flota propia).
  - `PATCH /red-operativa/unidades/{idunidademergencia}` — CU-O57, edición parcial.
  - `POST /red-operativa/unidades/{idunidademergencia}/baja` — CU-O58 (`Idempotency-Key`).
  - `POST /red-operativa/unidades/{idunidademergencia}/reactivar` — CU-O58, valida unicidad de placa (`Idempotency-Key`).
  - ~~`POST .../disponibilidad` (CU-O59)~~ — **retirado**; usar CU-O30 en `evidencia-unidad`.
- Rationale: PATCH para edición parcial; POST + `Idempotency-Key` en escrituras de estado; reactivación como endpoint propio por validación de placa.
- Alternatives considered:
  - PUT para reemplazo completo (rechazado: subconjunto editable; `idunidademergencia`/`idcliente` inmutables).
  - Reactivación como `PATCH {activo: true}` (rechazado: oculta validación de unicidad de placa).
  - Mantener O59 Operador-sin-login (rechazado Session 2026-07-24).

## Decision 3: Django por capas (Vista → Servicio → Repositorio) + Kafka-only-write

- Decision:
  - **Vista**: DRF `APIView` en `apps/red_operativa/views/unidad_views.py`.
  - **Servicio**: `RegistroUnidadService` (CU-O54), `ImportacionLoteUnidadService` (CU-O56 + credenciales), `EdicionUnidadService` (CU-O57), `BajaUnidadService` (CU-O58 + reactivación). **Sin** `DisponibilidadExternaService`.
  - **Repositorio** (`core/repositories/red_operativa/`): `UnidadEmergenciaRepository` (escritura + `find_by_placa_activa`), `BajaUnidadRepository`, `DespachoActivoReadRepository` (lectura `Fact_Despacho`). Historial de estado lo escribe **CU-O30**, no este módulo.
  - **Escritura**: `KafkaWriter.publish()` a `Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic` (+ topics de cuenta en O56: usuarios/credenciales/roles).
- Rationale: Regla vinculante de `architectural-patterns.md`; repositorios de lectura de `Dim_UnidadEmergencia` ya existen en despacho/seguimiento — este spec aporta escritura.
- Alternatives considered:
  - Extender el repo de solo-lectura de `despacho/` para escribir (rechazado: mezcla dominios).

## Decision 4: Autenticación JWT + autorización Proveedor

- Decision:
  - Todos los endpoints: `Authorization: Bearer <JWT>` (`IsAuthenticated401`).
  - `IsProveedorFlota`: CU-O54/O56/O57/O58 — ownership por `idcliente` del token; sin override Administrador (RN-CAM-002 / Session 2026-07-24).
- Rationale: Modelo Proveedor; el Admin global no muta flotas de terceros.
- Alternatives considered:
  - `IsAdministradorRedOperativa` para CRUD de unidades (rechazado 2026-07-24; ese permiso queda para **incorporacion-regional**).
  - Permission class genérica por lista de roles (rechazado: menos legible).

## Decision 5: Importación en lote — todo-o-nada (unidades + logins)

- Decision: `ImportacionLoteUnidadService` valida todas las filas en memoria (unidad + viabilidad de `gmail`/credencial, máx. 500) antes de cualquier escritura; si alguna falla → `insertadas: 0`. Si todas pasan: por fila INSERT unidad + `Dim_Usuarios` + `Dim_Credencial` + rol unidad + invitación correo.
- Rationale: RF-CAM-002 / RN-CAM-007; RNF-CAM-002 (<30s / 500 filas).
- Alternatives considered:
  - Compensación Kafka fila a fila (rechazado: complejidad; validación previa basta).
  - Crear unidades sin login en lote (rechazado Session 2026-07-24).

## Decision 6: Concurrencia en edición — last-write-wins

- Decision: `EdicionUnidadService` sin bloqueo optimista; última escritura gana.
- Rationale: Clarificación 2026-07-21 (actor actualizado a Proveedor en 2026-07-24).
- Alternatives considered: ETag / versionado (rechazado por clarify).

## Decision 7: Bloqueo por despacho activo (RF-CAM-003, RF-CAM-004)

- Decision: `DespachoActivoReadRepository.has_despacho_activo(idunidademergencia)` lee `Fact_Despacho` en tiempo real. `EdicionUnidadService` y `BajaUnidadService` lo consultan antes de cambios críticos.
- Rationale: Validación en tiempo real; lectura cross-módulo vía `core/`.
- Alternatives considered: cache local de eventos (rechazado: staleness).

## Decision 8: Migración `zonacobertura` → `idcondado`

- Decision: `Dim_UnidadEmergencia.idcondado` (FK `Dim_Condado`) reemplaza `zonacobertura`. Actualizar consumidores en `despacho-inteligente` y `evidencia-unidad` (repo, servicios, OpenAPI, FE).
- Rationale: Clarificación aprobada; filtro de candidatas por condado no puede vivir en texto libre.
- Alternatives considered: mantener ambos campos (rechazado: doble fuente de verdad).

## Decision 9: Angular — API tipada + `ProveedorFlotaGuard`

- Decision:
  - `UnidadEmergenciaApiService` 1:1 con OpenAPI; tipos en `models/unidad-emergencia.contract.ts`.
  - `ProveedorFlotaGuard` protege catálogo / edición / baja (sin página de disponibilidad externa).
  - Standalone OnPush; lógica en `UnidadEmergenciaFacadeService`.
- Rationale: angular-architect; alineado a actor Proveedor.
- Alternatives considered:
  - `AdministradorRedOperativaGuard` + `OperadorDisponibilidadGuard` para O59 (obsoleto post-2026-07-24).
