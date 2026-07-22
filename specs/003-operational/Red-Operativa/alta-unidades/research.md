# Phase 0 Research - Alta y Configuración de Unidades de Emergencia

## Decision 1: Contract-first con OpenAPI para endpoints de unidades

- Decision: Definir primero contrato OpenAPI 3.0 en `contracts/alta-unidades.openapi.yaml` para todos los endpoints bajo `/api/v1/red-operativa/unidades/...`.
- Rationale: Cumple API-first (`api-standards.md`) y permite generar/validar tipos TypeScript y tests de contrato antes de implementar vistas DRF, consistente con `gestion-cuentas` y `registro-accidente` ya implementados.
- Alternatives considered:
  - Implementar vistas DRF primero y documentar después (rechazado: alto riesgo de desalineación frontend/backend, ya evitado en los otros 8 specs implementados).

## Decision 2: Endpoints REST y semántica HTTP

- Decision:
  - `POST /red-operativa/unidades` — CU-O54, alta individual (`Idempotency-Key`).
  - `POST /red-operativa/unidades/importacion-lote` — CU-O56, todo-o-nada (`Idempotency-Key`).
  - `GET /red-operativa/unidades/{idunidademergencia}` — lectura de detalle.
  - `PATCH /red-operativa/unidades/{idunidademergencia}` — CU-O57, edición parcial.
  - `POST /red-operativa/unidades/{idunidademergencia}/baja` — CU-O58 (`Idempotency-Key`).
  - `POST /red-operativa/unidades/{idunidademergencia}/reactivar` — CU-O58, valida unicidad de placa antes de escribir (`Idempotency-Key`).
  - `POST /red-operativa/unidades/{idunidademergencia}/disponibilidad` — CU-O59, rol Operador.
- Rationale: PATCH para edición parcial (spec define campos editables específicos, no reemplazo completo); POST + `Idempotency-Key` en toda escritura de estado según `api-standards.md`; reactivación como endpoint propio (no `PATCH activo=true`) porque tiene su propia validación de negocio (unicidad de placa) y no es una edición de campo simple.
- Alternatives considered:
  - PUT para reemplazo completo de unidad (rechazado: spec define un subconjunto explícito de campos editables, `idunidademergencia`/`idcliente` inmutables).
  - Reactivación como `PATCH {activo: true}` genérico (rechazado: oculta la validación de unicidad de placa como efecto secundario no evidente en el contrato).

## Decision 3: Django por capas (Vista → Servicio → Repositorio) + Kafka-only-write

- Decision:
  - **Vista**: DRF `APIView` por operación, un archivo `unidad_views.py` en `apps/red_operativa/views/`.
  - **Servicio**: un servicio por caso de uso — `RegistroUnidadService` (CU-O54, reutilizado por CU-O56 fila a fila), `ImportacionLoteUnidadService` (CU-O56, orquesta validación todo-o-nada), `EdicionUnidadService` (CU-O57), `BajaUnidadService` (CU-O58, incluye reactivación), `DisponibilidadExternaService` (CU-O59).
  - **Repositorio** (`core/repositories/red_operativa/`): `UnidadEmergenciaRepository` (escritura — CRUD + `find_by_placa_activa`), `BajaUnidadRepository`, `HistorialEstadoUnidadRepository`, `DespachoActivoReadRepository` (SELECT de solo lectura contra `Fact_Despacho`, módulo Emergencias).
  - **Escritura**: `KafkaWriter.publish()` a `Dim_UnidadEmergencia_topic`, `Fact_BajaUnidad_topic`, `Fact_HistorialEstadoUnidad_topic`.
- Rationale: Regla vinculante de `architectural-patterns.md`; mismo patrón que `despacho-inteligente` y `evidencia-unidad`, que ya tienen repositorios de **lectura** para `Dim_UnidadEmergencia` en `core/repositories/despacho/` y `core/repositories/seguimiento/` — este spec añade el repositorio de **escritura**, que hoy no existe en ningún módulo.
- Alternatives considered:
  - Reutilizar/extender el repositorio de solo-lectura existente en `core/repositories/despacho/unidad_emergencia_repository.py` para también escribir (rechazado: ese repositorio pertenece al dominio de lectura de `despacho`; mezclar escritura ahí viola la regla de "ningún import directo entre apps de distinto módulo de negocio" de `architectural-patterns.md` — `red_operativa` necesita su propio repositorio de escritura en `core/repositories/red_operativa/`).

## Decision 4: Autenticación JWT + autorización por rol

- Decision:
  - Todos los endpoints requieren `Authorization: Bearer <JWT>` (`IsAuthenticated401`, reutilizado de `core/auth`).
  - `IsAdministradorRedOperativa`: exclusivo para CU-O54, O56, O57, O58 (alta, lote, edición, baja, reactivación) — RN-CAM-002.
  - `IsOperadorDisponibilidadExterna`: exclusivo para CU-O59 — mismo patrón que `IsOperadorDespacho` en `apps/despacho/permissions.py`.
- Rationale: Alineado con api-authentication (JWT stateless + verificación de rol) y RN-CAM-002; reutiliza el patrón de permisos por clase ya validado en `despacho/permissions.py` (`IsAdministradorOrDespachoService`, `IsOperadorDespacho`).
- Alternatives considered:
  - Un único permission class con lista de roles permitidos por vista (rechazado: menos legible que clases dedicadas, y el resto del proyecto ya usa el patrón de clases específicas).

## Decision 5: Importación en lote — todo-o-nada con reporte fila por fila

- Decision: `ImportacionLoteUnidadService` valida las 500 filas máximo en memoria (mismas reglas que `RegistroUnidadService`, incluyendo duplicado de placa dentro del propio archivo) antes de ejecutar cualquier escritura; si todas pasan, publica un evento Kafka por unidad (batch de eventos, no una sola transacción de tabla — no hay transacciones ACID multi-fila en el modelo Kafka→Pinot).
- Rationale: RF-CAM-002 exige todo-o-nada; RNF-CAM-002 exige reporte fila por fila en <30s para 500 filas — validar todo en memoria antes de publicar el primer evento evita estados parciales.
- Alternatives considered:
  - Publicar eventos fila por fila y revertir con eventos de compensación si falla una fila tardía (rechazado: mayor complejidad, Kafka no soporta rollback nativo; la validación completa en memoria antes de publicar es más simple y cumple el mismo contrato).

## Decision 6: Concurrencia en edición — last-write-wins

- Decision: `EdicionUnidadService` no implementa bloqueo optimista ni control de versión; la última escritura recibida sobrescribe el estado anterior en Kafka/Pinot.
- Rationale: Clarificación aprobada (2026-07-21); consistente con el patrón ya usado en los demás módulos administrativos de bajo volumen de escritura concurrente (`gestion-cuentas`).
- Alternatives considered:
  - ETag / optimistic locking con campo de versión (rechazado por clarificación: complejidad no solicitada para este volumen de uso).

## Decision 7: Bloqueo por despacho activo (RF-CAM-003, RF-CAM-004)

- Decision: `DespachoActivoReadRepository.has_despacho_activo(idunidademergencia)` ejecuta un `SELECT` de solo lectura contra `Fact_Despacho` (módulo Emergencias, `despacho-inteligente`) en tiempo real, sin tabla ni cache propios. `EdicionUnidadService` y `BajaUnidadService` lo consultan antes de aplicar cambios críticos.
- Rationale: RF-CAM-003/004 exigen validación en tiempo real, no un snapshot; `architectural-patterns.md` permite lectura cross-módulo vía repositorios en `core/`, igual que `region_operativa_repository.py` ya lee `Dim_RegionOperativa` desde `accidentes/`.
- Alternatives considered:
  - Suscribirse a eventos de `Fact_Despacho` y mantener un flag local (rechazado: introduce staleness — RF-CAM-003 exige el estado real al momento de la edición, no una copia con delay).

## Decision 8: Migración `zonacobertura` → `idcondado` en `despacho-inteligente`

- Decision: `Dim_UnidadEmergencia.idcondado` (FK real a `Dim_Condado`) reemplaza a `zonacobertura` (texto libre). Se actualiza el módulo ya implementado `despacho-inteligente`:
  - `spec.md` (líneas que documentan `zonacobertura` en el esquema y en el criterio de filtro por condado) y `data-model.md` pasan a referenciar `idcondado`.
  - `core/repositories/despacho/unidad_emergencia_repository.py::list_candidatas_por_condado` deja de castear `zonacobertura` a int y usa `row.get("idcondado")` directamente, sin fallback.
  - `apps/despacho/services/disponibilidad_unidad_service.py` deja de exponer `zonacobertura` en la respuesta de `consultar()`/`consultar_por_usuario()` (CU-O30) y expone `idcondado`.
- Rationale: Clarificación aprobada — `zonacobertura` no era un campo huérfano sino el único mecanismo real (aunque frágil) para resolver candidatas por condado hoy; dejarlo sin reemplazo real rompería el despacho. La migración se ejecuta en el mismo ciclo que `alta-unidades` porque ambos specs comparten la tabla física `Dim_UnidadEmergencia` y quedarían inconsistentes si se separan en el tiempo.
- Alternatives considered:
  - Mantener `zonacobertura` indefinidamente junto a `idcondado` (rechazado: duplica la fuente de verdad geográfica y perpetúa el cast de texto frágil que se buscaba eliminar).
  - Posponer la migración de `despacho-inteligente` a un spec/PR separado sin fecha (rechazado: ventana de inconsistencia entre specs sin tracking formal — mismo antipatrón que motivó la clarificación).

## Decision 9: Angular — servicios tipados y guards por rol

- Decision:
  - `UnidadEmergenciaApiService`: métodos 1:1 con operaciones OpenAPI; tipos en `models/unidad-emergencia.contract.ts`.
  - `AdministradorRedOperativaGuard`: protege alta, lote, edición, baja, reactivación.
  - `OperadorDisponibilidadGuard`: protege la página de disponibilidad externa (CU-O59).
  - Componentes standalone OnPush; lógica en `UnidadEmergenciaFacadeService`, no en templates.
- Rationale: angular-architect + typescript-expert; separación presentación/lógica de `architectural-patterns.md`; mismo patrón que guards de `gestion-cuentas` (`AdminLocalGuard`, `CuentaScopeGuard`).
- Alternatives considered:
  - Un guard único por rol genérico (`RoleGuard` parametrizado) reutilizado sin especializar (rechazado por ahora: el resto del proyecto usa guards nombrados por caso de uso, más legibles bajo presión operativa — Principio IV de la constitution).
