# Data Model — Informes Tácticos Simples de Soporte al Cliente (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema. Ningún cambio en la capa transversal.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Fact_Reclamo` | Entidad principal | L1 |
| `Fact_Historial_Ticket` | Entidad principal | L2 |
| `Dim_Cliente` | Catálogo (cuenta) | L1, L2 |
| `Dim_Usuarios` | Catálogo (agente, autor) | L1, L2 |
| `Dim_Servicio` | Catálogo | L1 |
| `Dim_Estado_Soporte` | Catálogo | L1 |

Todas de solo lectura.

---

## 2. El acotamiento se decide por lo que NO se tiene

| Solicitante | Alcance |
|---|---|
| Con **algún** rol de atención (Agente, Administrador) | Todos los tickets; puede filtrar por agente o cuenta |
| **Sin ningún** rol de atención (Cliente, Partner) | Solo los de su cuenta |
| Con roles de **ambos** tipos | Todos — tener un rol de atención saca del acotamiento |
| Sin rol de reporte ni de atención | Negativa |

La condición ya está implementada en el módulo operativo y **se reutiliza sin reimplementarla**. Su
razón de ser está documentada allí: decidirla por «ser Cliente» habría dejado al Partner de
integración viendo tickets ajenos.

**Columna de titularidad:** `Fact_Reclamo.idcliente`, resuelta desde el usuario por el resolutor
transversal con criterio **amplio**.

> ⚠️ **Hoy el criterio amplio y el estricto resuelven la misma población** (research D1): la tabla de
> vínculos usuario-cuenta no la escribe ningún código de producción, así que todo cae en el
> administrador local. El listado funciona; lo que no existe todavía es el acceso de los demás
> usuarios de una organización.

---

## 3. Los dos listados

### L1 — Tickets · `FR-001`, `FR-002`, `FR-004`–`FR-006` · OT19

- **Tabla:** `Fact_Reclamo`
- **Campos:** `id_reclamo`*, `cuenta`, `asunto`, `estado`, `prioridad`, `tipo_incidencia`,
  `servicio`, `agente_asignado`, `situacion_compromiso`, `factura_vinculada`, `fechahora`
- **⛔ No expuesto:** `descripcion` — cuerpo del reporte, innecesario en una vista de cola
  (research D6). **Columnas enumeradas.**
- **Orden:** `fechahora DESC` · **Cursor:** compuesto `fechahora|id_reclamo`
- **Filtros:** `estado`, `situacion_compromiso`, `prioridad`, `tipo_incidencia`, `agente`,
  `con_factura`, `cuenta`
- **Tipo:** estado actual → rechaza rango de fechas
- **Acotado por:** `idcliente`, criterio amplio
- **Catálogo:** `idcliente` → `Dim_Cliente`; `id_agente_asignado` → `Dim_Usuarios`; `idservicio` →
  `Dim_Servicio`; `idestadosoporte` → `Dim_Estado_Soporte`

**⚠️ `situacion_compromiso` toma CINCO valores** (research D5, corregido al implementar):

| Valor | Significa | ¿Alguien lo vigila? |
|---|---|---|
| `en curso` | Plazo corriendo | Sí |
| `en riesgo` | Plazo por vencer | Sí |
| `incumplido` | Plazo vencido | Sí |
| **`sin compromiso`** | Ticket clasificado **sin plazo asignable** | **No** |
| `cumplido` | Resuelto dentro de plazo | Ya no aplica |

> ⚠️ **`cumplido` faltaba en esta tabla.** Lo escribe `resolver_ticket_service`. Enumerar solo cuatro
> valores dejaría el filtro rechazando un valor legítimo con `400`, e imposible listar los tickets
> resueltos a tiempo. Los valores se **importan** de `domain_constants`, no se copian de aquí.

**`sin compromiso` es el único estado en que un ticket puede quedarse indefinidamente sin que ningún
proceso lo mire.** Omitirlo del listado, o presentarlo como `en curso`, lo volvería invisible — que
es exactamente el defecto que la corrección anterior resolvió.

Un ticket **sin clasificar** aparece sin plazo y **sin situación de compromiso**: no se le atribuye
ninguna.

---

### L2 — Escalados · `FR-003`, `FR-007`, `FR-008`, `FR-022` · OT20 / OP50

- **Tabla:** `Fact_Historial_Ticket`
- **Campos:** `id_historial`*, `id_reclamo`*, `numero_ticket`, `cuenta`, `tipo_escalado`,
  `estado_anterior`, `estado_nuevo`, `autor`, `fecha_accion`
- **⛔ No consultado:** el texto del mensaje. **No se lee y luego se descarta: no se consulta**
  (research D4). Es donde viven las notas internas.
- **Orden:** `fecha_accion DESC` · **Cursor:** compuesto `fecha_accion|id_historial`
- **Filtros:** `desde`, `hasta` (**opcionales**), `tipo_escalado`, `cuenta`
- **Tipo:** **hechos del período**
- **Acceso:** solo roles de atención. **Un reportador recibe negativa** (FR-008)

**⚠️ De once tipos de acción, el filtro incluye exactamente dos** (research D2):

| Incluido | Excluido y por qué |
|---|---|
| `escalado_manual` | `alerta_sla_riesgo` — es un **aviso**: el ticket no cambia de agente ni de nivel |
| `escalado_automatico_sla` | `cierre_automatico_por_vencimiento` — es acción del sistema, pero **cierra**, no deriva |
| | `creacion`, `clasificacion_manual`, `asignacion_agente`, `comentario`, `resolucion`, `cierre_confirmado`, `reapertura` |

Incluir los avisos inflaría el recuento de escalados con acciones que no cambiaron nada.

**⚠️ La autoría se decide por la ausencia de autor, no por el tipo** (research D3):

| Señal | Manual | Automático |
|---|---|---|
| Tipo de acción | `escalado_manual` | `escalado_automatico_sla` |
| Autor | El agente que escaló | **Ausente** |

El campo `autor` se presenta con el nombre de la persona cuando existe, y **como acción del sistema**
cuando está ausente. La ausencia es autoritativa: si las dos señales se contradijeran, el dato
estaría corrupto, y decidir por el tipo lo ocultaría.

\* Identificadores de uso interno. **No se muestran** (`design-system.md` §8) salvo el número de
ticket, que es lenguaje de negocio.

---

## 4. Reglas transversales

**Resolución de catálogo.** Dos consultas y unión en memoria — sin JOIN.

**Centinelas.** El cliente de la base ya devuelve ausencia. Un ticket sin agente asignado, sin
factura vinculada o sin prioridad llega como «no hay», y **se muestra**.

**Paginación.** Keyset, `limit + 1`.

**Retraso de ingesta.** 5–15 s. Un ticket recién resuelto puede seguir apareciendo abierto. No se
compensa.

---

## 5. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|17", "limit": 50, "has_next": true },
    "filtros": { "situacion_compromiso": "sin compromiso" },
    "acotado_a": "propios"
  }
}
```

`acotado_a` declara si el resultado está limitado a la cuenta del solicitante. Sin él, un cliente no
puede distinguir «no hay tickets incumplidos» de «no hay tickets incumplidos **míos**».

---

## 6. Resumen

| # | Listado | Tabla | Tipo | Cuidado |
|---|---|---|---|---|
| L1 | Tickets | `Fact_Reclamo` | Estado actual | ⚠️ «sin compromiso» es el que nadie vigila: hay que poder listarlo |
| L2 | Escalados | `Fact_Historial_Ticket` | Período opcional | ⚠️ solo 2 de 11 tipos · ⛔ el texto no se consulta · autoría por ausencia de autor |
