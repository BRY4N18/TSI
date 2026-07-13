# Phase 0 Research — Evidencia en Sitio y Disponibilidad de Unidad

## Decision 1: Contract-first OpenAPI unificado

- **Decision:** Definir primero `contracts/evidencia-unidad.openapi.yaml` con todos los endpoints CU-O27, CU-O30 y CU-O43 bajo `/api/v1/`.
- **Rationale:** Cumple constitution (API-First Compatibility) y alinea backend Django con frontend Angular antes de implementar; el usuario solicitó explícitamente contract-first.
- **Alternatives considered:**
  - Implementar ViewSets y documentar después (rechazado: drift spec↔código).
  - Dos contratos separados evidencia/disponibilidad (rechazado: un solo spec de feature, un solo artefacto de validación).

## Decision 2: Backend en capas Vista → Servicio → Repositorio

- **Decision:** DRF APIViews en `apps/accidentes/views/evidencia_*` y `apps/despacho/views/disponibilidad_*`; servicios de dominio en cada app; repositorios Pinot/Kafka en `core/repositories/evidencia/` y `core/repositories/despacho/`.
- **Rationale:** Patrón vinculante en `architectural-patterns.md`; extiende apps Emergencias existentes sin crear app huérfana.
- **Alternatives considered:**
  - Nueva app `evidencia_unidad/` (rechazado en esta fase: `project-structure.md` ya define `accidentes/` + `despacho/`; evidencia pertenece al caso, disponibilidad a la flota).
  - Lógica en serializers/views (rechazado: viola mantenibilidad).

## Decision 3: Escritura exclusiva vía Kafka (sin INSERT directo a Pinot)

- **Decision:** Mutaciones en `Dim_EvidenciaFoto`, `Dim_NotaAccidente` (notas de campo) y `Fact_HistorialEstadoUnidad` publican evento al topic Kafka `{Tabla}_topic`.
- **Rationale:** Regla vinculante del proyecto; Pinot es solo lectura desde Django.
- **Alternatives considered:**
  - Escritura directa a Pinot (rechazado: viola arquitectura).
  - Dual-write Blob+Kafka sin orden (rechazado: inconsistencia si Blob falla tras Kafka).

## Decision 4: Azure Blob Storage para binarios fotográficos

- **Decision:** `BlobStorageService` sube JPEG/PNG comprimidos (≤10 MB) antes de publicar evento Kafka con `urlevidenciafoto`. Orden: Blob exitoso → Kafka INSERT metadata.
- **Rationale:** `infrastructure.md` sección 3; Pinot/Kafka nunca almacenan binarios.
- **Alternatives considered:**
  - Base64 en evento Kafka (rechazado: payload excesivo, anti-patrón).
  - Almacenar binario en Pinot (rechazado: arquitectura).

## Decision 5: Autenticación JWT + RBAC por rol

- **Decision:** Endpoints protegidos con `Authorization: Bearer`; permisos DRF:
  - **Técnico de campo**, **Unidad de emergencia**, **Administrador** → galería y captura evidencia.
  - **Unidad de emergencia** → solo propia disponibilidad (`/mi-unidad-emergencia/*`).
  - **Administrador** + token servicio despacho → flota completa (`/unidades-emergencia/*`).
  - **Técnico de campo** → HTTP 403 en endpoints de disponibilidad.
- **Rationale:** Clarificaciones Session 2026-07-09 + skill `api-authentication`; reutiliza JWT/interceptor de `autenticacion-y-rbac`.
- **Alternatives considered:**
  - Autorización solo en frontend (rechazado: riesgo de seguridad).
  - API key sin JWT para móvil (rechazado: inconsistente con stack TSI).

## Decision 6: Modelo offline-first en cliente móvil

- **Decision:** Evidencia `sincronizado=false` vive en IndexedDB/SQLite local del dispositivo capturador; backend solo recibe registros con `sincronizado=true`. Galería móvil fusiona local+servidor en el servicio Angular; API GET solo retorna sincronizados.
- **Rationale:** Clarificación A en spec (RN-EVI-013); simplifica backend y RBAC.
- **Alternatives considered:**
  - Registros `sincronizado=false` en Pinot (rechazado: contradice clarificación).
  - Sync todo-o-nada transaccional (rechazado: clarificación A — sync parcial con reintento).

## Decision 7: Sincronización diferida con resultado parcial

- **Decision:** `POST .../evidencias/sincronizar` procesa batch item a item; exitosos persisten (Blob+Kafka); fallidos retornan en `resultados[]` con `sincronizado=false` y `error`; cliente reintenta en siguiente ciclo.
- **Rationale:** Clarificación A (RN-EVI-014); cumple RNF-EVI-004 sin bloquear batch.
- **Alternatives considered:**
  - Transacción todo-o-nada (rechazado: spec).
  - Descartar fallidos (rechazado: pérdida de evidencia).

## Decision 8: Estado por defecto sin historial

- **Decision:** `DisponibilidadUnidadService.resolve_current_state()` retorna `Fuera de servicio` + `incluido_en_despacho=false` cuando no hay filas en `Fact_HistorialEstadoUnidad`.
- **Rationale:** Clarificación CA-EVI-002; fail-safe para despacho.
- **Alternatives considered:**
  - Activa por defecto (rechazado: riesgo Safety).
  - Error 404 (rechazado: spec).

## Decision 9: Angular — servicios tipados + guards por rol

- **Decision:** Módulo `evidencia-unidad/` con:
  - `EvidenciaApiService`, `DisponibilidadUnidadApiService`, `EvidenciaOfflineStoreService` (IndexedDB)
  - Guards: `EvidenciaGalleryGuard`, `UnidadEmergenciaDisponibilidadGuard`, `AdministradorFlotaGuard`
  - Tipos estrictos en `models/evidencia-unidad.types.ts` espejo de OpenAPI
- **Rationale:** `angular-architect` + `typescript-expert`; componentes sin lógica de dominio.
- **Alternatives considered:**
  - Un solo servicio monolítico (rechazado: menor testabilidad).
  - Llamadas HTTP en componentes (rechazado: anti-patrón).

## Decision 10: Separación Dim_NotaAccidente escalamiento vs campo

- **Decision:** Mismo topic `Dim_NotaAccidente_topic`; campo `tipo` distingue `escalamiento` (registro-accidente O40) de tipos de campo (RF-EVI-003). Repositorio compartido con filtro por `tipo`.
- **Rationale:** Tabla única en modelo dimensional; evita duplicar infraestructura Kafka.
- **Alternatives considered:**
  - Tabla separada para notas de campo (rechazado: no existe en esquema).

## Tie-Breaker (constitution)

- **Conflicto:** Performance Efficiency (RNF-EVI-003 ≤5s reflejo despacho) vs Maintainability (servicios separados evidencia/disponibilidad/blob).
- **Prioridad:** Maintainability — servicios por caso de uso; lectura de estado optimizada con query Pinot “última fila por unidad” (índice `fechahora`).
- **Safety:** cambio de disponibilidad impacta despacho; evento Kafka debe publicarse antes de responder 201; lectura posterior por `despacho-inteligente` usa mismo repositorio (consistencia eventual ≤5s alineada a RNF-EVI-003).
