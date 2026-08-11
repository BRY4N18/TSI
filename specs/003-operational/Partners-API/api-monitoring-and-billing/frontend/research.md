# Phase 0 Research — Monitoreo y Facturación de API (Frontend)

Ocho decisiones de diseño previas a la implementación. Las tres primeras condicionan todo lo demás.

---

## Decision 1: El exceso de cupo se presenta como **coste**, no como severidad

- **Decision:** el bloque de cupo usa el token `informacion` en cualquier estado, incluido el de consumo por encima del 100 %. El exceso se rotula **«Excedente estimado»** con su importe, junto a la frase «tu servicio no se interrumpe». **Ningún** `alerta-critica`, `alerta-alta` ni `alerta-media` en ese bloque.
- **Rationale:** RN-APM-002 es explícita y el SRS la documentó *«para que nadie la corrija asumiendo que debería bloquear»*. Un medidor en rojo comunicaría una interrupción que **no ocurre**, y el daño no es estético: el partner apagaría su integración por su cuenta, o abriría un ticket por un sistema que funciona.
- **Alternatives considered:**
  - *Ámbar como compromiso* — rechazado: el ámbar sigue siendo lenguaje de advertencia, y sobrepasar el cupo no es una advertencia, es una compra.
  - *Rojo con texto aclaratorio* — rechazado: el color se lee antes que el texto. Nadie lee el pie de un indicador rojo.
- **Cómo se protege de una regresión:** un test que falla si aparece un token de severidad en el bloque de cupo, con el porqué en el mensaje del aserto. Sin él, el primero que vea un 120 % en azul lo «arreglará».

## Decision 2: El panel de consumo vive **dentro** del portal existente

- **Decision:** ruta `/partners/portal/consumo`, dentro del portal de #07, con su misma navegación.
- **Rationale:** el partner ya tiene un sitio donde mira su integración («Mi integración»). Darle un segundo sitio para mirar la misma integración desde otro ángulo multiplica los lugares donde buscar sin añadir capacidad.
- **Alternatives considered:** módulo Angular propio (rechazado: duplicaría guards y servicios de #07 sin ganar aislamiento real).

## Decision 3: **Todo se consulta a la base. Nada se filtra en memoria.**

**Revisada 2026-08-10 por decisión del usuario.** La primera versión filtraba
código y fecha en cliente sobre la ventana cargada, porque el endpoint no los
aceptaba. Se descartó: **es una excepción al patrón del resto del sistema**, y
las excepciones de este tipo son las que después nadie recuerda por qué existen.

- **Decision:** `idpartner`, `solo_errores`, `codigohttp`, `desde` y `hasta` van
  **todos** al servidor, y la paginación es por cursor. Cada cambio de filtro es
  una consulta nueva, igual que en `lista-partners`, expedientes o unidades.
- **Rationale.** Filtrar en cliente tenía dos defectos que no son de rendimiento
  sino de **veracidad**:
  1. **Falsa exhaustividad.** Filtrar por `500` sobre los últimos 50 registros
     haría creer al usuario que no hay más errores de plataforma en la historia
     del partner, cuando solo no los hay en esa ventana. Declararlo en un rótulo
     lo hacía menos engañoso, no menos falso.
  2. **Descuadre con la paginación.** El recuento de la página dejaría de
     coincidir con lo que el servidor devolvió, y «Cargar más» traería filas que
     el filtro local volvería a esconder.
- **Coste:** `BE-DELTA-06` — tres parámetros y un cursor en
  `LogLlamadaRepository.list_by_partner` y en `ConsolaLogsView`. Pequeño, y
  además arregla el `next_cursor` que el `meta` anunciaba sin aceptar.
- **Matiz de implementación:** un `codigohttp` concreto **manda sobre**
  `solo_errores`. Pedir `200` con el conmutador puesto no puede devolver vacío
  en silencio: sería contradictorio y el usuario no sabría por qué.
- **Alternatives considered:** mantener el filtrado en cliente (rechazado por lo
  anterior); traer siempre los 500 y filtrar (rechazado: sigue siendo una
  ventana, solo que más grande, y el problema no era el tamaño).

## Decision 4: `null` del backend se renderiza «no aplica», nunca cero

- **Decision:** un helper único traduce `porcentaje_consumido: null` y `excedente_estimado: null` a la cadena «No aplica», con su motivo al lado («sin cupo configurado» / «sin tarifa configurada»).
- **Rationale:** el backend devuelve `null` **a propósito** cuando el cupo está en el centinela o el plan no tiene tarifa; su propio comentario dice que «inventar un 0 % sería peor que decir *no aplica*». Un 0 % se lee como «no has consumido nada», que es falso; un importe de 0,00 € se lee como «no debes nada», que puede ser falso también.
- **Dónde vive:** en el mapeo a view-model (`data-model.md`), no repartido por plantillas. Si estuviera en cada `@if`, el primero que se olvide imprimirá un cero.

## Decision 5: El auto-refresco existe, pero **apagado por defecto**

- **Decision:** botón «Actualizar» siempre; conmutador de auto-refresco cada 30 s, apagado al entrar.
- **Rationale:** la ingesta de Pinot va 5–15 s por detrás y el backend ya resta ese retraso en `datos_hasta`. Refrescar cada 5 s no traería datos nuevos: traería el mismo dato y más carga. El usuario que quiera vigilancia continua lo enciende.
- **Alternatives considered:** WebSocket/SSE (rechazado: no existe esa infraestructura para Pinot en el proyecto, y el retraso de ingesta haría que el «push» llegara igual de tarde).

## Decision 6: Vocabulario fijo para no confundir cupo con tasa

- **Decision:** dos términos, usados literalmente en toda la interfaz y en este orden de preferencia:

| Concepto | Término en UI | Nunca decir |
|---|---|---|
| `limitellamadasmes` | **Cupo mensual** | «límite», «cuota» a secas |
| `limitellamadasminuto` | **Límite de ritmo** | «cuota por minuto», «límite mensual» |
| Consumo sobre el cupo | **Excedente** | «exceso de cuota», «sobrepasado» |
| `429` | **Límite de ritmo alcanzado** | «cuota superada», «bloqueado» |

- **Rationale:** § 15 D2 del backend separa los dos mecanismos precisamente porque confundirlos lleva a la conclusión errónea de que el cupo bloquea. Si la UI los llama igual, la separación que el backend defendió se pierde en la última milla.

## Decision 7: El vacío de un mes sin consumo **no** es el vacío de un error

- **Decision:** tres copys distintos, en `app-list-empty-state` y `app-list-error-state`:

| Situación | Copy | Componente |
|---|---|---|
| Mes sin llamadas | «Este período no registró consumo.» + «No es un error: el partner no realizó llamadas en producción.» | `empty-state` |
| Consola sin registros del partner | «Sin llamadas registradas para este partner.» | `empty-state` |
| Cola de excepciones vacía | «No hay excepciones de facturación pendientes.» + «Todo el excedente del último corte se facturó correctamente.» | `empty-state` |
| Fallo de red | «No se pudieron cargar los datos.» + botón Reintentar | `error-state` |
| 403 | «No tienes acceso a esta información.» — **sin** botón Reintentar | `error-state` |

- **Rationale:** RF-APM-009 dice que un mes sin llamadas devuelve cero y «no es un error, es el caso límite normal». Si la UI lo pinta con el mismo vacío gris que un fallo de red, convierte una respuesta correcta en una sospecha de avería. El de la cola vacía se redacta en positivo **porque vacío es el estado deseable**.
- **Nota sobre el 403:** no lleva «Reintentar» a propósito. Reintentar un permiso denegado no cambia nada y sugiere que insistiendo funcionará.

## Decision 8: La cola de excepciones distingue **dos tipos** y no ofrece emitir

- **Decision:** la cola muestra dos tipos de fila, con etiqueta distinta:
  - **Reintentos agotados** — la factura existe y su emisión falló tres veces. Acción sugerida: emitirla manualmente.
  - **No tarificable** — el plan no tiene tarifa (`precio_excedente_llamada` en el centinela `-1.0`), así que **no hay factura**. Acción sugerida: configurar la tarifa del plan (CU-O26) y reejecutar el corte.
- **Rationale:** son problemas distintos con soluciones distintas. Presentarlos juntos sin distinguir haría que el Administrador buscara una factura que en el segundo caso **no existe**.
- **Y no se ofrece emitir desde la UI:** no hay endpoint de emisión manual. Un botón «Emitir» que abriera un modal para no hacer nada, o que llamara a algo inexistente, sería peor que decir cuál es el siguiente paso. Se documenta como fuera de alcance (`spec.md`), no como omisión.

---

## Hallazgo de la fase 0 — resuelto en la implementación

**`GET /logs-api` devolvía `next_cursor` en `meta` pero no aceptaba ningún
parámetro de cursor.** Cualquier consumidor del contrato —no solo esta UI—
habría asumido que podía paginar y no habría podido.

**Resuelto con `BE-DELTA-06`** (2026-08-10): el endpoint acepta `cursor` y el
repositorio filtra por `idlogllamadaapi < cursor`. El id sirve como cursor
porque es monótono con el tiempo (`_next_id` = `MAX + 1`), así que ordenar por
id descendente coincide con ordenar por fecha descendente.

La otra salida que se consideró —quitar el `next_cursor` del `meta`— habría
dejado la consola sin paginar. Se descartó al decidir que los filtros van a la
base: sin paginación, una consulta filtrada sobre un historial largo devolvería
una ventana arbitraria.
