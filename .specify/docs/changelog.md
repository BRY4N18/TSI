# Changelog fuera de ciclo — cambios de código no originados en `/plan`→`/tasks`

Este documento registra cambios de código aplicados directamente al detectar brechas
entre `spec.md` y el comportamiento real del sistema (vía `/speckit-analyze` extendido),
fuera del flujo normal Spec-Driven. Cada entrada debe quedar reflejada también en el
`traceability.md` de la feature afectada.

---

## 2026-07-15 — Módulo Emergencias (revisión spec vs. implementación)

Alcance: `despacho-inteligente`, `evidencia-unidad`, `registro-accidente`, `seguimiento-cierre-de-casos`

> Nota: el `git status` del repo también mostraba otros archivos modificados/sin trackear que
> **no** correspondían a este trabajo (cambios previos ya en curso antes de esta sesión,
> p. ej. `confirmar_despacho_service.py`, `mi_seguimiento_views.py`, extracción de templates
> `.html`, etc.). Esta entrada solo cubre lo hecho en esa sesión.

### Backend

**G1 (CRITICAL) — Jobs periódicos sin agendar.**
`run_timeout_despacho_job`, `run_gps_senal_perdida_job` y el job de depuración GPS existían
pero nadie los invocaba (no había Celery/APScheduler ni cron configurado). Se agregaron
management commands de Django (patrón `send_onboarding_reminders.py`):
`backend/apps/despacho/management/commands/run_timeout_despacho_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_senal_perdida_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_depuracion_job.py`.
**Pendiente:** decidir invocación en producción (cron, worker separado, Celery beat).

**G2 (HIGH) — Estado de unidad forzado a "Activa" al liberar despacho.**
Al retirar o abortar un despacho, la unidad siempre volvía a `Activa`, ignorando
`Fuera de servicio` (RN-SEG-003 no implementada). Corregido en
`backend/apps/seguimiento/services/retiro_despacho_service.py` y
`backend/apps/seguimiento/services/abortar_mision_service.py` (consultan estado actual
antes de liberar; `cerrar_caso_service.py`/`forzar_retiro_service.py` heredan el fix vía
`RetiroDespachoService`).

**G4 (HIGH) — Mensaje de error genérico en registro de accidente.**
`AccidenteListCreateView.post` respondía siempre `"duplicado_posible"` ante un
`DuplicateConflictError`, aun cuando la advertencia real era `fuera_cobertura`. Corregido
en `backend/apps/accidentes/views/accidente_views.py` (usa `advertencias[0]` real, expone
el arreglo completo).

**G5 (HIGH) — Scoring de "disponibilidad reciente" hardcodeado.**
En `consulta_candidatas_service.py`, el 15% del score de RN-DES-008 era constante
(`disp_score = 0.5`). Se agregó `_disponibilidad_reciente_score()` (score real por tiempo
continuo en estado `Activa`, tope 30 min).

**G6 (MEDIUM) — Selección de accidente "padre" en fusión usa campo incorrecto.**
`ValidacionAccidenteService.suggest_parent_id` usaba `fechahoraaccidente` en vez del
`fechahoramodificado` de la primera transición a `BORRADOR`/`REPORTADO`
(`Fact_AccidenteTipoEstadoAccidente`), per RN-REG-010b. Corregido en
`backend/apps/accidentes/services/validacion_accidente_service.py` (fallback a
`fechahoraaccidente` si no hay historial).

**G9 — Verificado sin cambios.** `registrar_posicion_gps_service.py` sí invoca
`RegistrarLlegadaService` automáticamente vía geofencing (RF-SEG-002) — falso positivo del
análisis previo.

### Frontend

**G3 (HIGH) — Auto-sync de evidencias nunca se activaba.**
`EvidenciaSyncSchedulerService.iniciarAutoSync()` existía pero no se llamaba desde ningún
lado — código muerto. Corregido: nuevo `listarIdsAccidentesPendientes()` en
`evidencia-offline-store.service.ts`; `sincronizarTodosLosCasos()` ahora usa la unión de
casos en sesión + pendientes reales en IndexedDB; `app.component.ts` invoca
`iniciarAutoSync()` en el constructor (corre durante toda la vida de la app).

**Bug preexistente (detectado al verificar G4 en el frontend) — Manejo del conflicto
409 roto.** `registro-accidente.page.ts` leía `err.error` en vez de `err.error.data`
(envoltura `{data, meta}`) y usaba `idaccidente_duplicado_sugerido` (siempre `null`) en
vez de `idaccidente_similar`. Resultado real: el diálogo de "posible duplicado" nunca se
abría y la fusión nunca funcionaba. Corregido en
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`;
se agregó manejo explícito de `error === 'fuera_cobertura'`. Tests actualizados en
`registro-accidente.page.spec.ts`.

### Verificación realizada

- Backend: `pytest apps/despacho apps/accidentes apps/seguimiento` → 285/285 tests.
- Frontend: `tsc --noEmit` (app + spec) sin errores. (Karma/Jasmine no se pudo correr por
  falta de Chrome en el entorno; recomendado correr `ng test` localmente.)
- Docker: `docker compose -f accidentes.yml build` exitoso.

### Pendientes / fuera de alcance

- **G7** — Notificaciones push/SMS en despacho son stubs (`_default_push`/`_default_sms`
  siempre "exitosos"); requiere integración real con un proveedor.
- **G8** — Payload estructurado de alerta crítica hacia monitoreo (RF-DES-008) no
  confirmado a fondo.
- **G10 / T108** — No existe endpoint de reversión (undo) para descarte/fusión de
  accidentes; decisión de alcance pendiente. Ver `registro-accidente/tasks.md` T108.

---

## 2026-07-16 — Regularización de contrato para proxy de ruta OSRM

Alcance: `seguimiento-cierre-de-casos`

El endpoint `GET /api/v1/seguimiento/ruta` (`backend/apps/seguimiento/views/ruta_views.py`,
`core/osrm/client.py`) se implementó junto con el trabajo del 2026-07-15 pero no se agregó
al contrato OpenAPI ni a `tasks.md` en su momento (violación Principio VI — API-First).
Regularizado: contrato agregado en
`contracts/seguimiento-cierre-de-casos.openapi.yaml` (`/seguimiento/ruta`), tarea T042b y
fila CA-SEG-002b en `traceability.md`.
