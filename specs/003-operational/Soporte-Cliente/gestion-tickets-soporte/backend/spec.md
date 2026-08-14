# Especificación: Gestión de Tickets de Soporte e Incidencias

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../gestion-tickets-soporte.md`](../gestion-tickets-soporte.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B — autoridad Interaction Capability en capa FE; no duplicar OpenAPI/data-model en FE.


## 1. Objetivo

Canalizar y resolver incidencias reportadas por los clientes dentro de los tiempos de servicio comprometidos contractualmente (SLA), mediante un sistema de tickets con ciclo de vida completo, trazabilidad inmutable vía historial, y monitoreo automático de cumplimiento de SLA con escalado automático.

## Clarifications

### Session 2026-07-21

- Q: Al reabrir un ticket cerrado (RF-TIC-005, CU-O88), ¿se asigna un `idslaconfig` nuevo o se conserva el original? → A: Renovar — se busca la configuración vigente actual en `Dim_SLAConfig` y se actualiza `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion`.
- Q: ¿Cada cuánto debe ejecutarse el job de monitoreo de SLA (RNF-TIC-001, CU-O89)? → A: Cada 1 minuto.
- Q: RN-TIC-005 asigna el ticket escalado a "supervisor/gerente de turno" pero no hay tabla ni mecanismo de turnos definido — ¿cómo se resuelve? → A: Rol fijo — se asigna a un usuario con rol "Supervisor de Soporte" configurado como responsable por defecto, sin lógica de horario/turno rotativo.
- Q: El job de CU-O89 vigila `sla_primera_respuesta` y `sla_resolucion` — ¿deben monitorearse de forma independiente? → A: Sí, de forma independiente — alerta/escala si se incumple cualquiera de los dos plazos por separado.

### Session 2026-07-26 (remediation `/speckit-analyze`)

- Q: ¿Nombre canónico de la superficie del agente? → A: **Cola de soporte** (nav, spec, plan, UI). Deprecar sinónimos "Cola de agente" / "Tickets de Soporte" en documentación nueva.
- Q: ¿Layout de la cola? → A: **Master-detail** en una sola página (`cola-agente`): lista izquierda + panel de detalle/acciones a la derecha. La ruta `detalle-ticket` permanece para deep-link y rol Cliente.
- Q: ¿El agente crea tickets desde la cola? → A: No en v1 de RF-TIC-008. El alta sigue CU-O83 (Cliente / flujo de registro). No hay CTA "+ Nuevo ticket" en la cola del agente.
- Q: ¿Botón "Procesar reembolso" en la cola? → A: **No** — permanece fuera de alcance (§13). No se muestra en UI.
- Q: ¿Filtros de cola? → A: Sí — prioridad y estado vía query params ya definidos en OpenAPI (`prioridad`, `idestadosoporte`).
- Q: ¿Qué significa "SLA próximos a vencer" en RF-TIC-007? → A: Tickets con `sla_status='en riesgo'` (umbral 80% de RF-TIC-004 / CA-TIC-010). "Vencidos" = `sla_status='incumplido'`.

### Session 2026-07-29 (remediation `/speckit-analyze`)

- Q: ¿Los IDs del borrador de chat (O68/O27/O28/O69/O70) son canónicos? → A: **No.** Canónicos del repo: **CU-O97 / O83 / O84-O87 / O89 / O88** (ver §2 mapa). O27/O28 del borrador colisionan con Emergencias.
- Q: ¿`idservicio` (FK `Dim_Servicio`) entra en v1? → A: **Sí, opcional** en registro CU-O83 — contrato + persistencia; no bloquea clasificación/SLA.
- Q: ¿RF-TIC-007 tiene CA propio? → A: **CA-TIC-016** — dashboard expone las métricas listadas en RF-TIC-007.

## 2. Contexto

Los clientes de TSI (aseguradoras, municipios, Smart Cities) dependen de la plataforma para decisiones en tiempo real. Cuando enfrentan una incidencia técnica (API no responde, dato inconsistente) u operativa (problema de acceso, consulta sobre funcionalidad), necesitan un canal formal para reportarla y recibir atención dentro de tiempos comprometidos según su plan contratado.

**Casos de uso incluidos:**

| CU | Descripción | Actor |
|----|-------------|-------|
| CU-O83 | Registrar ticket de soporte con clasificación automática y asignación de SLA | Cliente / Partner de integración / Soporte al cliente |
| CU-O84-O87 | Atender, escalar y resolver ticket con confirmación de cierre del cliente | Soporte al cliente |
| CU-O97 | Configurar niveles de SLA por tipo de cliente/plan (temporal versioning) | Administrador |
| CU-O89 | Notificar incumplimiento de SLA y escalar automáticamente (job de fondo) | Sistema |
| CU-O88 | Reabrir ticket cerrado por inconformidad del cliente | Cliente |

**Mapa borrador (chat) → CU canónicos (repo)** — no usar IDs del borrador en implementación ni en conversación operativa:

| Borrador | Canónico | Fase |
|----------|----------|------|
| CU-O68 | **CU-O97** | Configurar SLA (`Dim_SLAConfig`, vigencia temporal) |
| CU-O27 | **CU-O83** | Registrar ticket (O27 en Emergencias es otro CU) |
| CU-O28 | **CU-O84-O87** | Atender / escalar / resolver / cierre |
| CU-O69 | **CU-O89** | Job vigilancia SLA |
| CU-O70 | **CU-O88** | Reabrir ticket |

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json`): `Fact_Reclamo`, `Dim_Estado_Soporte`, `Dim_SLAConfig`, `Fact_Historial_Ticket`, `Fact_ArchivosAdjuntosReclamos`, `Dim_Servicio` (catálogo; FK opcional `Fact_Reclamo.idservicio`).

## 3. Actores

| Actor | Rol en este spec | Interacción principal |
|-------|--------------------|-----------------------|
| **Cliente** | Reportador de incidencias | Registra tickets, adjunta evidencias, da seguimiento, confirma resolución, reabre tickets. |
| **Partner de integración** (`PartnerIntegracion`) | Reportador, para disputas de facturación | Mismo alcance que el Cliente. El SRS le reconoce registrar una disputa sobre su factura (RF-O83.2); es el mismo actor —quien recibe el servicio y reclama—, solo que su relación con TSI pasa por la API en vez del portal. Se acota a sus propios tickets por `Fact_Reclamo.idcliente`, igual que el Cliente, y **no** ve notas internas. |
| **Soporte al cliente** | Atiende y resuelve tickets | Toma tickets, clasifica, investiga, resuelve, escala manualmente, registra notas internas. |
| **Desarrollador de APIs / Director Tecnológico** | Nivel de escalado | Recibe tickets escalados que requieren intervención técnica o decisión ejecutiva. |
| **Administrador** | Configura SLA | Define reglas de SLA por plan/tipo/prioridad con vigencia temporal. |
| **Sistema** | Monitoreo automático | Job de fondo que vigila SLA y ejecuta escalado automático y cierre automático. |
| **Supervisor de Soporte** | Receptor de escalado automático | Rol fijo (sin lógica de turno rotativo) al que se asigna `id_agente_asignado` cuando el job de CU-O89 escala un ticket por SLA incumplido (RN-TIC-005, clarificación Session 2026-07-21). |

## 4. Requisitos funcionales

### RF-TIC-001: Registro de ticket con clasificación automática y SLA (CU-O83)

1. El actor completa el formulario: `idcliente`, `asunto`, `descripcion`, `tipo`, `idaccidente` (opcional — referencia a un caso de emergencia activo, ver nota de implementación), `idservicio` (opcional — FK a `Dim_Servicio` cuando la incidencia afecta un servicio/API concreto), `idfactura` (STRING, opcional — RF-O83.2, vincula una única factura en disputa; STRING porque `Fact_Factura.id_factura` es un UUID, corregido 2026-08-08; el sistema rechaza el registro con `422` si esa factura ya tiene otro ticket con disputa abierta, es decir `Fact_Reclamo.estado != 'Cerrado'`), adjuntos (opcional).
2. El sistema ejecuta clasificación automática para determinar `tipo_incidencia` y `prioridad`:
   - Tickets vinculados a una emergencia activa → `prioridad='crítico'`.
   - Clasificación por reglas predefinidas según `tipo`, plan del cliente y contexto.

**Nota de implementación (resuelta durante `/speckit-analyze`, sin sesión de clarify formal):** el spec original no definía cómo el sistema determina que un ticket está "vinculado a una emergencia activa". Se adopta el mecanismo más simple y verificable: el formulario acepta un `idaccidente` opcional; si se envía y referencia un `Fact_Accidente` con estado distinto de Cerrado/Descartado (`Fact_AccidenteTipoEstadoAccidente`), se clasifica como `prioridad='crítico'`. Si no se envía `idaccidente`, la clasificación cae al resto de reglas por palabra clave (`research.md` Decision 4). Esta es una decisión técnica documentada, no una decisión de negocio — si en producción existe otro mecanismo (p. ej. vínculo automático por `idcliente` sin que el cliente indique el accidente), debe revisarse antes de implementar RF-TIC-001.
3. `Fact_Reclamo` — INSERT con estado inicial (`idestadosoporte`, y su reflejo denormalizado en `estado`) y, si se enviaron, `idservicio` / `idfactura`.
4. **Asignación de SLA:** `SELECT` en `Dim_SLAConfig` la fila vigente que coincida con `tipo_incidencia`, `prioridad` e `idplan` del cliente.
   - Si se encuentra coincidencia → `Fact_Reclamo` — UPDATE: `idslaconfig`, `sla_primera_respuesta`, `sla_resolucion`, `sla_status='en curso'`.
   - Si no se puede clasificar automáticamente → estado `Pendiente_de_clasificacion`, `idslaconfig=NULL`, el SLA timer **no** arranca. Cuando un agente clasifique manualmente, recién se ejecuta el bloque de asignación de SLA.
5. `Fact_ArchivosAdjuntosReclamos` — INSERT por cada archivo adjunto.
6. `Fact_Historial_Ticket` — INSERT con `tipo_accion='creacion'`.

### RF-TIC-002: Ciclo de vida completo del ticket (CU-O84-O87)

**Toma del ticket:**
1. Agente se asigna el ticket. `Fact_Reclamo` — UPDATE: `id_agente_asignado`, `idestadosoporte=En_progreso`.
2. `Fact_Historial_Ticket` — INSERT: `tipo_accion='asignacion_agente'`.

**Interacciones:**
3. Por cada mensaje (interno o al cliente): `Fact_Historial_Ticket` — INSERT: `tipo_accion='comentario'`, con `es_nota_interna`. Un agente puede comentar en cualquier ticket; un Cliente solo puede comentar en tickets donde `Fact_Reclamo.idcliente` coincide con el suyo (se rechaza con `403` en caso contrario).

**Escalado manual:**
4. Si requiere nivel superior (Desarrollador de APIs, Director Tecnológico): `Fact_Reclamo` — UPDATE: `idestadosoporte=Escalado`, `id_agente_asignado=nuevo_actor`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='escalado_manual'`.

**Resolución:**
5. Agente resuelve el ticket. `Fact_Reclamo` — UPDATE: `idestadosoporte=Resuelto`, `tiempo_solucion=diferencia`, `sla_status` recalculado (`'cumplido'` si dentro del plazo, `'incumplido'` si ya excedido).
6. `Fact_Historial_Ticket` — INSERT: `tipo_accion='resolucion'`.

**Confirmación de cierre (CU-O87, RF-O87.1):**
7. Ticket en Resuelto no pasa a Cerrado automáticamente. Se notifica al cliente.
   - Cliente confirma: `Fact_Reclamo` — UPDATE: `idestadosoporte=Cerrado`, `cierreconfirmadocliente=true`, `fechahoraconfirmacioncierre=now`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='cierre_confirmado'`. Solo el Cliente dueño del ticket (`Fact_Reclamo.idcliente`) puede confirmar — un agente no puede confirmar en su nombre; se valida en `ConfirmarCierreService.confirmar()` y se rechaza con `403` si no coincide.
   - Sin respuesta en 5 días: `Fact_Reclamo` — UPDATE: `idestadosoporte=Cerrado`, `cierreconfirmadocliente=false`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='cierre_automatico_por_vencimiento'`.

### RF-TIC-003: Configuración de SLA con vigencia temporal (CU-O97)

1. El Administrador accede a la configuración de SLA y define o modifica una regla para un plan específico.
2. **Alta de nueva regla:** `Dim_SLAConfig` — INSERT con `fechavigenciadesde=now`, `fechavigenciahasta=NULL`, `activo=true`.
3. **Modificación de regla existente:**
   - `Dim_SLAConfig` — UPDATE de la fila vigente: `fechavigenciahasta=now`, `activo=false`.
   - `Dim_SLAConfig` — INSERT de fila nueva con los tiempos actualizados, `fechavigenciadesde=now`, `fechavigenciahasta=NULL`, `activo=true`.
4. No afecta tickets existentes. Los tickets ya creados conservan su `idslaconfig` original.

### RF-TIC-004: Monitoreo y escalado automático de SLA (CU-O89)

Job programado que se ejecuta cada 1 minuto (RNF-TIC-001):
1. Lee todos los `Fact_Reclamo` con `idestadosoporte` distinto de Cerrado.
2. Compara de forma **independiente** `fechahora` + `sla_primera_respuesta` y `fechahora` + `sla_resolucion` contra la hora actual (clarificación Session 2026-07-21): un ticket sin primera respuesta a tiempo alerta/escala aunque su plazo de resolución aún tenga margen, y viceversa.
3. **Umbral 80%:** si el tiempo transcurrido supera el 80% de cualquiera de los dos plazos permitidos (`sla_primera_respuesta` o `sla_resolucion`) y el ticket no está Resuelto: `Fact_Reclamo` — UPDATE: `sla_status='en riesgo'`. `Fact_Historial_Ticket` — INSERT: `tipo_accion='alerta_sla_riesgo'`.
4. **Límite excedido:** si se superó cualquiera de los dos plazos sin estar Resuelto/Cerrado: `Fact_Reclamo` — UPDATE: `sla_status='incumplido'`, `idestadosoporte=Escalado`, `id_agente_asignado`=usuario con rol "Supervisor de Soporte" configurado como responsable por defecto. `Fact_Historial_Ticket` — INSERT: `tipo_accion='escalado_automatico_sla'`.
5. SLA marcado como `'cumplido'` cuando el ticket se resuelve dentro de ambos plazos (se setea durante `CU-O84-O87`).

### RF-TIC-005: Reapertura de ticket cerrado (CU-O88)

1. Validación: `Fact_Reclamo` debe tener `idestadosoporte=Cerrado` **y** pertenecer al Cliente que solicita la reapertura (`Fact_Reclamo.idcliente`); se rechaza con `403` si no coincide — se valida en `ReabrirTicketService.reabrir()`.
2. `Fact_Reclamo` — UPDATE: `idestadosoporte=Reabierto`. El resto de campos se conservan.
3. `Fact_Historial_Ticket` — INSERT: `tipo_accion='reapertura'`, `estado_anterior='Cerrado'`, `estado_nuevo='Reabierto'`.
4. Si el cliente adjunta nueva evidencia: `Fact_ArchivosAdjuntosReclamos` — INSERT.
5. **Renovación de SLA:** el sistema busca la fila vigente en `Dim_SLAConfig` que coincida con `tipo_incidencia`, `prioridad` e `idplan` del cliente (mismo criterio que RF-TIC-001 paso 4) y actualiza `Fact_Reclamo.idslaconfig`, `sla_primera_respuesta`, `sla_resolucion`, `sla_status='en curso'` (clarificación Session 2026-07-21).
6. El ticket reabierto vuelve al flujo de `CU-O84-O87` para ser atendido nuevamente.

### RF-TIC-006: Confirmación de cierre por cliente (CU-O87)

**Alias de lectura** de los pasos de confirmación/cierre automático ya definidos en **RF-TIC-002** (pasos 7): ticket en Resuelto espera confirmación del cliente. Si confirma → Cerrado con `cierreconfirmadocliente=true`. Si no responde en 5 días → Cerrado automático con `cierreconfirmadocliente=false`. No introduce comportamiento adicional; se conserva el ID por trazabilidad de CA-TIC-006/007.

### RF-TIC-007: Dashboard de soporte

Métricas: tickets por estado/prioridad; SLA **próximos a vencer** (= `sla_status='en riesgo'`, umbral 80% de RF-TIC-004) y **vencidos** (= `sla_status='incumplido'`); tiempo promedio de primera respuesta y resolución; distribución por tipo de incidencia y por cliente; tasa de reapertura.

**Criterio de aceptación:** CA-TIC-016.

### RF-TIC-008: Cola de soporte — layout master-detail (Interaction Capability / CU-O84-O87)

Superficie canónica del agente (**Cola de soporte**) para atender tickets bajo presión operativa (Ley de Hick / Gestalt / carga cognitiva — `.specify/docs/design/design-system.md`).

1. **Composición:** una sola vista con dos paneles:
   - **Lista (izquierda):** cada ítem muestra `id_reclamo`, asunto, badges de prioridad y estado, y tipo/categoría cuando esté disponible. El ítem seleccionado se distingue visualmente (borde/acento del design system).
   - **Detalle (derecha):** asunto + id, controles de asignación/estado alineados a transiciones CU-O84-O87 (tomar, escalar, resolver según rol y estado), historial de mensajes/acciones, composer de respuesta (con opción de nota interna solo para roles de soporte).
2. **Filtros:** controles de prioridad y estado que invocan `GET /soporte/tickets` con `prioridad` y/o `idestadosoporte` (contrato OpenAPI existente).
3. **Empty state:** si no hay tickets tras filtros (o sin filtros), mostrar título de página + mensaje "No hay tickets pendientes." sin acciones de reembolso ni de alta de ticket. No dejar la pantalla en blanco total sin contexto de título.
4. **Fuera de esta superficie:** no mostrar CTA de reembolso ni de pasarela de pago. No CTA "+ Nuevo ticket" (alta = CU-O83 fuera de esta página).
5. **Deep-link:** `detalle-ticket` sigue disponible para Cliente y URLs directas; la cola del agente no obliga a navegar fuera para las acciones diarias de CU-O84-O87.

## 5. Requisitos no funcionales

### RNF-TIC-001: Frecuencia del job de monitoreo de SLA
El job de `CU-O89` debe ejecutarse cada 1 minuto para detectar el umbral del 80% con margen de reacción útil (clarificación Session 2026-07-21).

### RNF-TIC-002: Inmutabilidad del historial
`Fact_Historial_Ticket` es INSERT-only — ningún registro se actualiza ni elimina una vez escrito.

### RNF-TIC-003: Tiempo de respuesta del registro de ticket
El registro de un ticket (`CU-O83`), incluyendo clasificación automática y asignación de SLA, debe completarse en menos de 3 segundos.

### RNF-TIC-004: Operabilidad de la Cola de soporte (Interaction Capability)
En viewport ≥1024px, lista + detalle deben ser visibles simultáneamente sin scroll horizontal de la composición. Acciones primarias del ticket seleccionado (responder / tomar o resolver según estado) deben estar al alcance del panel de detalle (Ley de Fitts). Badges de prioridad, estado y `sla_status` usan tokens semánticos del design system (no hex ad hoc). Notas internas nunca se renderizan para rol Cliente (RN-TIC-002; verificación también en API).

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

### RN-TIC-008 (RF-O83.2)
Una factura admite una sola disputa (ticket) abierta a la vez. Se considera "abierta" cualquier ticket con esa `idfactura` cuyo `estado` sea distinto de `Cerrado` (incluye `Reabierto`). Aplicado a nivel de aplicación en `RegistrarTicketService.registrar()`, no como constraint de esquema (Pinot no soporta `UNIQUE` declarativo).

### RN-TIC-009 (RF-O83.2 x RF-APM-014) — la disputa excluye la factura del cobro automático

Registrar un ticket con `idfactura` marca esa factura como **en disputa**
(`Fact_Factura.estado_pago = 'En disputa'`), y cerrar el reclamo la devuelve a
`'Pendiente'`. Es la contraparte de RF-APM-014, que declara que la factura la marca
**este** módulo y que facturación "no abre ni resuelve disputas: solo respeta la exclusión";
sin esta regla nadie ejecutaba el marcado y se seguía reintentando el cobro del cargo que el
cliente estaba discutiendo.

No se usa un flag propio: `estado_pago` es la columna que ya consultan todos los cobradores
(excedente de API, cobro de suscripción, dunning y mora), y todos exigen `'Pendiente'`, así
que la exclusión es automática.

La liberación se aplica en **ambos** cierres —confirmación del cliente y cierre automático
por vencimiento (RN-TIC-004)—, porque de otro modo un ticket auto-cerrado dejaría la factura
fuera del cobro indefinidamente. No pisa una factura que la resolución ya dejó `Pagada` o con
el monto ajustado: ese resultado manda.

Implementado en `DisputaFacturaService`, invocado por `RegistrarTicketService.registrar()`
(después de crear el ticket) y por `ConfirmarCierreService`.

### RN-TIC-010 — Ticket clasificado sin compromiso aplicable: se declara, no se calla

Si el ticket **sí** se clasificó pero no hay regla aplicable —el cliente no tiene suscripción
activa, o su plan no tiene fila en `Dim_SLAConfig` para ese tipo y prioridad—, se guarda con
`sla_status = 'sin compromiso'`, nunca con `null`.

`null` está reservado al ticket **sin clasificar**, que además tiene su propio estado
(`Pendiente_de_clasificacion`) y por eso se ve. Un ticket clasificado sin plazo no tenía ninguna
señal: aparecía en la cola como cualquier otro mientras `MonitoreoSLAService` lo descartaba por
`idslaconfig is None`, de modo que nadie lo marcaba en riesgo ni lo escalaba. Puede ser correcto
que no haya plazo; lo que no puede es no verse.

Aplica en el alta, en la clasificación manual y en la **reapertura** — ahí además impide conservar
el `'en curso'` anterior, que mostraría un plazo que ya nadie vigila.

### RN-TIC-011 — Las acciones automáticas no llevan autor humano

`Fact_Historial_Ticket.idusuario` queda **vacío** en lo que ejecuta un proceso de fondo: el
escalado por incumplimiento de SLA, la alerta de riesgo y el cierre automático por vencimiento.
R-03 del SRS exige que una acción automática se registre explícitamente como del sistema, "lo que
permite distinguir una decisión humana de una automática".

En el escalado automático, el supervisor de turno va en `id_agente_asignado` —es el **destino**— y
en ningún otro sitio. Estamparlo también como `idusuario` hacía que la bitácora afirmara que lo
había escalado él.

La UI lo refleja marcando esas entradas como **«Sistema»**: en pantalla, un autor vacío se lee
como dato que falta, no como acción automática.

## 7. Entradas

### Registro de ticket (CU-O83)
`idcliente`, `asunto`, `descripcion`, `tipo`, `idaccidente` (opcional, ver nota de implementación en RF-TIC-001), `idservicio` (opcional, FK `Dim_Servicio`), `adjuntos[]` (opcional).

### Transiciones de ticket (CU-O84-O87, CU-O88)
`accion` (tomar/comentario/escalar/resolver/confirmar/reabrir), `mensaje` (opcional), `es_nota_interna` (opcional), `id_rol_escalar` (requerido si `accion=escalar`).

### Configuración de SLA (CU-O97)
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
   └── CU-O89 vigila SLA en paralelo sobre todo estado ≠ Cerrado
       Puede forzar ESCALADO si se incumple el SLA
```

**Transiciones válidas:**

| Desde | Hacia | Vía |
|-------|-------|-----|
| Pendiente_de_clasificacion | Abierto | Agente clasifica manualmente |
| Abierto | En_progreso | Agente toma el ticket |
| En_progreso | Escalado | Escalado manual (agente) o automático (CU-O89) |
| En_progreso | Resuelto | Agente resuelve |
| Escalado | En_progreso | Nivel superior devuelve |
| Escalado | Resuelto | Nivel superior resuelve |
| Resuelto | Cerrado | Cliente confirma (5 días) o auto-cierre |
| Cerrado | Reabierto | Cliente reabre (CU-O88) |
| Reabierto | En_progreso | Agente retoma |

## 10. Escenarios

### Escenario 1: Registro con clasificación automática exitosa (CU-O83)
Dado que un Cliente reporta un problema técnico vinculado a un caso de emergencia activo
Cuando envía el ticket
Entonces el sistema debe clasificar `prioridad='crítico'` automáticamente
Y debe asignar `idslaconfig`, `sla_primera_respuesta`, `sla_resolucion` según el plan del cliente
Y debe insertar `Fact_Historial_Ticket` con `tipo_accion='creacion'`.

### Escenario 2: Ticket no clasificable (CU-O83)
Dado que un ticket no coincide con ninguna regla de clasificación automática
Cuando se registra
Entonces el sistema debe dejarlo en estado `Pendiente_de_clasificacion`
Y `idslaconfig` debe quedar `NULL`
Y el timer de SLA no debe arrancar.

### Escenario 3: Ciclo completo de atención y cierre confirmado (CU-O84-O87)
Dado que un agente de Soporte toma un ticket Abierto
Cuando lo resuelve dentro del plazo de SLA
Y el cliente confirma el cierre
Entonces el sistema debe registrar `sla_status='cumplido'`
Y `idestadosoporte=Cerrado` con `cierreconfirmadocliente=true`.

### Escenario 4: Cierre automático por falta de respuesta (CU-O84-O87)
Dado que un ticket está en estado Resuelto
Y el cliente no responde en 5 días
Cuando el sistema evalúa el vencimiento
Entonces debe cerrar el ticket con `cierreconfirmadocliente=false`
Y debe insertar `Fact_Historial_Ticket` con `tipo_accion='cierre_automatico_por_vencimiento'`.

### Escenario 5: Modificación de regla de SLA sin afectar tickets existentes (CU-O97)
Dado que existe una regla vigente de SLA para el plan "Premium"
Cuando el Administrador la modifica
Entonces el sistema debe cerrar la vigencia de la fila anterior (`activo=false`)
Y debe insertar una fila nueva con los tiempos actualizados
Y los tickets ya creados deben conservar su `idslaconfig` original sin cambios.

### Escenario 6: Escalado automático por incumplimiento de SLA (CU-O89)
Dado que un ticket "En progreso" supera el 100% de su `sla_resolucion` sin resolverse
Cuando el job de monitoreo ejecuta su ciclo
Entonces debe marcar `sla_status='incumplido'`
Y debe escalar automáticamente a `idestadosoporte=Escalado` con el usuario configurado como Supervisor de Soporte (rol fijo, sin lógica de turno rotativo — ver RN-TIC-005).

### Escenario 7: Reapertura de ticket cerrado (CU-O88)
Dado que un ticket está en estado Cerrado
Y el cliente indica que la solución no fue efectiva
Cuando ejecuta la reapertura
Entonces el sistema debe actualizar `idestadosoporte=Reabierto`
Y debe conservar todo el historial previo en `Fact_Historial_Ticket`.

## 11. Criterios de aceptación

| CA | Descripción | CU |
|----|-------------|----|
| CA-TIC-001 | Cliente/Soporte registra ticket con clasificación automática y SLA asignado cuando es clasificable. | O83 |
| CA-TIC-002 | Ticket no clasificable queda en Pendiente_de_clasificacion sin SLA. | O83 |
| CA-TIC-003 | Agente toma ticket, registra notas internas, responde al cliente. | O84-O87 |
| CA-TIC-004 | Agente escala manualmente a Desarrollador de APIs o Director Tecnológico. | O84-O87 |
| CA-TIC-005 | Ticket resuelto notifica al cliente y espera confirmación. | O84-O87 |
| CA-TIC-006 | Cliente confirma cierre → Cerrado con cierreconfirmadocliente=true. | O84-O87 |
| CA-TIC-007 | Sin respuesta en 5 días → auto-cierre con cierreconfirmadocliente=false. | O84-O87 |
| CA-TIC-008 | Admin configura regla SLA nueva → INSERT en Dim_SLAConfig. | O97 |
| CA-TIC-009 | Admin modifica regla SLA → cierre vigencia anterior + INSERT nueva fila. | O97 |
| CA-TIC-010 | Job monitorea tickets activos y marca sla_status='en riesgo' al 80%. | O89 |
| CA-TIC-011 | Job escala automáticamente al exceder SLA → idestadosoporte=Escalado. | O89 |
| CA-TIC-012 | Cliente reabre ticket cerrado → idestadosoporte=Reabierto con historial conservado. | O88 |
| CA-TIC-013 | Reapertura permite adjuntar nueva evidencia. | O88 |
| CA-TIC-014 | Cola de soporte muestra layout master-detail: lista con badges + panel detalle/historial/composer; filtros prioridad/estado consumen query OpenAPI. | O84-O87 / RF-TIC-008 |
| CA-TIC-015 | Empty state de cola: título + "No hay tickets pendientes."; sin CTA de reembolso ni alta de ticket; sin botones de pasarela de pago. | O84-O87 / RF-TIC-008 |
| CA-TIC-016 | Dashboard (`GET /soporte/dashboard`) expone las métricas de RF-TIC-007 (por estado/prioridad, SLA en riesgo/vencidos, tiempos promedio, distribución tipo/cliente, tasa de reapertura). | RF-TIC-007 |

## 12. Dependencias

- **`autenticacion-y-rbac`:** requiere roles Cliente, Soporte al Cliente, Administrador, Desarrollador de APIs, Director Tecnológico, y el rol nuevo **Supervisor de Soporte** (agregado a `Dim_Rol` por la clarificación Session 2026-07-21 de RN-TIC-005 — un único usuario responsable fijo, sin gestión de turnos).
- **`incorporacion-clientes`:** tickets asociados a clientes con cuenta activa.
- **`subscriptions-and-billing`** (módulo Suscripciones-Facturación): `Dim_SLAConfig` depende de `idplan` (plan de suscripción del cliente).

## 13. Fuera de alcance

- Chat en vivo o chatbot.
- Base de conocimiento autogestionada por el cliente.
- Encuesta de satisfacción post-resolución (NPS).
- Integración con sistemas externos de helpdesk (Zendesk, Freshdesk, Jira).
- Automatización de respuestas con IA o sugerencia de soluciones basadas en tickets similares.
- Integración con pasarela de pago para reembolsos — **incluye cualquier CTA/botón "Procesar reembolso" (o equivalente) en la Cola de soporte u otras pantallas de este módulo**.
- Alta de ticket desde la Cola de soporte del agente (CTA "+ Nuevo ticket"); el registro permanece en CU-O83 / flujo Cliente.
