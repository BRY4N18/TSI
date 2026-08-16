# Data Model — Informes Tácticos Simples de Ventas y CRM (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Dim_Prospecto` | Entidad principal | L1 (cartera), L3 (demos activas) |
| `Fact_Asignacion` | Entidad principal | L2 |
| `Fact_NotificacionVentas` | Entidad principal | L4 |
| `Dim_Usuarios` | Catálogo | L1, L2, L4 (nombre del ejecutivo) |

Todas de solo lectura.

---

## 2. El eje de titularidad, por listado

Es lo que distingue este módulo del piloto. Cada listado acota por una columna distinta:

| Listado | Columna de titularidad | Significa |
|---|---|---|
| L1 Cartera | `Dim_Prospecto.idusuario` | Ejecutivo asignado al prospecto |
| L2 Reasignaciones | — | Solo Administrador; no se acota |
| L3 Demos activas | `Dim_Prospecto.idusuario` | Ejecutivo asignado al prospecto |
| L4 Notificaciones | `Fact_NotificacionVentas.idusuariogerentenotificado` | Ejecutivo **destinatario** del aviso |

El resolutor de `core/informes/acotamiento.py` devuelve **a quién** acotar; cada repositorio decide
**por qué columna**. Esa separación es la que permite reutilizarlo en los seis departamentos que
faltan, donde el eje será cliente, partner o proveedor.

---

## 3. Los cuatro listados

### L1 — Cartera de prospectos · `FR-001`, `FR-002` · OT01/OT02

- **Tabla:** `Dim_Prospecto`
- **Campos expuestos:** `idprospecto`*, `empresa`, `nombre_contacto`, `cargo`, `tipo_organizacion`,
  `canal_origen`, `etapa_actual`, `ejecutivo`, `estado`, `motivo_perdida`, `valor_estimado`,
  `fecha_registro`
- **⚠️ No expuestos:** `gmail`, `telefono` — dato personal de contacto excluido por defecto
  (research D4). **Columnas enumeradas, prohibido `SELECT *`.**
- **Orden:** `idprospecto DESC` · **Cursor:** escalar
- **Filtros:** `canal`, `tipo_organizacion`, `etapa`, `ejecutivo`, `estado`
- **Tipo:** estado actual → rechaza `desde`/`hasta` con `400`
- **Acotado por:** `idusuario`

**⚠️ El filtro `estado` tiene tres valores, no dos** (research D1):

| Valor | Condición | Significa |
|---|---|---|
| `activo` | `activo = true` | En curso |
| `perdido` | `motivo_inactividad = 'perdido'` | Oportunidad perdida |
| `convertido` | `motivo_inactividad = 'convertido'` | **Ganado** — ya es cliente |

**Prohibido usar `activo = false` como equivalente de «perdido»**: incluiría los convertidos, es
decir presentaría los éxitos como fracasos.

`motivo_perdida` se devuelve solo cuando el estado es `perdido`.

---

### L2 — Reasignaciones de prospecto · `FR-003` · OT02 / CU-O19

- **Tabla:** `Fact_Asignacion`
- **Campos:** `idasignacion`*, `idprospecto`*, `empresa`, `ejecutivo_anterior`, `ejecutivo_nuevo`,
  `tipo_asignacion`, `motivo`, `fechahoraasignacion`
- **Orden:** `fechahoraasignacion DESC` · **Cursor:** compuesto `fecha|idasignacion`
- **Filtros:** `desde`, `hasta` (**opcionales**), `idprospecto`, `tipo_asignacion`
- **Tipo:** **hechos del período**
- **Acotado por:** no se acota — es un listado de supervisión, solo Administrador
- **Catálogo:** `idusuariogerenteanterior` / `idusuariogerenteactual` → `Dim_Usuarios`
- **Regla:** la **primera asignación** de un prospecto no tiene responsable anterior; se presenta
  como **ausente**, no como vacío ni cero (research D7)

---

### L3 — Demos activas · `FR-004` · OT03 / CU-O23

- **Tabla:** `Dim_Prospecto` · demo con expiración futura
- **Campos:** `idprospecto`*, `empresa`, `nombre_contacto`, `ejecutivo`, `demo_expiracion`,
  `dias_restantes`
- **Orden:** `demo_expiracion ASC`, desempate `idprospecto` · **Cursor:** compuesto
- **Tipo:** estado actual
- **Acotado por:** `idusuario`

**⚠️ Filtro en dos pasos** (research D3). La columna de expiración es **texto** con formatos mixtos
(`Z`, `+00:00`, y sin zona), así que compararla entera en la base da resultados incorrectos sin
error visible:

1. **Base de datos:** prefiltro por el **prefijo de fecha** `YYYY-MM-DD` del día actual. El prefijo
   es uniforme sea cual sea el sufijo, así que la comparación es segura.
2. **Servicio:** refinamiento exacto con el instante actual, usando el parseador que ya tolera los
   tres formatos, y cálculo de `dias_restantes` **con ese mismo instante** (research D5).

**Consecuencia declarada:** una página **puede devolver menos filas que el `limit` pedido**. El
indicador de página siguiente sigue siendo la autoridad; el número de filas no lo es.

Una demo **sin fecha de expiración no se considera activa** y no aparece.

---

### L4 — Notificaciones de señal de interés enviadas · `FR-005` · OT03 / CU-O25

- **Tabla:** `Fact_NotificacionVentas`
- **Campos:** `idnotificacion`*, `id_prospecto`*, `empresa`, `ejecutivo_notificado`,
  `regla_disparada`, `canal`, `fechahoranotificacion`
- **Orden:** `fechahoranotificacion DESC` · **Cursor:** compuesto `fecha|idnotificacion`
- **Filtros:** `desde`, `hasta` (**opcionales**), `regla`, `canal`
- **Tipo:** **hechos del período**
- **Acotado por:** `idusuariogerentenotificado` — el ejecutivo ve **aquellas de las que fue
  destinatario**

**⚠️ `estado_envio` no se expone.** La columna existe en el esquema pero **ningún código la
escribe**; devolverla sería presentar un dato que siempre está vacío como si significara algo. Por
eso el listado de «notificaciones con envío fallido» quedó fuera de alcance.

\* Identificadores de uso interno para resolver catálogos y componer el cursor. **No se muestran**
(`design-system.md` §8).

---

## 4. Reglas transversales

**Acotamiento.** Resuelto en `core/informes/acotamiento.py` (research D2). Administrador ve todo;
Gerente queda forzado a lo suyo; pedir lo ajeno es **negativa explícita**, nunca sustitución
silenciosa. Cualquier otro rol, negativa.

**Resolución de catálogo.** Dos consultas y unión en memoria — sin JOIN. Traduce etiquetas, no
calcula métricas.

**Centinelas.** El cliente de la base ya devuelve ausencia de valor para los centinelas de texto y
de entero. Un prospecto sin ejecutivo y una asignación sin responsable previo llegan correctamente
como «no hay», y **se muestran** en vez de ocultarse (research D7).

**Paginación.** Keyset, `limit + 1` para detectar página siguiente. Nunca desplazamiento por
posición.

**Retraso de ingesta.** 5–15 s. Un prospecto recién reasignado puede seguir mostrando su ejecutivo
anterior. No se compensa.

---

## 5. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|42", "limit": 50, "has_next": true },
    "filtros": { "estado": "perdido", "canal": "inbound" },
    "acotado_a": "propios"
  }
}
```

`acotado_a` declara si el resultado está limitado a la titularidad del solicitante (`propios`) o
abarca a todos (`todos`). Sin él, un Gerente no puede distinguir «no hay prospectos perdidos» de
«no hay prospectos perdidos **míos**» — que es justo la ambigüedad que la negativa explícita de
FR-008 pretende evitar.

---

## 6. Resumen

| # | Listado | Tabla | Tipo | Acotado por | Cuidado |
|---|---|---|---|---|---|
| L1 | Cartera de prospectos | `Dim_Prospecto` | Estado actual | Ejecutivo asignado | ⚠️ perdido ≠ inactivo · sin datos de contacto |
| L2 | Reasignaciones | `Fact_Asignacion` | Período opcional | — | Responsable previo ausente en la 1.ª |
| L3 | Demos activas | `Dim_Prospecto` | Estado actual | Ejecutivo asignado | ⚠️ filtro en dos pasos · página corta |
| L4 | Notificaciones enviadas | `Fact_NotificacionVentas` | Período opcional | Ejecutivo destinatario | ⚠️ `estado_envio` no se expone |
