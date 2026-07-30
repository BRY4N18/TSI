# Phase 0 Research — Evidencia en Sitio y Disponibilidad de Unidad

## Decision 1: Contract-first OpenAPI unificado

- **Decision:** Definir primero `contracts/evidencia-unidad.openapi.yaml` con todos los endpoints CU-O27, CU-O30, CU-O43 y **CU-O46** bajo `/api/v1/`.
- **Rationale:** Cumple constitution (API-First Compatibility) y alinea backend Django con frontend Angular antes de implementar; el usuario solicitó explícitamente contract-first.
- **Alternatives considered:**
  - Implementar ViewSets y documentar después (rechazado: drift spec↔código).
  - Dos contratos separados evidencia/disponibilidad (rechazado: un solo spec de feature, un solo artefacto de validación).
  - Contrato separado solo para CU-O46 (rechazado: mismo módulo `evidencia-unidad`).

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
  - **Técnico de campo**, **Unidad de emergencia**, **Administrador** → galería, captura evidencia y **lectura enriquecimiento**.
  - **Técnico de campo**, **Unidad de emergencia** → escritura enriquecimiento CU-O46.
  - **Unidad de emergencia** → solo propia disponibilidad (`/mi-unidad-emergencia/*`).
  - **Administrador** + token servicio despacho → flota completa (`/unidades-emergencia/*`).
  - **Técnico de campo** → HTTP 403 en endpoints de disponibilidad.
- **Rationale:** Clarificaciones Session 2026-07-09 + Session 2026-07-28 (CU-O46) + skill `api-authentication`; reutiliza JWT/interceptor de `autenticacion-y-rbac`.
- **Alternatives considered:**
  - Autorización solo en frontend (rechazado: riesgo de seguridad).
  - API key sin JWT para móvil (rechazado: inconsistente con stack TSI).

## Decision 6: Modelo offline-first en cliente móvil

- **Decision:** Evidencia/enriquecimiento `sincronizado=false` vive en IndexedDB local del dispositivo capturador; PII conductor cifrada (Decision 11); backend solo recibe registros con `sincronizado=true`. Galería/enriquecimiento móvil fusiona local+servidor; API GET solo retorna sincronizados.
- **Rationale:** Clarificación A en spec (RN-EVI-013) + RN-EVI-020/021; simplifica backend y RBAC.
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
  - `EvidenciaApiService`, `DisponibilidadUnidadApiService`, `EnriquecimientoApiService`, `EvidenciaOfflineStoreService` (IndexedDB + cifrado PII)
  - Guards: `EvidenciaGalleryGuard` (también rutas CU-O46), `UnidadEmergenciaDisponibilidadGuard`, `AdministradorFlotaGuard`
  - Tipos estrictos en `models/evidencia-unidad.types.ts` espejo de OpenAPI
- **Rationale:** `angular-architect` + `typescript-expert`; componentes sin lógica de dominio; Decision 12.
- **Alternatives considered:**
  - Un solo servicio monolítico (rechazado: menor testabilidad).
  - Llamadas HTTP en componentes (rechazado: anti-patrón).

## Decision 10: Separación Dim_NotaAccidente escalamiento vs campo

- **Decision:** Mismo topic `Dim_NotaAccidente_topic`; campo `tipo` distingue `escalamiento` (registro-accidente O40) de tipos de campo (RF-EVI-003). Repositorio compartido con filtro por `tipo`.
- **Rationale:** Tabla única en modelo dimensional; evita duplicar infraestructura Kafka.
- **Alternatives considered:**
  - Tabla separada para notas de campo (rechazado: no existe en esquema).

## Decision 11: PII de conductores — cifrado tránsito + reposo + offline (CU-O46 / Principle V)

- **Decision:**
  1. API/sync solo sobre HTTPS/TLS.
  2. PII en Pinot (`Dim_Conductor`, vínculos) reposa bajo cifrado at-rest de infraestructura (volúmenes/backups del cluster); sin stores colaterales en claro.
  3. Borradores offline `LocalConductorAccidente` se cifran en IndexedDB (Web Crypto; clave de sesión); tras sync exitosa se borran (RN-EVI-020/021, RNF-EVI-009).
  4. RBAC estricto + audit de altas/consultas/soft-deletes (RF-EVI-009, T110).
- **Rationale:** Constitution Principle V y tie-breaker dominio (identidad de involucrados): Security prioriza sobre Maintainability; nunca sobre Safety. CU-O46 introduce PII que el módulo evidencia previo (solo fotos/notas) no modelaba igual.
- **Alternatives considered:**
  - Solo TLS sin at-rest/offline crypto (rechazado: viola MUST de Principle V).
  - Prohibir captura offline de conductores (rechazado: reduce Functional Suitability en campo sin cobertura; crypto local es trade-off aceptable).
  - Tokenización/hash de `identificacion` sin texto recuperable (rechazado por ahora: operativo de campo y reutilización RN-EVI-019 requieren valor comparable; revisit si compliance lo exige).

## Decision 12: Guard de rutas enriquecimiento

- **Decision:** Reutilizar `EvidenciaGalleryGuard` (mismos roles RN-EVI-012/016) para rutas de enriquecimiento; no crear `EnriquecimientoCampoGuard` separado.
- **Rationale:** Misma matriz RBAC lectura/escritura que galería; Maintainability (menos duplicación).
- **Alternatives considered:** Guard dedicado (rechazado: drift de permisos).

## Decision 13: `Dim_Implicado` = ontología dimensional (remediación app → Pinot)

- **Decision:** Autoridad = diagrama ER / `database/esquemas.json`: `idimplicado`, `idaccidente`, `tipoimplicado`, `genero`, `estadoimplicado`, `activo`, `edad` (+ `fecha_actualizacion` infra). **No** ampliar Pinot. Remediación = bajar app/spec/OpenAPI/código al modelo oficial.
  - Enums: `tipoimplicado` ∈ {Peaton, Pasajero, Testigo, Otro}; `estadoimplicado` ∈ {Ileso, Lesionado, Fallecido, Desconocido}.
  - Offline `LocalImplicado` sin cifrado PII (no hay PII en esta dimensión).
  - Identidad de personas (cédula/nombres) permanece solo en `Dim_Conductor` (Decision 11 / RF-EVI-009).
- **Rationale:** Evita drift triple (diagrama ≠ Pinot ≠ app). Constitution Maintainability + Compatibility; Security se simplifica al no introducir PII extra en Implicado.
- **Alternatives considered:**
  - Expandir `esquemas.json` al payload PII de la app (rechazado por el usuario / ontología).
  - Mantener dual-write PII+ontología (rechazado: complejidad y campos fantasma en Kafka).

## Tie-Breaker (constitution)

- **Conflicto 1:** Performance Efficiency (RNF-EVI-003 ≤5s reflejo despacho) vs Maintainability (servicios separados evidencia/disponibilidad/blob).
  - **Prioridad:** Maintainability — servicios por caso de uso; lectura de estado optimizada con query Pinot “última fila por unidad” (índice `fechahora`).
  - **Safety:** cambio de disponibilidad impacta despacho; evento Kafka debe publicarse antes de responder 201; lectura posterior por `despacho-inteligente` usa mismo repositorio (consistencia eventual ≤5s alineada a RNF-EVI-003).
- **Conflicto 2 (CU-O46):** Information Security (PII conductor at-rest/offline) vs Maintainability (crypto IndexedDB + ciclo de vida borradores).
  - **Prioridad:** **Security** (excepción de dominio del tie-breaker — identidad de involucrados).
  - **Sacrificado:** simplicidad del offline store; se acepta complejidad Web Crypto y tests de no-persistencia en claro.
  - **Safety no afectada:** enriquecimiento no participa en asignación/despacho.
- **Conflicto 3 (2026-07-29):** Functional Suitability “rica” (PII en implicados) vs ontología dimensional + Maintainability.
  - **Prioridad:** **ontología / Maintainability** (Decision 13) — un solo contrato de datos.
  - **Sacrificado:** captura de cédula/nombres en `Dim_Implicado` (queda fuera de alcance; conductores siguen en RF-EVI-009).
