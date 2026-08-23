# Trazabilidad: Plan Global de Pruebas y Validación

> **Generado contando el `spec.md` — no editar a mano.** Una tabla de trazabilidad escrita a mano
> se desincroniza del plan en la primera actualización y pasa a afirmar cobertura que no existe:
> el fallo exacto que este plan existe para detectar. Ya ocurrió con la tabla de cobertura del
> propio `spec.md` (2026-08-23). Regenerar con el script del scratchpad tras cada cambio de estado.

**Fuente:** [`spec.md`](spec.md) v2.0.2 · **Actualizado:** 2026-08-23

**Leyenda:** ✅ Cubierta (existe prueba que falla si se viola) · ⚠️ Parcial (hay prueba, pero no
cubre el caso adversarial) · ❌ Pendiente (regla declarada, sin prueba).

---

## Reglas y su verificación

### `PG-CFG` — Configuración, secretos y entorno

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-CFG-001` | `DEBUG` jamás activo fuera de local | Bloqueante | ✅ | `backend/tests/test_configuracion_segura.py` |
| `PG-CFG-002` | Ningún secreto conserva su valor de desarrollo en producción | Bloqueante | ✅ | `backend/tests/test_configuracion_segura.py` |
| `PG-CFG-003` | `ALLOWED_HOSTS` y CORS cerrados por defecto | Bloqueante | ⚠️ | `backend/tests/test_configuracion_segura.py` |
| `PG-CFG-004` | `manage.py check --deploy` sin advertencias | Mayor | ✅ | `.github/workflows/ci.yml` (job `configuracion`) |
| `PG-CFG-005` | Ningún secreto versionado en git | Bloqueante | ❌ | _(sin prueba)_ |

### `PG-OPE` — Capa operacional — Pinot, Kafka, Zookeeper

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-OPE-001` | Un consumidor detenido es un fallo, no un silencio | Bloqueante | ❌ | _(sin prueba)_ |
| `PG-OPE-002` | Reconciliación evento publicado → fila consultable | Bloqueante | ⚠️ | `backend/tests/regression/test_cadena_completa_accidente_despacho_seguimiento.py` |
| `PG-OPE-003` | Esquema declarado == esquema real | Mayor | ✅ | `backend/tests/regression/test_doble_pinot_vs_esquemas.py` |
| `PG-OPE-004` | Upsert `FULL` y monotonía de `fecha_actualizacion` | Mayor | ⚠️ | `backend/tests/regression/test_fecha_actualizacion_epoch_ms.py` |
| `PG-OPE-005` | Idempotencia de reintentos | Mayor | ❌ | _(sin prueba)_ |
| `PG-OPE-006` | Límite de resultados explícito en toda consulta | Mayor | ✅ | `backend/tests/regression/test_pinot_client_limit.py` |
| `PG-OPE-007` | Pinot es de solo lectura desde Django | Bloqueante | ✅ | `backend/tests/seguridad/test_pinot_solo_lectura.py` |
| `PG-OPE-008` | Borrado lógico en el camino de la API | Mayor | ❌ | _(sin prueba)_ |

### `PG-ANA` — Capa analítica — ClickHouse, Airflow, ETL

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-ANA-001` | Cuadre analítica ↔ operacional | Bloqueante | ❌ | _(sin prueba)_ |
| `PG-ANA-002` | Frescura declarada y visible | Mayor | ❌ | _(sin prueba)_ |
| `PG-ANA-003` | Un DAG fallido no deja datos a medias | Bloqueante | ❌ | _(sin prueba)_ |
| `PG-ANA-004` | Reejecución de un DAG es idempotente | Mayor | ❌ | _(sin prueba)_ |
| `PG-ANA-005` | Alias que tapa la columna en ClickHouse | Mayor | ❌ | _(sin prueba)_ |
| `PG-ANA-006` | El Postgres de Airflow no almacena negocio | Mayor | ❌ | _(sin prueba)_ |

### `PG-API` — Contratos de API

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-API-001` | Implementación conforme al contrato OpenAPI | Mayor | ⚠️ | `apps/accidentes/tests/api/test_informes_openapi_conforme.py` |
| `PG-API-002` | Rechazo estricto de campos no declarados | Bloqueante | ⚠️ | varios `test_*_contract.py` |
| `PG-API-003` | Envelope y errores uniformes | Mayor | ⚠️ | `core/api/response_envelope.py` (implementación) |
| `PG-API-004` | Validación de límites y tipos | Mayor | ❌ | _(sin prueba)_ |
| `PG-API-005` | Paginación íntegra | Mayor | ⚠️ | `apps/accidentes/tests/api/test_informes_paginacion_integridad.py` |

### `PG-NEG` — Lógica de negocio y concurrencia

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-NEG-001` | Escrituras concurrentes sobre el mismo recurso | Mayor | ❌ | _(sin prueba)_ |
| `PG-NEG-002` | Doble asignación de unidad de emergencia | Bloqueante | ❌ | _(sin prueba)_ |
| `PG-NEG-003` | Transiciones de estado válidas | Mayor | ⚠️ | dispersa por módulo |
| `PG-NEG-004` | Unicidad e integridad de identificadores | Mayor | ✅ | `backend/tests/test_secuencia_id.py` |
| `PG-NEG-005` | Cálculos de facturación y cuotas | Mayor | ⚠️ | módulos de suscripciones y partners |

### `PG-SEC` — Seguridad transversal

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-SEC-001` | Aislamiento multi-tenant (IDOR) | Bloqueante | ⚠️ | `apps/partners/tests/unit/test_no_enumeracion_partners.py` |
| `PG-SEC-002` | Autorización vertical por rol | Bloqueante | ⚠️ | `e2e/tests/04-auth-roles.spec.ts` |
| `PG-SEC-003` | Integridad del JWT | Bloqueante | ✅ | `backend/tests/seguridad/test_integridad_jwt.py` |
| `PG-SEC-004` | Límite de tasa efectivo | Mayor | ✅ | `backend/tests/seguridad/test_throttles.py` |
| `PG-SEC-005` | Inyección | Bloqueante | ⚠️ | `backend/tests/seguridad/test_inyeccion.py` + `test_inyeccion_integracion.py` |
| `PG-SEC-006` | Subida de archivos | Mayor | ✅ | `backend/tests/seguridad/test_subida_archivos.py` |
| `PG-SEC-007` | Datos sensibles en registros y respuestas | Bloqueante | ⚠️ | `backend/tests/seguridad/test_datos_sensibles.py` |
| `PG-SEC-008` | Cabeceras y cookies de seguridad HTTP | Mayor | ✅ | `backend/tests/seguridad/test_cabeceras.py` |
| `PG-SEC-009` | Dependencias sin vulnerabilidades conocidas | Mayor | ✅ | `.github/workflows/ci.yml` (job `dependencias`) |
| `PG-SEC-010` | Endpoints de demo aislados del sistema real | Mayor | ✅ | `backend/tests/seguridad/test_aislamiento_demo.py` |

### `PG-UI` — Frontend y E2E

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-UI-001` | Componentes sin acceso directo a red | Menor | ⚠️ | 250 `.spec.ts` en `frontend/src` |
| `PG-UI-002` | El sistema nunca muestra una pantalla en blanco | Mayor | ⚠️ | `e2e/tests/` |
| `PG-UI-003` | Sesión expirada durante el uso | Mayor | ❌ | _(sin prueba)_ |
| `PG-UI-004` | Validación duplicada, nunca delegada | Mayor | ⚠️ | dispersa |
| `PG-UI-005` | Reconexión de SSE | Mayor | ❌ | _(sin prueba)_ |
| `PG-UI-006` | Accesibilidad | Menor | ❌ | _(sin prueba)_ |

### `PG-RES` — Rendimiento, resiliencia y observabilidad

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-RES-001` | Presupuestos de latencia por motor y percentil | Mayor | ⚠️ | `PerfTrace` en tests |
| `PG-RES-002` | Degradación ante caída de dependencias | Bloqueante | ❌ | _(sin prueba)_ |
| `PG-RES-003` | Arranque en orden y reintento | Mayor | ❌ | _(sin prueba)_ |
| `PG-RES-004` | Sonda de salud honesta | Mayor | ❌ | _(sin prueba)_ |
| `PG-RES-005` | Prueba de carga sobre la cadena crítica | Mayor | ❌ | _(sin prueba)_ |
| `PG-RES-006` | Migraciones reversibles | Mayor | ❌ | _(sin prueba)_ |

### `PG-CI` — Compuertas de calidad y automatización

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-CI-001` | Pipeline de integración continua | Bloqueante | ✅ | `.github/workflows/ci.yml`, `.github/workflows/integracion.yml` |
| `PG-CI-002` | Cobertura como compuerta, no como informe | Mayor | ✅ | `.github/workflows/ci.yml` (`--cov-fail-under=90`) |
| `PG-CI-003` | Cero pruebas intermitentes o desactivadas | Mayor | ⚠️ | `.github/workflows/ci.yml` (sin exclusiones) |
| `PG-CI-004` | Análisis estático | Menor | ⚠️ | `.github/workflows/ci.yml` (job `estatico`) |

### `PG-DOC` — Coherencia documental

| Regla | Descripción | Severidad | Estado | Verificada por |
|---|---|---|---|---|
| `PG-DOC-001` | Toda regla nueva nace con estado | Mayor | ✅ | `backend/tests/seguridad/test_coherencia_plan.py` |
| `PG-DOC-002` | Coherencia del rol de Pinot en la documentación | Menor | ✅ | `.specify/docs/infra/infrastructure.md` §3 (corregido) |

---

## Resumen

| | Reglas | ✅ | ⚠️ | ❌ |
|---|---|---|---|---|
| `PG-CFG` | 5 | 3 | 1 | 1 |
| `PG-OPE` | 8 | 3 | 2 | 3 |
| `PG-ANA` | 6 | 0 | 0 | 6 |
| `PG-API` | 5 | 0 | 4 | 1 |
| `PG-NEG` | 5 | 1 | 2 | 2 |
| `PG-SEC` | 10 | 6 | 4 | 0 |
| `PG-UI` | 6 | 0 | 3 | 3 |
| `PG-RES` | 6 | 0 | 1 | 5 |
| `PG-CI` | 4 | 2 | 2 | 0 |
| `PG-DOC` | 2 | 2 | 0 | 0 |
| **Total** | **57** | **17** | **19** | **21** |

**13 de las 18 reglas bloqueantes siguen sin cobertura completa.** Es el número que decide
si el sistema puede considerarse validado — no el total de reglas ni el de pruebas existentes.

| Regla | Estado | Descripción |
|---|---|---|
| `PG-CFG-003` | ⚠️ | `ALLOWED_HOSTS` y CORS cerrados por defecto |
| `PG-CFG-005` | ❌ | Ningún secreto versionado en git |
| `PG-OPE-001` | ❌ | Un consumidor detenido es un fallo, no un silencio |
| `PG-OPE-002` | ⚠️ | Reconciliación evento publicado → fila consultable |
| `PG-ANA-001` | ❌ | Cuadre analítica ↔ operacional |
| `PG-ANA-003` | ❌ | Un DAG fallido no deja datos a medias |
| `PG-API-002` | ⚠️ | Rechazo estricto de campos no declarados |
| `PG-NEG-002` | ❌ | Doble asignación de unidad de emergencia |
| `PG-SEC-001` | ⚠️ | Aislamiento multi-tenant (IDOR) |
| `PG-SEC-002` | ⚠️ | Autorización vertical por rol |
| `PG-SEC-005` | ⚠️ | Inyección |
| `PG-SEC-007` | ⚠️ | Datos sensibles en registros y respuestas |
| `PG-RES-002` | ❌ | Degradación ante caída de dependencias |

---

## Registro de correcciones

Las correcciones de código asociadas viven en [`changelog.md`](../../../.specify/docs/changelog.md):

| Entrada | Fecha | Reglas afectadas |
|---|---|---|
| C1 | 2026-08-23 | `PG-CFG-001`, `PG-CFG-002` (✅) · `PG-CFG-003`, `PG-CFG-005` (parcial) |
| C2 | 2026-08-23 | `PG-CI-001`, `PG-CFG-004`, `PG-SEC-009` (✅) · `PG-SEC-008`, `PG-CI-004` (parcial) |
| C3 | 2026-08-23 | `PG-CI-003` — 42 pruebas recuperadas; exclusiones del CI retiradas |

Ambigüedades pendientes de decisión: `decisiones-pendientes.md` (#50).
