# Data Model — Gestión de Tickets de Soporte

Esquemas verificados contra `database/esquemas.json` (Apache Pinot).

## Entidades principales (escritura vía Kafka)

### 1) `Fact_Reclamo` (el ticket)

- **PK:** `id_reclamo` (INT, autoincremental — no usar formato texto tipo `TKT-2026-00145`, ver `## 8. Salidas` del spec)
- **FKs:** `idcliente` → `Dim_Cliente`, `idestadosoporte` → `Dim_Estado_Soporte`, `idservicio` → `Dim_Servicio`, `idslaconfig` → `Dim_SLAConfig`, `id_agente_asignado` → `Dim_Usuarios` (auth-rbac)
- **Campos:** `tipo` (STRING, del formulario), `tipo_incidencia` (STRING, clasificación automática), `prioridad` (STRING), `asunto`, `descripcion`, `activo` (BOOLEAN), `estado` (STRING denormalizado, ver RN-TIC-007), `sla_status` (STRING: `en curso` | `en riesgo` | `cumplido` | `incumplido` | `null`), `cierreconfirmadocliente` (BOOLEAN)
- **Métricas:** `sla_primera_respuesta` (LONG, epoch ms — deadline), `sla_resolucion` (LONG, epoch ms — deadline), `tiempo_solucion` (INT)
- **Fechas:** `fechahora` (creación), `fechahoraconfirmacioncierre`, `fecha_actualizacion`
- **Reglas:**
  - `idestadosoporte` y `estado` deben actualizarse siempre juntos (RN-TIC-007).
  - `sla_status` es independiente de `idestadosoporte` (RN-TIC-001): un ticket "En_progreso" puede tener `sla_status='en riesgo'`.
  - Sin clasificación automática exitosa: `idestadosoporte=Pendiente_de_clasificacion`, `idslaconfig=NULL`, `sla_status=NULL` (RN-TIC-003).
  - **Nota de esquema:** `idservicio` existe en `Fact_Reclamo` (FK a `Dim_Servicio`) pero no aparece descrito en la narrativa del spec — se usa para vincular el ticket al servicio/API específico afectado cuando aplica (dato opcional, no bloqueante para RF-TIC-001).

### 2) `Fact_Historial_Ticket` (append-only)

- **PK:** `id_historial` (INT)
- **FKs:** `id_reclamo`, `idusuario` (quién ejecutó la acción; NULL si la acción la ejecuta `Sistema`)
- **Campos:** `tipo_accion` (STRING: `creacion` | `asignacion_agente` | `comentario` | `escalado_manual` | `resolucion` | `cierre_confirmado` | `cierre_automatico_por_vencimiento` | `alerta_sla_riesgo` | `escalado_automatico_sla` | `reapertura`), `mensaje` (STRING, opcional), `es_nota_interna` (BOOLEAN), `estado_anterior`, `estado_nuevo`
- **Fechas:** `fecha_accion`, `fecha_actualizacion`
- **Regla:** INSERT-only — ningún registro se actualiza ni elimina (RNF-TIC-002). Notas con `es_nota_interna=true` nunca se exponen al rol `Cliente` (RN-TIC-002), filtrado en la capa de servicio/serializer, no solo en frontend.

### 3) `Dim_SLAConfig` (versionado temporal)

- **PK:** `idslaconfig` (INT)
- **FKs:** `idplan` → `Dim_Plan`
- **Campos:** `tipoincidencia` (STRING — **sin** guion bajo, distinto de `Fact_Reclamo.tipo_incidencia` que sí lo lleva; mismo valor semántico, distinta convención de nombre de columna, preservar tal cual por venir del esquema real), `prioridad`, `activo` (BOOLEAN)
- **Métricas:** `tiemporespuestamax` (LONG), `tiemporesolucionmax` (LONG)
- **Fechas:** `fechavigenciadesde`, `fechavigenciahasta` (NULL mientras vigente), `fecha_actualizacion`
- **Reglas (RF-TIC-003, RN-TIC-006):**
  - Alta: INSERT con `fechavigenciadesde=now`, `fechavigenciahasta=NULL`, `activo=true`.
  - Modificación: UPDATE fila vigente (`fechavigenciahasta=now`, `activo=false`) + INSERT fila nueva.
  - Nunca afecta tickets ya creados — cada `Fact_Reclamo.idslaconfig` queda fijo al momento de asignación (creación o reapertura, ver Decision 8 de `research.md`).

### 4) `Fact_ArchivosAdjuntosReclamos`

- **PK:** `idarchivoadjuntoreclamo` (INT)
- **FKs:** `id_reclamo`
- **Campos:** `urlarchivo` (STRING), `activo` (BOOLEAN)
- **Fechas:** `fechahorasubida`, `fecha_actualizacion`
- **Regla:** Un INSERT por archivo adjunto, en registro inicial (RF-TIC-001) o en reapertura (RF-TIC-005, CA-TIC-013).

### 5) `Dim_Estado_Soporte`

- **PK:** `id_estado_soporte` (INT) — **nota de esquema:** nombre de columna con guion bajo (`id_estado_soporte`), distinto de la FK en `Fact_Reclamo` (`idestadosoporte`, sin guion bajo); mismo campo semántico, preservar ambas grafías tal cual están en el esquema real.
- **Campos:** `nombre` (STRING: Abierto | Pendiente_de_clasificacion | En_progreso | Escalado | Resuelto | Cerrado | Reabierto), `descripcion`, `activo`

## Entidades de lectura (fuera de este módulo)

| Entidad | Uso en módulo |
|---------|---------------|
| `Dim_Cliente` | Datos del cliente reportante; **no** usar `plan_suscripcion` (STRING de conveniencia) para resolver `idplan` — ver `Fact_Suscripcion` |
| `Fact_Suscripcion` | Fuente de verdad de `idplan` vigente del cliente (`idcliente` → `idplan` donde `activo=true`), usado por `AsignacionSLAService` (Decision 5) |
| `Dim_Plan` | Catálogo de planes, referenciado por `Dim_SLAConfig.idplan` |
| `Dim_Servicio` | Catálogo de servicios/APIs, referenciado opcionalmente por `Fact_Reclamo.idservicio` |
| `Fact_AccidenteTipoEstadoAccidente` | Detecta si el cliente tiene un caso de emergencia activo, para `prioridad='crítico'` (RF-TIC-001 paso 2, Decision 4) |
| `Dim_Usuarios`, `Dim_Rol` | Roles: Cliente, Soporte al cliente, Desarrollador de APIs, Director Tecnológico, Administrador, Supervisor de Soporte (nuevo, Decision 6) |

## Transiciones de estado

### Ticket (`Dim_Estado_Soporte` vía `Fact_Reclamo.idestadosoporte`)

```text
Pendiente_de_clasificacion → Abierto      (agente clasifica manualmente, arranca SLA)
Abierto → En_progreso                     (agente toma el ticket, CU-O92)
En_progreso → Escalado                    (escalado manual o automático CU-O96)
En_progreso → Resuelto                    (agente resuelve)
Escalado → En_progreso                    (nivel superior devuelve)
Escalado → Resuelto                       (nivel superior resuelve)
Resuelto → Cerrado                        (confirmación cliente o auto-cierre 5 días)
Cerrado → Reabierto                       (CU-O97, renueva SLA — Decision 8)
Reabierto → En_progreso                   (agente retoma)
```

### SLA (`Fact_Reclamo.sla_status`, independiente del estado del ticket — RN-TIC-001)

```text
NULL          (Pendiente_de_clasificacion — timer no arrancado, RN-TIC-003)
en curso      (SLA asignado, dentro de plazo)
en riesgo     (>80% de sla_primera_respuesta O sla_resolucion consumido — clarificación Session 2026-07-21)
incumplido    (excedió sla_primera_respuesta O sla_resolucion sin Resuelto/Cerrado → dispara Escalado)
cumplido      (resuelto dentro de ambos plazos)
```

## Eventos Kafka

### Topics de tabla (Pinot ingest)

| Topic | Productor | Disparador |
|-------|-----------|------------|
| `Fact_Reclamo_topic` | `ReclamoRepository` | O91 (INSERT), O92/O96/O97 (UPDATE) |
| `Fact_Historial_Ticket_topic` | `HistorialTicketRepository` | Toda transición/comentario/alerta |
| `Dim_SLAConfig_topic` | `SLAConfigRepository` | O95 (INSERT alta, UPDATE+INSERT modificación) |
| `Fact_ArchivosAdjuntosReclamos_topic` | `ArchivoAdjuntoRepository` | O91, O97 |

## Índices / consultas Pinot críticas

- Tickets activos por agente/estado: `Fact_Reclamo.idestadosoporte != Cerrado` filtrado por `id_agente_asignado`.
- Job de monitoreo SLA (O96): `Fact_Reclamo` con `idestadosoporte != Cerrado` y `idslaconfig IS NOT NULL`, comparando `fechahora + sla_primera_respuesta` y `fechahora + sla_resolucion` contra `now`.
- Configuración SLA vigente: `Dim_SLAConfig` con `activo=true` filtrado por `idplan`, `tipoincidencia`, `prioridad`.
- Dashboard (RF-TIC-007): agregaciones por `idestadosoporte`, `prioridad`, `tipo_incidencia`, `idcliente`; tasa de reapertura vía `Fact_Historial_Ticket.tipo_accion='reapertura'` / total tickets cerrados.
