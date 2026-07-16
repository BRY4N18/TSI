# Cambios realizados — Módulo Emergencias (revisión spec vs. implementación)

Fecha: 2026-07-15
Alcance: `despacho-inteligente`, `evidencia-unidad`, `registro-accidente`, `seguimiento-cierre-de-casos`

Este documento resume los cambios de código aplicados a partir del análisis (`/speckit-analyze` extendido) que comparó `spec.md` de cada sub-feature contra el comportamiento real del sistema, no solo contra el contrato OpenAPI o `tasks.md`.

> Nota: el `git status` del repo también muestra otros archivos modificados/sin trackear que **no** corresponden a este trabajo (cambios previos ya en curso antes de esta sesión, p. ej. `confirmar_despacho_service.py`, `mi_seguimiento_views.py`, extracción de templates `.html`, etc.). Este documento solo cubre lo hecho en esta sesión.

---

## 1. Backend

### 1.1 Jobs periódicos sin agendar (G1 — CRITICAL)
**Problema:** `run_timeout_despacho_job`, `run_gps_senal_perdida_job` y el job de depuración GPS existían pero nadie los invocaba (no había Celery/APScheduler ni cron configurado).

**Cambio:** se agregaron management commands de Django, siguiendo el patrón ya usado en `apps/cuentas_clientes/management/commands/send_onboarding_reminders.py`:

- `backend/apps/despacho/management/commands/run_timeout_despacho_job.py` — soporta `--once` (para cron externo) o loop continuo (`--interval`, default 30s).
- `backend/apps/seguimiento/management/commands/run_gps_senal_perdida_job.py` — mismo patrón, default 30s.
- `backend/apps/seguimiento/management/commands/run_gps_depuracion_job.py` — ejecución única por defecto, o `--loop` (default 24h).

**Pendiente para el usuario:** decidir cómo se invocan en producción/despliegue (cron, un contenedor worker separado, Celery beat, etc.). El código ya soporta ambos modos.

### 1.2 Estado de unidad forzado a "Activa" al liberar despacho (G2 — HIGH)
**Problema:** al retirar (`RetiroDespachoService.retirar`) o abortar (`AbortarMisionService.abortar`) un despacho, la unidad siempre volvía a estado `Activa`, aunque hubiera estado `Fuera de servicio` antes/durante la misión (RN-SEG-003 no implementada).

**Cambio:**
- `backend/apps/seguimiento/services/retiro_despacho_service.py`
- `backend/apps/seguimiento/services/abortar_mision_service.py`

Ambos ahora consultan el estado actual de la unidad antes de liberar el despacho: si ya estaba `Fuera de servicio`, se preserva ese estado; si no, se restaura a `Activa` (comportamiento anterior). `cerrar_caso_service.py` y `forzar_retiro_service.py` reutilizan `RetiroDespachoService`, así que quedan cubiertos automáticamente.

### 1.3 Mensaje de error genérico en registro de accidente (G4 — HIGH)
**Problema:** `AccidenteListCreateView.post` en `accidente_views.py` respondía siempre `"error": "duplicado_posible"` ante un `DuplicateConflictError`, incluso cuando la única advertencia real era `fuera_cobertura` (fuera de área operativa). El operador nunca veía el motivo real.

**Cambio:** `backend/apps/accidentes/views/accidente_views.py` — la respuesta 409 ahora usa el código/detalle de la primera advertencia real (`validation.advertencias[0]`) y expone el arreglo completo `advertencias` en el body.

### 1.4 Scoring de "disponibilidad reciente" hardcodeado (G5 — HIGH)
**Problema:** en `consulta_candidatas_service.py`, el 15% del score correspondiente a RN-DES-008 ("disponibilidad reciente") era una constante fija `disp_score = 0.5` para todas las candidatas — no reflejaba nada real.

**Cambio:** `backend/apps/despacho/services/consulta_candidatas_service.py` — se agregó `_disponibilidad_reciente_score()`, que calcula el score en base al tiempo continuo que la unidad lleva en estado `Activa` (usando el timestamp que ya devuelve `get_current_estado`), con un tope de 30 minutos para alcanzar el score máximo (constante `DISPONIBILIDAD_MAX_MINUTOS`).

### 1.5 Selección de accidente "padre" en fusión usa campo incorrecto (G6 — MEDIUM)
**Problema:** `ValidacionAccidenteService.suggest_parent_id` elegía el candidato más antiguo por `fechahoraaccidente` (hora del suceso), pero el spec (RN-REG-010b) exige usar el `fechahoramodificado` de la primera transición a `BORRADOR`/`REPORTADO` en `Fact_AccidenteTipoEstadoAccidente`.

**Cambio:** `backend/apps/accidentes/services/validacion_accidente_service.py` — ahora consulta `EstadoAccidenteRepository.get_history()` por cada candidato y usa el primer `fechahoramodificado` en estado `BORRADOR`/`REPORTADO`; si no hay historial, cae de vuelta a `fechahoraaccidente` como fallback.

### 1.6 Verificado sin cambios (G9)
Se confirmó que `registrar_posicion_gps_service.py` sí invoca automáticamente `RegistrarLlegadaService` cuando el geofencing detecta llegada (RF-SEG-002) — era un falso positivo del análisis previo, no requirió cambios.

---

## 2. Frontend

### 2.1 Auto-sync de evidencias nunca se activaba (G3 — HIGH)
**Problema:** `EvidenciaSyncSchedulerService.iniciarAutoSync()` existía pero no se llamaba desde ningún lado de la app — código muerto. La sincronización solo ocurría si el usuario abría manualmente la galería de un caso ya visitado en la sesión.

**Cambio:**
- `frontend/src/app/modules/evidencia-unidad/services/evidencia-offline-store.service.ts` — nuevo método `listarIdsAccidentesPendientes()` que recorre toda la IndexedDB (no solo un caso puntual) para encontrar accidentes con fotos/notas pendientes de sincronizar.
- `frontend/src/app/modules/evidencia-unidad/services/evidencia-sync-scheduler.service.ts` — `sincronizarTodosLosCasos()` ahora usa la unión de casos monitoreados en sesión + los pendientes reales en IndexedDB; se agregó guard `autoSyncIniciado` y sincronización inmediata si ya hay conexión al iniciar.
- `frontend/src/app/app.component.ts` — se inyecta `EvidenciaSyncSchedulerService` y se llama `iniciarAutoSync()` en el constructor, para que corra durante toda la vida de la app y no solo dentro de la página de galería.

### 2.2 Manejo del conflicto de duplicado/fuera de cobertura roto (bug preexistente detectado al verificar conexión con el backend)
**Problema (no estaba en el listado original, se detectó al revisar si el fix 1.3 llegaba bien al frontend):** en `registro-accidente.page.ts`, el manejador de error 409 leía `err.error` en vez de `err.error.data` (el backend envuelve la respuesta en `{data, meta}`), y usaba el campo `idaccidente_duplicado_sugerido` — que el backend **siempre** manda `null` al crear un accidente — tanto para decidir si abrir el diálogo de fusión como para el argumento del endpoint `/fusionar`. Resultado real: **el diálogo de "posible duplicado" nunca se abría y la fusión nunca funcionaba**, ni para duplicados genuinos.

**Cambio:** `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`
- Se lee correctamente `err.error?.data`.
- Se usa `idaccidente_similar` (el campo que sí viene poblado) para abrir el diálogo y como argumento de `fusionar()`.
- Se agregó manejo explícito para `error === 'fuera_cobertura'`, mostrando el mensaje real en vez del genérico "No se pudo registrar el accidente".

**Tests actualizados:** `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.spec.ts` — se corrigió el shape mockeado del error 409 (envuelto en `data`) y los valores de `idaccidente_similar` / `idaccidente_duplicado_sugerido`; se agregó un test nuevo para el caso `fuera_cobertura`.

---

## 3. Verificación realizada

- Backend: `python -m pytest apps/despacho`, `apps/accidentes`, `apps/seguimiento` → **285/285 tests pasan** (89 + 116 + 80).
- Frontend: `npx tsc -p tsconfig.app.json --noEmit` y `npx tsc -p tsconfig.spec.json --noEmit` → compilan sin errores. (No fue posible correr Karma/Jasmine en este entorno por falta de binario Chrome; se recomienda correr `ng test` localmente antes de dar por cerrado el cambio.)
- Docker: `docker compose -f accidentes.yml build` → build exitoso de `accidentes-django` y `accidentes-frontend` (solo warnings de lint de Angular, sin errores).

---

## 4. Pendientes / fuera de alcance de esta ronda

Estos hallazgos del análisis original **no se tocaron** porque requieren decisión de producto o infraestructura externa:

- **G7** — Notificaciones push/SMS en despacho son stubs (`_default_push`/`_default_sms` siempre "exitosos"); requiere integración real con un proveedor.
- **G8** — Payload estructurado de alerta crítica hacia monitoreo (RF-DES-008) no confirmado a fondo.
- **G10 / T108** — No existe endpoint de reversión (undo) para descarte/fusión de accidentes; decisión de alcance pendiente.
