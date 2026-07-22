# Especificación: Gestión de Tickets de Soporte e Incidencias

## 1. Objetivo

Canalizar y resolver incidencias reportadas por los clientes dentro de los tiempos de servicio comprometidos contractualmente (SLA), mediante un sistema de tickets con ciclo de vida completo, trazabilidad inmutable vía historial, y monitoreo automático de cumplimiento de SLA con escalado automático.

## Clarifications

### Session 2026-07-21

- Q: Al reabrir un ticket cerrado (RF-TIC-005, CU-O97), ¿se asigna un `idslaconfig` nuevo o se conserva el original? → A: Renovar — se busca la configuración vigente actual en `Dim_SLAConfig` y se actualiza `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion`.
- Q: ¿Cada cuánto debe ejecutarse el job de monitoreo de SLA (RNF-TIC-001, CU-O96)? → A: Cada 1 minuto.
- Q: RN-TIC-005 asigna el ticket escalado a "supervisor/gerente de turno" pero no hay tabla ni mecanismo de turnos definido — ¿cómo se resuelve? → A: Rol fijo — se asigna a un usuario con rol "Supervisor de Soporte" configurado como responsable por defecto, sin lógica de horario/turno rotativo.
- Q: El job de CU-O96 vigila `sla_primera_respuesta` y `sla_resolucion` — ¿deben monitorearse de forma independiente? → A: Sí, de forma independiente — alerta/escala si se incumple cualquiera de los dos plazos por separado.

## 2. Contexto

Los clientes de TSI (aseguradoras, municipios, Smart Cities) dependen de la plataforma para decisiones en tiempo real. Cuando enfrentan una incidencia técnica (API no responde, dato inconsistente) u operativa (problema de acceso, consulta sobre funcionalidad), necesitan un canal formal para reportarla y recibir atención dentro de tiempos comprometidos según su plan contratado.

**Casos de uso incluidos:**

| CU | Descripción | Actor |
|----|-------------|-------|
| CU-O91 | Registrar ticket de soporte con clasificación automática y asignación de SLA | Cliente / Soporte al cliente |
| CU-O92 | Atender, escalar y resolver ticket con confirmación de cierre del cliente | Soporte al cliente |
| CU-O95 | Configurar niveles de SLA por tipo de cliente/plan (temporal versioning) | Administrador |
| CU-O96 | Notificar incumplimiento de SLA y escalar automáticamente (job de fondo) | Sistema |
| CU-O97 | Reabrir ticket cerrado por inconformidad del cliente | Cliente |

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json`): `Fact_Reclamo`, `Dim_Estado_Soporte`, `Dim_SLAConfig`, `Fact_Historial_Ticket`, `Fact_ArchivosAdjuntosReclamos`.

## 3. Actores

| Actor | Rol en este spec | Interacción principal |
|-------|--------------------|-----------------------|
| **Cliente** | Reportador de incidencias | Registra tickets, adjunta evidencias, da seguimiento, confirma resolución, reabre tickets. |
| **Soporte al cliente** | Atiende y resuelve tickets | Toma tickets, clasifica, investiga, resuelve, escala manualmente, registra notas internas. |
| **Desarrollador de APIs / Director Tecnológico** | Nivel de escalado | Recibe tickets escalados que requieren intervención técnica o decisión ejecutiva. |
| **Administrador** | Configura SLA | Define reglas de SLA por plan/tipo/prioridad con vigencia temporal. |
| **Sistema** | Monitoreo automático | Job de fondo que vigila SLA y ejecuta escalado automático y cierre automático. |
| **Supervisor de Soporte** | Receptor de escalado automático | Rol fijo (sin lógica de turno rotativo) al que se asigna `id_agente_asignado` cuando el job de CU-O96 escala un ticket por SLA incumplido (RN-TIC-005, clarificación Session 2026-07-21). |

## 4. Requisitos funcionales

### RF-TIC-001: Registro de ticket con clasificación automática y SLA (CU-O91)

1. El actor completa el formulario: `idcliente`, `asunto`, `descripcion`, `tipo`, `idaccidente` (opcional — referencia a un caso de emergencia activo, ver nota de implementación), adjuntos (opcional).
2. El sistema ejecuta clasificación automática para determinar `tipo_incidencia` y `prioridad`:
   - Tickets vinculados a una emergencia activa → `prioridad='crítico'`.
   - Clasificación por reglas predefinidas según `tipo`, plan del cliente y contexto.

**Nota de implementación (resuelta durante `/speckit-analyze`, sin sesión de clarify formal):** el spec original no definía cómo el sistema determina que un ticket está "vinculado a una emergencia activa". Se adopta el mecanismo más simple y verificable: el formulario acepta un `idaccidente` opcional; si se envía y referencia un `Fact_Accidente` con estado distinto de Cerrado/Descartado (`Fact_AccidenteTipoEstadoAccidente`), se clasifica como `prioridad='crítico'`. Si no se envía `idaccidente`, la clasificación cae al resto de reglas por palabra clave (`research.md` Decision 4). Esta es una decisión técnica documentada, no una decisión de negocio — si en producción existe otro mecanismo (p. ej. vínculo automático por `idcliente` sin que el cliente indique el accidente), debe revisarse antes de implementar RF-TIC-001.
3. `Fact_Reclamo` — INSERT con estado inicial (`idestadosoporte`, y su reflejo denormalizado en `estado`).
4. **Asignación de SLA:** `SELECT` en `Dim_SLAConfig` la fila vigente que coincida con `tipo_incidencia`, `prioridad` e `idplan` del cliente.
   - Si se encuentra coincidencia → `Fact_Reclamo` — UPDATE: `idslaconfig`, `sla_primera_respuesta`, `sla_resolucion`, `sla_status='en curso'`.
   - Si no se puede clasificar automáticamente → estado `Pendiente_de_clasificacion`, `idslaconfig=NULL`, el SLA timer **no** arranca. Cuando un agente clasifique manualmente, recién se ejecuta el bloque de asignación de SLA.
5. `Fact_ArchivosAdjuntosReclamos` — INSERT por cada archivo adjunto.
6. `Fact_Historial_Ticket` — INSERT con `tipo_accion='creacion'`.

### RF-TIC-002: Ciclo de vida completo del ticket (CU-O92)

**Toma del ticket:**
1. Agente se asigna el ticket. `Fact_Reclamo` — UPDATE: `id_agente_asignado`, `idestadosoporte=En_progreso`.
2. `Fact_Historial_Ticket` — INSERT: `tipo_accion='asignacion_agente'`.

**Interacciones:**
3. Por cada mensaje (interno o al cliente): `Fact_Historial_Ticket` — INSERT: `tipo_accion='comentario'`, con `es_nota_interna`.

**Escalado manual:**
4. Si requiere nivel superior (Desarrollador de APIs, Director Tecnológico): `Fact_Reclamo` — UPDATE: `idestadosoporte=Escalado`, `id_agente_asignado=nuevo_actor`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='escalado_manual'`.

**Resolución:**
5. Agente resuelve el ticket. `Fact_Reclamo` — UPDATE: `idestadosoporte=Resuelto`, `tiempo_solucion=diferencia`, `sla_status` recalculado (`'cumplido'` si dentro del plazo, `'incumplido'` si ya excedido).
6. `Fact_Historial_Ticket` — INSERT: `tipo_accion='resolucion'`.

**Confirmación de cierre:**
7. Ticket en Resuelto no pasa a Cerrado automáticamente. Se notifica al cliente.
   - Cliente confirma: `Fact_Reclamo` — UPDATE: `idestadosoporte=Cerrado`, `cierreconfirmadocliente=true`, `fechahoraconfirmacioncierre=now`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='cierre_confirmado'`.
   - Sin respuesta en 5 días: `Fact_Reclamo` — UPDATE: `idestadosoporte=Cerrado`, `cierreconfirmadocliente=false`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='cierre_automatico_por_vencimiento'`.

### RF-TIC-003: Configuración de SLA con vigencia temporal (CU-O95)

1. El Administrador accede a la configuración de SLA y define o modifica una regla para un plan específico.
2. **Alta de nueva regla:** `Dim_SLAConfig` — INSERT con `fechavigenciadesde=now`, `fechavigenciahasta=NULL`, `activo=true`.
3. **Modificación de regla existente:**
   - `Dim_SLAConfig` — UPDATE de la fila vigente: `fechavigenciahasta=now`, `activo=false`.
   - `Dim_SLAConfig` — INSERT de fila nueva con los tiempos actualizados, `fechavigenciadesde=now`, `fechavigenciahasta=NULL`, `activo=true`.
4. No afecta tickets existentes. Los tickets ya creados conservan su `idslaconfig` original.

### RF-TIC-004: Monitoreo y escalado automático de SLA (CU-O96)

Job programado que se ejecuta cada 1 minuto (RNF-TIC-001):
1. Lee todos los `Fact_Reclamo` con `idestadosoporte` distinto de Cerrado.
2. Compara de forma **independiente** `fechahora` + `sla_primera_respuesta` y `fechahora` + `sla_resolucion` contra la hora actual (clarificación Session 2026-07-21): un ticket sin primera respuesta a tiempo alerta/escala aunque su plazo de resolución aún tenga margen, y viceversa.
3. **Umbral 80%:** si el tiempo transcurrido supera el 80% de cualquiera de los dos plazos permitidos (`sla_primera_respuesta` o `sla_resolucion`) y el ticket no está Resuelto: `Fact_Reclamo` — UPDATE: `sla_status='en riesgo'`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='alerta_sla_riesgo'`.
4. **Límite excedido:** si se superó cualquiera de los dos plazos sin estar Resuelto/Cerrado: `Fact_Reclamo` — UPDATE: `sla_status='incumplido'`, `idestadosoporte=Escalado`, `id_agente_asignado`=usuario con rol "Supervisor de Soporte" configurado como responsable por defecto. `Fact_Historial_Ticket` — INSERT: `tipo_accion='escalado_automatico_sla'`.
5. SLA marcado como `'cumplido'` cuando el ticket se resuelve dentro de ambos plazos (se setea durante `CU-O92`).

### RF-TIC-005: Reapertura de ticket cerrado (CU-O97)

1. Validación: `Fact_Reclamo` debe tener `idestadosoporte=Cerrado`.
2. `Fact_Reclamo` — UPDATE: `idestadosoporte=Reabierto`. El resto de campos se conservan.
3. `Fact_Historial_Ticket` — INSERT: `tipo_accion='reapertura'`, `estado_anterior='Cerrado'`, `estado_nuevo='Reabierto'`.
4. Si el cliente adjunta nueva evidencia: `Fact_ArchivosAdjuntosReclamos` — INSERT.
5. **Renovación de SLA:** el sistema busca la fila vigente en `Dim_SLAConfig` que coincida con `tipo_incidencia`, `prioridad` e `idplan` del cliente (mismo criterio que RF-TIC-001 paso 4) y actualiza `Fact_Reclamo.idslaconfig`, `sla_primera_respuesta`, `sla_resolucion`, `sla_status='en curso'` (clarificación Session 2026-07-21).
6. El ticket reabierto vuelve al flujo de `CU-O92` para ser atendido nuevamente.

### RF-TIC-006: Confirmación de cierre por cliente (CU-O92)

Ticket en Resuelto espera confirmación del cliente. Si confirma → Cerrado con `cierreconfirmadocliente=true`. Si no responde en 5 días → Cerrado automático con `cierreconfirmadocliente=false`.

### RF-TIC-007: Dashboard de soporte

Métricas: tickets por estado/prioridad, SLA próximos a vencer/vencidos, tiempo promedio de primera respuesta y resolución, distribución por tipo de incidencia y por cliente, tasa de reapertura.

## 5. Requisitos no funcionales

### RNF-TIC-001: Frecuencia del job de monitoreo de SLA
El job de `CU-O96` debe ejecutarse cada 1 minuto para detectar el umbral del 80% con margen de reacción útil (clarificación Session 2026-07-21).

### RNF-TIC-002: Inmutabilidad del historial
`Fact_Historial_Ticket` es INSERT-only — ningún registro se actualiza ni elimina una vez escrito.

### RNF-TIC-003: Tiempo de respuesta del registro de ticket
El registro de un ticket (`CU-O91`), incluyendo clasificación automática y asignación de SLA, debe completarse en menos de 3 segundos.

## 6. Reglas de negocio

### RN-TIC-001
El `sla_status` es independiente del `idestadosoporte`. Un ticket puede estar "En progreso" y tener `sla_status='en riesgo'`.

### RN-TIC-002
Las notas internas (`es_nota_interna=true`) no son visibles para el cliente bajo ninguna circunstancia.

### RN-TIC-003
Un ticket en "Pendiente de clasificación" no inicia el timer de SLA hasta que un agente lo clasifique manualmente.

### RN-TIC-004
El cierre automático por falta de confirmación del cliente ocurre a los 5 días de puesto en "Resuelto".

### RN-TIC-005
El escalado automático por SLA incumplido asigna al usuario con rol "Supervisor de Soporte" configurado como responsable por defecto (sin lógica de turno rotativo) como `id_agente_asignado` (clarificación Session 2026-07-21).

### RN-TIC-006
La modificación de una regla de SLA nunca afecta tickets ya creados. Cada ticket conserva el `idslaconfig` vigente al momento de su creación.

### RN-TIC-007
`Fact_Reclamo.estado` es un campo `STRING` denormalizado que refleja el nombre del estado apuntado por `idestadosoporte` — existe para lectura rápida sin join contra `Dim_Estado_Soporte`. Toda escritura de estado debe actualizar ambos campos de forma consistente.

## 7. Entradas

### Registro de ticket (CU-O91)
`idcliente`, `asunto`, `descripcion`, `tipo`, `idaccidente` (opcional, ver nota de implementación en RF-TIC-001), `adjuntos[]` (opcional).

### Transiciones de ticket (CU-O92, CU-O97)
`accion` (tomar/comentario/escalar/resolver/confirmar/reabrir), `mensaje` (opcional), `es_nota_interna` (opcional), `id_rol_escalar` (requerido si `accion=escalar`).

### Configuración de SLA (CU-O95)
`idplan`, `tipoincidencia`, `prioridad`, `tiemporespuestamax`, `tiemporesolucionmax`.

## 8. Salidas

### Registro de ticket
- **201 Created:** `{ "id_reclamo": 145, "estado": "Abierto", "sla_primera_respuesta": "...", "sla_resolucion": "...", "sla_status": "en curso" }`. **Nota:** `id_reclamo` es `INT` autoincremental en el esquema real, no un identificador con formato de texto tipo `"TKT-2026-00145"`.
- **201 Created (no clasificable):** `{ "id_reclamo": 146, "estado": "Pendiente de clasificación", "sla_status": null }`.

### Transiciones
- **200 OK:** `{ "id_reclamo": 145, "estado_anterior": "...", "estado_nuevo": "...", "agente_asignado": "..." }`.

### Configuración de SLA
- **201 Created:** `{ "idslaconfig": 12, "fechavigenciadesde": "...", "activo": true }`.

## 9. Estados posibles

| Estado | Significado |
|--------|-------------|
| **Abierto** | Ticket registrado, sin agente asignado. SLA timer corriendo. |
| **Pendiente de clasificación** | Sistema no pudo clasificar automáticamente. SLA timer NO corre. |
| **En progreso** | Agente asignado, trabajando en la solución. |
| **Escalado** | Requiere intervención de nivel superior (manual o automático por SLA). |
| **Resuelto** | Solución implementada, esperando confirmación del cliente. |
| **Cerrado** | Ticket finalizado (confirmado por cliente o cierre automático). |
| **Reabierto** | Cliente indicó que la solución no fue efectiva. |

**Diagrama de estados:**
```
                    ┌── Pendiente_de_clasificación ──► (asignación manual de SLA) ──► Abierto
                    │
ABIERTO ──► EN PROGRESO ──► RESUELTO ──► CERRADO
   │             │                          │
   │             └─► ESCALADO               └─► REABIERTO ──► vuelve a EN PROGRESO
   │                (manual o automático)
   │
   └── CU-O96 vigila SLA en paralelo sobre todo estado ≠ Cerrado
       Puede forzar ESCALADO si se incumple el SLA
```

**Transiciones válidas:**

| Desde | Hacia | Vía |
|-------|-------|-----|
| Pendiente_de_clasificacion | Abierto | Agente clasifica manualmente |
| Abierto | En_progreso | Agente toma el ticket |
| En_progreso | Escalado | Escalado manual (agente) o automático (CU-O96) |
| En_progreso | Resuelto | Agente resuelve |
| Escalado | En_progreso | Nivel superior devuelve |
| Escalado | Resuelto | Nivel superior resuelve |
| Resuelto | Cerrado | Cliente confirma (5 días) o auto-cierre |
| Cerrado | Reabierto | Cliente reabre (CU-O97) |
| Reabierto | En_progreso | Agente retoma |

## 10. Escenarios

### Escenario 1: Registro con clasificación automática exitosa (CU-O91)
Dado que un Cliente reporta un problema técnico vinculado a un caso de emergencia activo
Cuando envía el ticket
Entonces el sistema debe clasificar `prioridad='crítico'` automáticamente
Y debe asignar `idslaconfig`, `sla_primera_respuesta`, `sla_resolucion` según el plan del cliente
Y debe insertar `Fact_Historial_Ticket` con `tipo_accion='creacion'`.

### Escenario 2: Ticket no clasificable (CU-O91)
Dado que un ticket no coincide con ninguna regla de clasificación automática
Cuando se registra
Entonces el sistema debe dejarlo en estado `Pendiente_de_clasificacion`
Y `idslaconfig` debe quedar `NULL`
Y el timer de SLA no debe arrancar.

### Escenario 3: Ciclo completo de atención y cierre confirmado (CU-O92)
Dado que un agente de Soporte toma un ticket Abierto
Cuando lo resuelve dentro del plazo de SLA
Y el cliente confirma el cierre
Entonces el sistema debe registrar `sla_status='cumplido'`
Y `idestadosoporte=Cerrado` con `cierreconfirmadocliente=true`.

### Escenario 4: Cierre automático por falta de respuesta (CU-O92)
Dado que un ticket está en estado Resuelto
Y el cliente no responde en 5 días
Cuando el sistema evalúa el vencimiento
Entonces debe cerrar el ticket con `cierreconfirmadocliente=false`
Y debe insertar `Fact_Historial_Ticket` con `tipo_accion='cierre_automatico_por_vencimiento'`.

### Escenario 5: Modificación de regla de SLA sin afectar tickets existentes (CU-O95)
Dado que existe una regla vigente de SLA para el plan "Premium"
Cuando el Administrador la modifica
Entonces el sistema debe cerrar la vigencia de la fila anterior (`activo=false`)
Y debe insertar una fila nueva con los tiempos actualizados
Y los tickets ya creados deben conservar su `idslaconfig` original sin cambios.

### Escenario 6: Escalado automático por incumplimiento de SLA (CU-O96)
Dado que un ticket "En progreso" supera el 100% de su `sla_resolucion` sin resolverse
Cuando el job de monitoreo ejecuta su ciclo
Entonces debe marcar `sla_status='incumplido'`
Y debe escalar automáticamente a `idestadosoporte=Escalado` con el usuario configurado como Supervisor de Soporte (rol fijo, sin lógica de turno rotativo — ver RN-TIC-005).

### Escenario 7: Reapertura de ticket cerrado (CU-O97)
Dado que un ticket está en estado Cerrado
Y el cliente indica que la solución no fue efectiva
Cuando ejecuta la reapertura
Entonces el sistema debe actualizar `idestadosoporte=Reabierto`
Y debe conservar todo el historial previo en `Fact_Historial_Ticket`.

## 11. Criterios de aceptación

| CA | Descripción | CU |
|----|-------------|----|
| CA-TIC-001 | Cliente/Soporte registra ticket con clasificación automática y SLA asignado cuando es clasificable. | O91 |
| CA-TIC-002 | Ticket no clasificable queda en Pendiente_de_clasificacion sin SLA. | O91 |
| CA-TIC-003 | Agente toma ticket, registra notas internas, responde al cliente. | O92 |
| CA-TIC-004 | Agente escala manualmente a Desarrollador de APIs o Director Tecnológico. | O92 |
| CA-TIC-005 | Ticket resuelto notifica al cliente y espera confirmación. | O92 |
| CA-TIC-006 | Cliente confirma cierre → Cerrado con cierreconfirmadocliente=true. | O92 |
| CA-TIC-007 | Sin respuesta en 5 días → auto-cierre con cierreconfirmadocliente=false. | O92 |
| CA-TIC-008 | Admin configura regla SLA nueva → INSERT en Dim_SLAConfig. | O95 |
| CA-TIC-009 | Admin modifica regla SLA → cierre vigencia anterior + INSERT nueva fila. | O95 |
| CA-TIC-010 | Job monitorea tickets activos y marca sla_status='en riesgo' al 80%. | O96 |
| CA-TIC-011 | Job escala automáticamente al exceder SLA → idestadosoporte=Escalado. | O96 |
| CA-TIC-012 | Cliente reabre ticket cerrado → idestadosoporte=Reabierto con historial conservado. | O97 |
| CA-TIC-013 | Reapertura permite adjuntar nueva evidencia. | O97 |

## 12. Dependencias

- **`autenticacion-y-rbac`:** requiere roles Cliente, Soporte al Cliente, Administrador, Desarrollador de APIs, Director Tecnológico, y el rol nuevo **Supervisor de Soporte** (agregado a `Dim_Rol` por la clarificación Session 2026-07-21 de RN-TIC-005 — un único usuario responsable fijo, sin gestión de turnos).
- **`incorporacion-clientes`:** tickets asociados a clientes con cuenta activa.
- **`billing-and-auto-renewal`** (módulo Suscripciones-Facturación): `Dim_SLAConfig` depende de `idplan` (plan de suscripción del cliente).

## 13. Fuera de alcance

- Chat en vivo o chatbot.
- Base de conocimiento autogestionada por el cliente.
- Encuesta de satisfacción post-resolución (NPS).
- Integración con sistemas externos de helpdesk (Zendesk, Freshdesk, Jira).
- Automatización de respuestas con IA o sugerencia de soluciones basadas en tickets similares.
- Integración con pasarela de pago para reembolsos.
