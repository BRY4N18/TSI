# Especificación Funcional: Notificación de Prospectos a Ventas

**Spec:** `notificacion-ventas` · **Módulo:** Ventas-CRM · **Índice module-map.md:** #5  
**Carpeta:** `specs/003-operational/Ventas-CRM/notificacion-ventas/`  
**Fuente:** `VentasCRM_Pre-venta.md` (Parte 0) + `data-model.md` + `actors.md` + `architectural-patterns.md` + `api-standards.md` + `testing.md` + `constitution.md`  
**Depende de:** `commercial-pipeline-prospects` (spec #4)  
**Estado:** Draft clarificado (sesión `/speckit-clarify` 2026-07-25) — listo para `/speckit-plan`  
**Última actualización:** 2026-07-25

## Clarifications

### Session 2026-07-25

- Q: ¿IDs canónicos de CU? → A: **O118** (demo) y **O122** (notificar), según `module-map.md`; alias de fuente CU-O65→O118, CU-O31→O122.
- Q: ¿Qué hacer con `estado_envio` ausente en `data-model.md`? → A: **Fuera de alcance del MVP.** El registro en `Fact_NotificacionVentas` documenta la decisión de negocio (regla + destinatario + canal). El estado/reintento de *entrega* por canal vive en `core/notificaciones`, sin ampliar el esquema Pinot.
- Q: ¿Formato de `demo_expiracion` (STRING)? → A: **ISO-8601 UTC** con timestamp absoluto de expiración (ej. `2026-07-25T15:30:00Z`). Duración por defecto de sesión: **30 minutos** desde el primer acceso.
- Q: ¿Catálogo MVP de `regladisparada`? → A: Exactamente las dos reglas de la fuente, con umbrales literales (ver RN-NV-003). Reglas adicionales = fuera de alcance.
- Q: ¿Ventana de deduplicación? → A: **Día calendario UTC** (`fechahoranotificacion` en el mismo `YYYY-MM-DD` UTC).
- Q: ¿“Encolar” sin tabla de pendientes? → A: Significa **elegible para re-evaluación** por el mismo job (Decisión 2); ventana de elegibilidad = **7 días** desde el `timestamp_evento` del disparador.
- Q: ¿Canales vs `core/notificaciones` (email/SMS/push)? → A: Enum de negocio permanece `email | slack | push` (fuente). SMS no está en el enum de negocio. Slack requiere adaptador en `core/notificaciones` (hoy documenta email/SMS/push).
- Q: ¿Autorización para iniciar sesión de demo? → A: **`idprospecto` + código/grant de demo** emitido en el registro del prospecto (`commercial-pipeline-prospects`); canjeable una vez (o hasta fijar `demo_expiracion`); no basta el id numérico solo.
- Q: ¿Alcance de Slack en el MVP? → A: El enum acepta `slack` (validación/contrato); **envío real por Slack fuera de MVP** (sin adaptador). Ninguna regla MVP lo usa; si en el futuro una regla elige `slack`, el envío falla de forma explícita hasta existir el adaptador.
- Q: ¿Ventana de agregación de las reglas MVP? → A: Solo eventos de la **sesión de demo activa** (desde el evento `inicio_sesion` / grant canjeado hasta `demo_expiracion`); no se agregan demos previas ni la ventana de 7 días.
- Q: ¿Reemisión de token si el grant ya se canjeó? → A: Si `now < demo_expiracion`, **reemitir token** presentando el mismo grant ya canjeado; **sin** prolongar `demo_expiracion` ni crear un nuevo `inicio_sesion` (misma sesión de agregación).
- Q: ¿Re-evaluación vs agregación “solo en sesión”? → A: Agregación por **sesión histórica** (`[inicio_sesion, demo_expiracion]` de cada ciclo). La ventana de 7 días filtra qué sesiones pasadas se reexaminan; no exige que la demo esté “ahora abierta”.

### Trazabilidad (constitution — Mandatory traceability)

| Tipo | Referencia | Notas |
|---|---|---|
| Módulo / mapa | `module-map.md` #5 Ventas-CRM | Spec canónico de demo + alerta a ventas |
| CU canónicos | **O118, O122** | IDs oficiales del mapa |
| Alias de fuente | CU-O65→O118, CU-O31→O122 | Solo trazabilidad a `VentasCRM_Pre-venta.md` |
| Objetivo de negocio | Señalización comercial operativa (detectar intención en demo → avisar al ejecutivo) | Se introduce formalmente este conjunto de CU bajo Ventas-CRM; **no** colisiona con la ruta crítica de despacho de emergencias |

### Mapeo CU canónico ↔ requisito

| CU canónico | Alias fuente | Requisitos |
|---|---|---|
| **O118** | CU-O65 | RF-NV-001 — Acceso a demo e ingesta de interacciones |
| **O122** | CU-O31 | RF-NV-002 — Evaluación de reglas y notificación |
| *(derivado)* | RN-NV-002 | RF-NV-003 — Re-evaluación tras asignación tardía |
| *(consulta / auditoría)* | Nota clave fuente | RF-NV-004 — Consulta de historial por Gerente |

---

## 1. Objetivo

Detectar de forma automática el comportamiento de un Prospecto durante su sesión de demo interactiva y notificar al ejecutivo comercial responsable cuando ese comportamiento coincide con una regla de negocio del catálogo MVP, evitando notificaciones duplicadas por la misma regla en el mismo día calendario UTC, y garantizando que ninguna alerta se pierda cuando el Prospecto aún no tiene ejecutivo asignado (la **sesión histórica** queda elegible para re-evaluación mientras su `demo_expiracion` esté en los últimos 7 días).

## 2. Contexto

Este spec cubre dos piezas que funcionan como productor y consumidor del mismo flujo de eventos:

1. **Generación de eventos crudos** (**O118**): el Prospecto abre la demo con grant de un solo canje; mientras navega (sin JWT de usuario — usa token de sesión acotado por `demo_expiracion`), cada interacción relevante (`click`, `tiempo_seccion`, `inicio_sesion`, `fin_sesion`) se registra como un evento en `Fact_Interaccion_Demo`.
2. **Evaluación de reglas y notificación** (**O122**): un proceso automatizado (actor `Sistema`) evalúa esos eventos contra el catálogo MVP y, cuando una regla se cumple y hay destinatario, inserta una notificación en `Fact_NotificacionVentas` dirigida al `idusuario` vigente del Prospecto en `Dim_Prospecto`, y dispara el envío por el `canal` vía `core/notificaciones`.

Ambos casos de uso están agrupados en un mismo spec porque comparten el mismo par productor-consumidor y el mismo propósito de negocio ("detectar señal de intención de compra y avisar a ventas"), a diferencia de `commercial-pipeline-prospects`, que cubre el ciclo de vida comercial del Prospecto.

## 3. Actores

| Actor | Tipo | Rol en este spec |
|---|---|---|
| **Prospecto** | Externo, no autenticado (JWT) | Abre la demo con **grant** emitido en su registro; genera eventos (**O118**) con token de sesión. No inicia ni consume notificaciones. |
| **Sistema** | Interno (`actors.md`) | Evalúa reglas sobre `Fact_Interaccion_Demo` e inserta en `Fact_NotificacionVentas` (**O122**); re-evalúa elegibles (**RF-NV-003**). |
| **Gerente de Ventas / Gerente de Cuentas Públicas** | Interno (`actors.md`) | Destinatario de la notificación; consulta su historial (**RF-NV-004**) — solo filas donde `idusuariogerentenotificado` = su id. |
| **Administrador** | Interno (`actors.md`) | Consulta historial de notificaciones de **cualquier** gerente (**RF-NV-004**). |

### Matriz RBAC

| Requisito | Quién puede ejecutarlo |
|---|---|
| RF-NV-001 (inicio de sesión) | Público con **`idprospecto` + código/grant de demo** válido (emitido en registro del prospecto) |
| RF-NV-001 (interacciones) | Público con **token de sesión de demo** válido y no expirado |
| RF-NV-002 / RF-NV-003 | Solo Sistema |
| RF-NV-004 | Gerente: solo `idusuariogerentenotificado` = propio id; Administrador: todos |

## 4. Modelo de datos

### `Fact_Interaccion_Demo` — PK `idinteraccion` · tiempo Pinot `timestamp_evento` · tópico Kafka `Fact_Interaccion_Demo_topic`
*(Este spec es dueño y escritor original de esta tabla — ver `RF-NV-001`)*

| Columna | Tipo | Notas |
|---|---|---|
| idinteraccion (PK) | INT | |
| idprospecto | INT | FK → `Dim_Prospecto` |
| tipo_evento | STRING | `click`, `tiempo_seccion`, `inicio_sesion`, `fin_sesion` |
| seccion | STRING | ej. `precios`, `mapa_accidentes`, `dashboard` |
| metadata | STRING | JSON serializado; para `tiempo_seccion` incluye duración en ms |
| timestamp_evento | LONG (EPOCH ms) | Columna de tiempo Pinot |
| fecha_actualizacion | LONG (EPOCH ms) | |

### `Fact_NotificacionVentas` — PK `idnotificacion` · tiempo Pinot `fechahoranotificacion` · tópico Kafka `Fact_NotificacionVentas_topic`
*(Este spec es dueño y escritor original de esta tabla — ver `RF-NV-002`)*

| Columna | Tipo | Notas |
|---|---|---|
| idnotificacion (PK) | INT | |
| id_prospecto | INT | FK → `Dim_Prospecto`. Nombrado `id_prospecto` (con guion bajo) — inconsistencia de nomenclatura vs `Fact_Asignacion.idprospecto`; se respeta el esquema confirmado |
| idinteraccion | INT | FK conceptual → `Fact_Interaccion_Demo` (evento disparador) |
| idusuariogerentenotificado | INT | Tomado de `Dim_Prospecto.idusuario` vigente al disparar |
| regladisparada | STRING | Solo valores del catálogo MVP (RN-NV-003) |
| canal | STRING | `'email' \| 'slack' \| 'push'` |
| fechahoranotificacion | LONG (EPOCH ms) | Columna de tiempo Pinot |
| fecha_actualizacion | LONG (EPOCH ms) | |

**Nota — `estado_envio`:** la fuente lo menciona; el esquema confirmado en `data-model.md` **no** lo incluye. **Decisión:** no se añade columna en este MVP. El estado de entrega por canal no se modela en Pinot (ver §16 y Assumptions).

### `Dim_Prospecto` (lectura/escritura parcial — propiedad de `commercial-pipeline-prospects`)

Este spec **actualiza** `demo_expiracion` (**O118**) y **lee** `idusuario` (**O122**), pero no redefine la tabla — ver `commercial-pipeline-prospects/spec.md`, sección 4.

**`demo_expiracion`:** STRING con **ISO-8601 UTC** absoluto. Sesión **activa** si `now < demo_expiracion`; **expirada** en caso contrario. Se fija solo en el **primer** acceso (no se renueva en accesos posteriores dentro de la misma vida del prospecto, salvo que `demo_expiracion` sea NULL).

## 5. Requisitos funcionales

### RF-NV-001 — Acceder a la demo interactiva e ingresar interacciones (**O118**, actor: Prospecto)

**Comportamiento:**
- Al iniciar sesión de demo el cliente envía `idprospecto` + **código/grant de demo** emitido en el registro del prospecto (`commercial-pipeline-prospects`). Rechazar si el prospecto no existe, no está activo, el grant es inválido, o no corresponde a ese `idprospecto`.
- **Primer canje** (grant aún no usado): emitir **token de sesión de demo** opaco ligado a `idprospecto`, con validez hasta `demo_expiracion`; marcar el grant como canjeado; si `demo_expiracion` es NULL, fijarla a `now + 30 minutos` ISO-8601 UTC; persistir evento `inicio_sesion`.
- **Resume** (grant ya canjeado y `now < demo_expiracion`): reemitir un nuevo token de sesión con la misma expiración; **no** modificar `demo_expiracion`; **no** insertar otro `inicio_sesion` (la sesión de agregación sigue siendo la original).
- Si `now ≥ demo_expiracion`: rechazar inicio y resume; no emitir token que prolongue la demo (renovación = fuera de alcance).
- INSERT continuo en `Fact_Interaccion_Demo` mientras la sesión esté activa: un evento por interacción relevante (`tipo_evento`, `seccion`, `metadata`, `timestamp_evento`).
- No escribe en `Fact_Pipeline` ni `Fact_Asignacion`.

### RF-NV-002 — Notificar automáticamente ante comportamiento clave en demo (**O122**, actor: Sistema)

**Comportamiento:**
1. Lectura de `Fact_Interaccion_Demo` **acotada a la sesión histórica bajo evaluación** (intervalo `[inicio_sesion, demo_expiracion]` de ese ciclo), evaluada contra el catálogo MVP (RN-NV-003).
2. Cuando una regla se cumple y `Dim_Prospecto.idusuario` no es NULL: INSERT en `Fact_NotificacionVentas` con `id_prospecto`, `idinteraccion` (disparador), `idusuariogerentenotificado`, `regladisparada`, `canal` (según regla), `fechahoranotificacion = now`; luego despacho vía `core/notificaciones`.
3. **Deduplicación (RN-NV-001):** antes de insertar, verificar que no exista ya fila con mismo `id_prospecto` + `regladisparada` en el **mismo día calendario UTC**. Si existe, no insertar ni reenviar.
4. **Sin destinatario (RN-NV-002):** si `idusuario` es NULL, **no** insertar fila; el evento permanece **elegible para re-evaluación** (RF-NV-003).

### RF-NV-003 — Re-evaluación tras asignación tardía

Contraparte operativa de RN-NV-002. El mismo proceso de Sistema (Decisión 1–2) reevalúa, en cada corrida, **sesiones históricas** cuyo intervalo `[inicio_sesion, demo_expiracion]` intersecta los **últimos 7 días** (p. ej. `demo_expiracion ≥ now - 7 días`) y cuyo prospecto **ahora** tiene `idusuario` no nulo. Dentro de cada sesión se aplica RN-NV-003 (agregación solo con eventos de esa sesión) y RN-NV-001 (deduplicación). No existe tabla de cola dedicada. La demo **no** necesita estar abierta en el momento de la re-evaluación.

### RF-NV-004 — Consultar notificaciones enviadas a un Gerente

Permite auditar qué comportamiento disparó cada aviso: listado paginado (cursor) de `Fact_NotificacionVentas` filtrado según matriz RBAC §3.

## 6. Requisitos no funcionales (ISO/IEC 25010:2023)

| ID | Característica | Aplica | Requisito / justificación | Criterio medible |
|---|---|---|---|---|
| RNF-NV-001 | **Functional Suitability** | Sí | Completar flujo demo→evaluación→notificación→consulta | 100% de CA-NV-001…009 verificables por prueba de aceptación |
| RNF-NV-002 | **Performance Efficiency** | Sí | Notificación oportuna tras cumplimiento de regla (fuera del camino crítico de despacho) | ≤ **2 minutos** desde el cumplimiento de la condición hasta el INSERT en `Fact_NotificacionVentas` (job ≤ 60 s) |
| RNF-NV-003 | **Reliability** | Sí | Sin pérdida silenciosa por falta de destinatario; sin duplicados en el día UTC | 100% de cumplimientos de sesiones históricas con `idusuario=NULL` y `demo_expiracion` en ≤ 7 días siguen elegibles; 0 duplicados `(id_prospecto, regladisparada)` el mismo día UTC |
| RNF-NV-004 | **Security** | Sí | Demo sin JWT de usuario; abuso controlado; consulta autenticada | Inicio con grant de un solo canje; token de demo en interacciones; ≤ **60 eventos/min por token**; RF-NV-004 con Bearer JWT y filtro RBAC |
| RNF-NV-005 | **Interaction Capability** | Sí | Listado de notificaciones con estados no felices | 100% vistas asíncronas de este módulo: skeleton, vacío accionable, error con reintento |
| RNF-NV-006 | **Maintainability** | Sí | Cobertura según `testing.md` | Servicios ≥ 80%, Repositorios ≥ 85%, Vistas ≥ 75% |
| RNF-NV-007 | **Compatibility** | Sí | API versionada; canales de negocio alineados a contrato | Contrato estable bajo `/api/v1/`; breaking → `/api/v2/`; solo canales `email\|slack\|push`; envío MVP = email/push |
| RNF-NV-008 | **Flexibility** | N/A | No introduce despliegue multi-región ni adaptación geográfica del despacho; el alcance es comercial pre-venta | Documentado como N/A |
| RNF-NV-009 | **Safety** | N/A | No participa en accidente→despacho→confirmación; un fallo aquí no desvía unidades de emergencia | Documentado como N/A |

## 7. Reglas de negocio

- **RN-NV-001 (deduplicación):** no insertar si ya existe `Fact_NotificacionVentas` con el mismo `id_prospecto` + `regladisparada` cuyo `fechahoranotificacion` cae en el **mismo día calendario UTC**.
- **RN-NV-002 (sin destinatario):** si `Dim_Prospecto.idusuario` es NULL al evaluar una sesión, no insertar; el cumplimiento de esa **sesión histórica** permanece **elegible para re-evaluación** mientras `demo_expiracion` de esa sesión caiga dentro de los últimos 7 días (tras asignación vía `RF-CPP-002`/`RF-CPP-003`).
- **RN-NV-003 (catálogo MVP cerrado):**

  | `regladisparada` | Condición (agregación **por sesión histórica**, no cross-sesión) | `canal` por defecto |
  |---|---|---|
  | `tiempo_seccion_precios_5min` | Evento(s) `tiempo_seccion` en `seccion='precios'` cuya duración acumulada **en el intervalo `[inicio_sesion, demo_expiracion]` de esa sesión** ≥ **5 minutos** (300_000 ms) | `email` |
  | `visito_pricing_3x` | ≥ **3** eventos con `seccion` en `{precios, pricing}` (cualquier `tipo_evento` de interacción) **en esa misma sesión** | `push` |

  **Límite de sesión:** eventos con `timestamp_evento` ∈ `[inicio_sesion, demo_expiracion)` de un ciclo de demo concreto. No se mezclan eventos de demos distintas. La ventana de 7 días (RF-NV-003) solo selecciona *qué sesiones pasadas* reexaminar; **no** redefine el universo de agregación.

  Reglas adicionales, umbrales distintos o configuración sin despliegue = **fuera de alcance**.

- **RN-NV-004:** este spec nunca escribe en `Fact_Pipeline` ni `Fact_Asignacion`.
- **RN-NV-005 (sesión):** interacciones rechazadas si el token es inválido, no corresponde al `idprospecto`, o `now ≥ demo_expiracion`.
- **RN-NV-006 (grant de demo):** el inicio/resume exige `idprospecto` + código/grant emitido en el registro. El **primer canje** abre la sesión y fija `demo_expiracion` si era NULL. Mientras la demo esté activa, el mismo grant permite **reemitir token** (resume) sin prolongar expiración. Con demo expirada, el grant no reactiva la sesión.

## 8. Entradas / Salidas

**Entradas:** inicio de sesión de demo (`idprospecto` + código/grant de demo); eventos de interacción; corridas del proceso Sistema; consulta autenticada de historial.  
**Salidas:** token de sesión de demo; confirmación de eventos; notificaciones entregadas por canal; listado auditable; errores de grant inválido/canjeado, sesión expirada / rate limit / autorización.

## 9. Estados posibles

**`Fact_NotificacionVentas.canal`:** `email` | `slack` | `push` (enum cerrado).

**Sesión de demo:** `activa` (`now < demo_expiracion`) | `expirada` (`now ≥ demo_expiracion` o sin sesión).

**Elegibilidad de re-evaluación (lógica de proceso, no columna):** `elegible` | `no_elegible` (sesión fuera de 7 días por `demo_expiracion`, ya notificado por deduplicación, o sin cumplimiento de regla en esa sesión).

## 10. Escenarios

### Escenario 1: Generación de eventos durante la demo
Dado que un Prospecto presenta `idprospecto` + grant de demo válido (aún no canjeado),  
Cuando inicia sesión e interactúa con distintas secciones dentro de la ventana activa,  
Entonces el sistema canjea el grant, fija `demo_expiracion` (ISO-8601 UTC, +30 min), emite token de sesión e inserta un evento en `Fact_Interaccion_Demo` por cada interacción relevante.

### Escenario 2: Notificación disparada exitosamente
Dado que un Prospecto tiene ejecutivo asignado y cumple una regla del catálogo MVP por primera vez ese día UTC,  
Cuando el Sistema evalúa las reglas,  
Entonces inserta una fila en `Fact_NotificacionVentas` dirigida a ese ejecutivo y dispara el envío por el `canal` de la regla.

### Escenario 3: Deduplicación
Dado que ya existe notificación para el mismo `id_prospecto` + `regladisparada` en el día UTC vigente,  
Cuando el mismo comportamiento vuelve a cumplirse,  
Entonces el sistema no inserta una segunda fila.

### Escenario 4: Cumplimiento sin ejecutivo asignado
Dado que un Prospecto cumple una regla pero `idusuario` es NULL,  
Cuando el Sistema evalúa,  
Entonces no inserta notificación y el cumplimiento permanece elegible para re-evaluación ≤ 7 días.

### Escenario 5: Re-evaluación tras asignación tardía
Dado que una **sesión histórica** cumplió una regla sin destinatario y su `demo_expiracion` cae dentro de los últimos 7 días,  
Cuando el Prospecto es asignado y el Sistema reevalúa,  
Entonces agrega solo eventos de esa sesión, completa el INSERT y el envío (sujeto a RN-NV-001), aunque la demo ya no esté abierta.

### Escenario 6: Consulta de historial
Dado un Gerente autenticado,  
Cuando solicita su listado de notificaciones,  
Entonces recibe solo filas con `idusuariogerentenotificado` = su id (Administrador: todas), con paginación cursor y estados vacío/error/skeleton en UI.

### Escenario 7: Sesión expirada / rate limit
Dado un token expirado o > 60 eventos/min,  
Cuando se intenta ingresar una interacción,  
Entonces el sistema rechaza la operación sin persistir el evento.

### Escenario 8: Grant inválido
Dado un `idprospecto` con grant inexistente, ajeno al prospecto, o prospecto inactivo,  
Cuando se intenta `POST .../demo/sesiones`,  
Entonces el sistema rechaza sin emitir token ni fijar/alterar `demo_expiracion`.

### Escenario 9: Resume con grant ya canjeado (demo aún activa)
Dado un grant ya canjeado y `now < demo_expiracion`,  
Cuando el Prospecto vuelve a llamar `POST .../demo/sesiones` con el mismo grant,  
Entonces el sistema reemite un token de sesión **sin** cambiar `demo_expiracion` y **sin** un nuevo `inicio_sesion`.

## 11. Criterios de aceptación

- **CA-NV-001:** el primer acceso con grant válido y `demo_expiracion` NULL canjea el grant, fija `demo_expiracion` en ISO-8601 UTC a `now+30min`, emite token y genera al menos un evento `inicio_sesion` en `Fact_Interaccion_Demo` (RF-NV-001, RN-NV-006).
- **CA-NV-002:** 0 duplicados `(id_prospecto, regladisparada)` en el mismo día calendario UTC (RF-NV-002, RN-NV-001).
- **CA-NV-003:** todo cumplimiento de una sesión histórica con `idusuario=NULL` permanece elegible mientras `demo_expiracion` de esa sesión esté en los últimos 7 días y, tras asignación, se notifica si aún no hay duplicado del día (RF-NV-002, RF-NV-003, RN-NV-002).
- **CA-NV-004:** desde el cumplimiento de la condición hasta el INSERT ≤ **2 minutos** (RNF-NV-002), verificado en prueba de aceptación del proceso.
- **CA-NV-005:** rechazo de cualquier `canal` fuera de `email|slack|push`.
- **CA-NV-006:** RF-NV-004 respeta la matriz RBAC §3 y paginación cursor.
- **CA-NV-007:** interacciones con token inválido/expirado o que excedan 60 eventos/min por token son rechazadas y no persisten (RN-NV-005, RNF-NV-004).
- **CA-NV-008:** `POST .../demo/sesiones` con grant inválido (inexistente / ajeno / prospecto inactivo) no emite token ni modifica `demo_expiracion` (RN-NV-006).
- **CA-NV-009:** con grant ya canjeado y demo activa, `POST .../demo/sesiones` reemite token sin alterar `demo_expiracion` ni duplicar `inicio_sesion`; con demo expirada, rechaza (RN-NV-006).

## 12. Decisiones de diseño (recomendaciones para `/plan`)

### Decisión 1 — Mecanismo de disparo de RF-NV-002

**Alternativa A — Consumidor Kafka streaming:** baja latencia; alta complejidad (windowing, exactly-once) para reglas agregadas.  
**Alternativa B — Job periódico que consulta Pinot:** latencia acotada por frecuencia; alinea la deduplicación a consulta (`SELECT COUNT(*)`); más mantenible.

**Elegida: B**, job cada **60 segundos**. Justificación constitucional: Ventas-CRM no es camino crítico de despacho; Mantenibilidad gana el tie-breaker por defecto. Trade-off: latencia hasta ~2 min (aceptado en RNF-NV-002).

### Decisión 2 — Reintento sin destinatario (RF-NV-003)

**Alternativa A — Re-evaluación periódica** sobre sesiones históricas en `Fact_Interaccion_Demo` + `Dim_Prospecto` actualizado, elegibles si `demo_expiracion` ∈ últimos **7 días**.  
**Alternativa B — Tabla de pendientes nueva:** trazabilidad explícita; costo de gobernanza (tabla fuera de las 71 confirmadas).

**Elegida: A.** “Encolar” = sesión histórica elegible para re-evaluación; sin tabla nueva.

### Decisión 3 — `estado_envio`

**Elegida:** no ampliar Pinot. Entrega/reintento por canal = responsabilidad de `core/notificaciones`. `Fact_NotificacionVentas` registra la decisión de negocio, no el ACK del proveedor de canal.

### Decisión 4 — Slack en MVP

**Elegida:** validar `slack` en el enum; **no implementar adaptador de envío** en este feature. Las reglas MVP usan `email` y `push`. Despachar `slack` → error explícito de canal no disponible (sin fallback silencioso).

## 13. Contrato de API / eventos (alineado a `api-standards.md`)

| Tipo | Endpoint / mecanismo | Auth | CU / RF | Notas |
|---|---|---|---|---|
| `POST` | `/api/v1/ventas-crm/demo/sesiones` | Público (`idprospecto` + grant de demo) | O118 / RF-NV-001 | Primer canje o resume si demo activa; fija `demo_expiracion` solo si NULL; no prolonga si ya expiró |
| `POST` | `/api/v1/ventas-crm/demo/interacciones` | Token de sesión de demo | O118 / RF-NV-001 | Rate limit 60/min por token |
| — | Job interno (proceso `Sistema`) | N/A | O122 / RF-NV-002, RF-NV-003 | Cada ≤ 60 s |
| `GET` | `/api/v1/ventas-crm/notificaciones` | Bearer JWT (Gerente / Administrador) | RF-NV-004 | Cursor pagination; filtro RBAC |

## 14. Dependencias

- **`commercial-pipeline-prospects`** (#4): `Dim_Prospecto.idusuario`; re-evaluación depende de `RF-CPP-002`/`RF-CPP-003`; **emisión del grant/código de demo** en el registro del prospecto (contrato de handoff hacia este spec).
- **`core/notificaciones`:** despacho **email** y **push** en este MVP. `canal='slack'` es valor válido del enum de negocio pero **sin adaptador de envío** en este alcance (falla explícita si se intenta despachar).
- **Cuentas-Clientes:** identidad de gerentes para resolver destinatario y auth de consulta.

## 15. Fuera de alcance

- Ciclo de vida comercial del Prospecto — `commercial-pipeline-prospects`.
- Reglas de negocio adicionales al catálogo MVP (RN-NV-003).
- Configuración dinámica de reglas sin despliegue.
- Plantillas de contenido por canal.
- **Envío real por Slack** (adaptador en `core/notificaciones`); el valor `slack` permanece en el enum para compatibilidad de contrato.
- Columna / máquina de estados `estado_envio` en Pinot.
- Renovación o extensión de `demo_expiracion` tras expirar.
- Portal público de planes (O123 / alias de fuente según `commercial-pipeline-prospects`).

## 16. Assumptions

1. Duración por defecto de demo = **30 minutos** (fuente no fija valor; alineado a demos comerciales cortas).
2. Deduplicación = **día calendario UTC** (interpreta el “mismo día” de la fuente de forma no ambigua).
3. Ventana de re-evaluación = **7 días** filtrando por `demo_expiracion` de la **sesión histórica**.
4. Rate limit de interacciones = **60 eventos/min por token** (protege flood sin ahogar telemetría legítima de UI).
5. Canales de negocio = fuente (`email|slack|push`); SMS no forma parte del enum de este spec.
6. `slack` es valor de enum válido; **envío Slack fuera de MVP**. No se sustituye por SMS ni por email automáticamente.
7. Catálogo MVP = exactamente las 2 reglas de la fuente; agregación **por sesión histórica** (no cross-sesión).
8. El token de sesión de demo no es JWT de usuario RBAC; es credencial de corta vida ligada a `idprospecto` y `demo_expiracion`.
9. El grant/código de demo se emite en el registro del prospecto (`commercial-pipeline-prospects`); este spec solo lo **valida y canjea/resume** al abrir la sesión. La persistencia exacta del grant (columna vs almacén de tokens) se resuelve en `/plan` sin inventar tabla Pinot nueva si puede vivir fuera del modelo dimensional.
