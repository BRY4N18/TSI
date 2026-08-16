# Research — Informes Tácticos Simples de Soporte al Cliente (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el código real. La primera **corrige una suposición de la spec** y
tiene consecuencia sobre los cuatro módulos anteriores.

---

## D1 — El criterio de pertenencia amplio no está poblado, y eso afecta a toda la serie ⚠️

**La spec suponía** que Soporte resuelve la cuenta de un usuario «por estar vinculado a ella, no por
ser su administrador local». **Es inexacto en dos sentidos.**

**Primero: no es un criterio, es una unión.** `cliente_lookup_service.py` consulta la tabla de
vínculos y, **si no encuentra nada, cae en el administrador local**. No elige entre criterios: los
acumula.

**Segundo, y más importante: la tabla de vínculos no la escribe nadie.** Existe, tiene su topic de
ingesta declarado, y aun así **ningún código de producción publica en ella**. Las únicas escrituras
están en las pruebas. El script de siembra del usuario de partner lo dice explícitamente: vincula
por administrador local «porque esa tabla no tiene topic de Kafka, y el resolutor ya contempla ese
camino».

> **La justificación de ese comentario es incorrecta**: la tabla **sí** tiene topic declarado. Lo
> cierto es la conclusión práctica —se vincula por administrador local—, no el motivo que da.

**Consecuencia real, y no es pequeña:** hoy, en **todos** los departamentos, la pertenencia se
resuelve de hecho por administrador local. Una organización con cinco usuarios tiene **uno solo**
que puede consultar los listados acotados a su cuenta.

**Decisión.** Se conserva la parametrización construida en Red Operativa, se declara que Soporte usa
el criterio amplio, y **se acepta que hoy ambos criterios resuelven la misma población**. No se
puebla la tabla de vínculos desde esta spec.

**Rationale.** Tres razones:

1. **La parametrización sigue siendo correcta.** Que hoy los dos criterios coincidan no la vuelve
   inútil: es lo que hará que el sistema se comporte bien el día que la tabla se pueble, sin tocar
   cinco departamentos.
2. **Poblar la tabla es una decisión de negocio, no de informes.** Determina quién de una
   organización puede ver qué, y eso excede el alcance de un módulo de listados.
3. **Ocultarlo sería peor.** Si nadie lo anota, el primero que pruebe con un usuario que no sea
   administrador local leerá el `403` como un defecto de estos listados.

**Alternativa descartada.** *Poblar la tabla de vínculos desde este módulo* — cambiaría el alcance
de acceso de cuatro departamentos ya especificados, por una decisión que no corresponde tomar aquí.

> **Para `decisiones-pendientes.md`:** ¿es intencional que solo el administrador local de una cuenta
> pueda consultar los listados de su organización? Si no lo es, hay que poblar la tabla de vínculos,
> y conviene hacerlo antes de que los ocho departamentos estén construidos.

---

## D2 — De once tipos de acción, solo dos son escalados

**Hallazgo.** El registro de acciones sobre un ticket usa once tipos distintos:
`creacion`, `clasificacion_manual`, `asignacion_agente`, `comentario`, `alerta_sla_riesgo`,
`escalado_manual`, `escalado_automatico_sla`, `resolucion`, `cierre_confirmado`,
`cierre_automatico_por_vencimiento` y `reapertura`.

**Decisión.** El listado de escalados incluye **exactamente dos**: el manual y el automático por
incumplimiento de plazo.

**Rationale.** Dos exclusiones merecen justificarse:

- **`alerta_sla_riesgo` no es un escalado.** Es un aviso previo de que el plazo se acerca; el ticket
  sigue con el mismo agente y el mismo nivel. Incluirlo inflaría el recuento de escalados con
  avisos que no cambiaron nada.
- **`cierre_automatico_por_vencimiento` tampoco.** Es otra acción del sistema, pero cierra un
  ticket, no lo deriva.

Confundir cualquiera de las dos con un escalado daría la impresión de que la cola se deriva mucho
más de lo que se deriva.

---

## D3 — Automático o humano: dos señales que deben coincidir

**Hallazgo.** La distinción entre un escalado decidido por una persona y uno disparado por el sistema
está registrada **por duplicado**:

| Señal | Manual | Automático |
|---|---|---|
| Tipo de acción | `escalado_manual` | `escalado_automatico_sla` |
| Autor de la acción | El agente que escaló | **Ausente** |

La ausencia de autor es deliberada: antes se registraba al supervisor que **recibía** el escalado
como si lo hubiera **ejecutado**, y la corrección consistió precisamente en dejar el autor vacío y
mover al supervisor al campo de destinatario.

**Decisión.** El autor **ausente** es la señal autoritativa para presentar la acción como del
sistema. El tipo de acción se usa para filtrar, no para decidir la autoría.

**Rationale.** La regla de negocio es «una acción automática se registra explícitamente como del
sistema». Si ambas señales se contradijeran —un `escalado_automatico_sla` con autor, o un
`escalado_manual` sin él— el dato estaría corrupto, y presentarlo según el tipo de acción lo
ocultaría. Apoyarse en la ausencia de autor hace visible la incoherencia en vez de disimularla.

**Prueba obligatoria.** Que las dos señales **coincidan** en todos los registros del período: ningún
escalado automático con autor, ningún manual sin él.

---

## D4 — El texto de los mensajes no se lee, ni siquiera para descartarlo

**Decisión.** El repositorio del listado de escalados **enumera columnas y no incluye el texto del
mensaje**. No se lee y luego se descarta: no se consulta.

**Rationale.** Ese texto es donde viven las notas internas dirigidas al equipo de atención, y la
regla de que no lleguen al cliente ya está establecida. Hoy se aplica leyendo la lista completa y
filtrando después.

Para un listado, **no consultarlo es más seguro que filtrarlo**: un filtro correcto sigue siendo un
filtro que alguien puede olvidar al añadir un campo dentro de seis meses, y el fallo sería silencioso
—la respuesta seguiría teniendo la forma esperada, solo que con contenido interno dentro—.

Un listado táctico responde **qué pasó, cuándo y quién lo hizo**. La prosa no forma parte de esa
pregunta.

---

## D5 — La situación del compromiso tiene cuatro valores, y el cuarto es el que importa

**Hallazgo.** `en curso`, `en riesgo`, `incumplido` y **`sin compromiso`**.

**Decisión.** El listado los expone los cuatro y permite filtrar por cada uno.

**Rationale.** `sin compromiso` es el ticket **clasificado** cuyo cliente no resuelve un plan, así que
no se le pudo asignar plazo. El vigilante de plazos **lo descarta**, precisamente porque no tiene
compromiso que vigilar. Es decir: es el único estado en el que un ticket puede quedarse indefinidamente
sin que ningún proceso lo mire.

Tratarlo como ausencia de dato —omitirlo del listado, o presentarlo como `en curso`— reintroduciría
el defecto que la corrección anterior resolvió, y volvería invisible exactamente lo que hay que ver.

---

## D6 — Qué se expone de un ticket

**Hallazgo.** El ticket guarda `asunto` y `descripcion`, ambos escritos por quien lo reportó.

**Decisión.** Se expone el **asunto**, no la descripción. Columnas enumeradas.

**Rationale.** El asunto identifica el ticket en una lista; la descripción es el cuerpo del reporte y
no aporta a una vista de cola. No es material interno —lo escribió el propio reportador— así que la
exclusión es de utilidad, no de confidencialidad: una descripción larga en cada fila hace la
respuesta pesada sin que nadie la lea desde un listado.

---

## D7 — Formas de cursor y tipo de cada listado

Se reutiliza la paginación keyset. Nada nuevo.

| Listado | Tipo | Orden por defecto | Cursor |
|---|---|---|---|
| Tickets | Estado actual | `fechahora DESC` | Compuesto `fechahora\|id_reclamo` |
| Escalados | **Período opcional** | `fecha_accion DESC` | Compuesto `fecha_accion\|id_historial` |

**Nota sobre el orden de la cola.** El listado de tickets ordena por fecha de registro descendente
—lo más reciente primero—, no ascendente como las bandejas de trabajo de otros módulos. Una cola de
soporte se prioriza por plazo y prioridad, no por antigüedad bruta, y ambos son filtros disponibles;
el orden por defecto solo tiene que ser determinista.
