# Data Model — Informes Tácticos Simples de Emergencias (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Fact_Accidente` | Entidad principal | L1 |
| `Fact_Despacho` | Entidad principal | L2 |
| `Dim_EvidenciaFoto` | Entidad principal | L3 |
| `Dim_NotaAccidente` | Entidad principal | L4 |
| `Fact_CierreAccidente` | Entidad principal | L5 |
| `Dim_Severidad`, `Dim_Calle`, `Dim_Ciudad`, `Dim_Condado`, `Dim_TipoReportado` | Catálogos | L1 |
| `Dim_UnidadEmergencia`, `Dim_OrigenDespacho` | Catálogos | L2 |
| `Dim_Usuarios` | Catálogo | L3, L4 |
| `Dim_Preferencias_Cliente` | Acotamiento | L1 |

### Tablas deliberadamente NO leídas

| Tabla | Por qué |
|---|---|
| Histórico de estados del caso | El estado formal es compuesto; el caso guarda lo suficiente (§2) |
| Histórico de estados del despacho | Ídem: las horas del despacho bastan (§4, L2) |
| `Dim_Conductor`, `Dim_Implicado`, `Dim_Vehiculo`, `Fact_Conductor_Accidente` | Identidad de personas implicadas — dato sensible |

---

## 2. El caso no guarda su estado, pero guarda lo suficiente

`Fact_Accidente` **no tiene columna de estado**. El estado formal vive en su histórico y exige el
último registro por caso — compuesto, y ya cubierto por los informes agregados.

**Pero tres columnas del propio caso bastan para distinguir las tres situaciones:**

| Situación | `activo` | `horafin` | `idaccidenteorigen` |
|---|:--:|:--:|:--:|
| **En curso** | ✅ | — | — |
| **Cerrado** | ❌ | ✅ | — |
| **Fusionado** (duplicado) | ❌ | — | ✅ |
| **Descartado** (falsa alarma) | ❌ | — | — |

**El listado devuelve los tres hechos, no un estado inferido.** La exclusividad entre cerrado,
descartado y fusionado la garantiza el módulo de fusión, no este; devolver un campo calculado ataría
este listado a una regla que no controla, y empezaría a mentir el día que cambiara.

> Un recuento de «casos inactivos» sin distinguir sumaría **emergencias atendidas, falsas alarmas y
> duplicados**: el trabajo realizado y el ruido descartado como la misma cosa.

---

## 3. El eje de acotamiento: cobertura contratada

Es el **cuarto eje** de la serie, y el único que no acota por titularidad.

| Solicitante | Alcance |
|---|---|
| **Rol interno** (Operador, Administrador) | Todos los casos, en cualquier situación |
| **Cliente** | **Solo casos cerrados**, y **solo de sus zonas contratadas** |
| **Cliente sin zonas** | **Resultado vacío** — nunca el listado completo |
| Otros roles | Negativa |

**Cómo se resuelve** (research D1): las zonas contratadas se traducen a un **conjunto de calles**
antes de consultar, encadenando catálogos —condado → ciudades → calles—, y el conjunto viaja al
filtro. Es el patrón que el sistema ya documenta como estándar para resolver un nivel geográfico.

**No se comprueba la zona fila a fila.** El módulo operativo lo hace así hoy, y es lo que la spec
descartó: no es un filtro, y el trabajo por fila incluye resolver la ubicación.

---

## 4. Los cinco listados

### L1 — Casos · `FR-001`, `FR-002`, `FR-006`–`FR-008` · OT21/OT25

- **Tabla:** `Fact_Accidente`
- **Campos:** `idaccidente`* (número de caso, **sí se muestra**: es lenguaje de negocio),
  `severidad`, `calle`, `ciudad`, `condado`, `tipo_reportado`, `num_vehiculos`, `num_heridos`,
  `num_victimas`, `num_fallecidos`, `fechahoraaccidente`, `activo`, `horafin`, `duracion_minutos`,
  `duplicado_de`
- **⛔ No expuestos:** `latitudinicio`, `longitudinicio` — coordenadas del accidente, dato sensible
  (research D4). **Columnas enumeradas.**
- **Orden:** `fechahoraaccidente DESC` · **Cursor:** compuesto `fechahoraaccidente|idaccidente`
  ⚠️ El segundo componente es **texto**, no entero: convertirlo a `int` daría `400` en la segunda
  página y el listado sería inpaginable más allá de la primera.
- **Filtros:** `severidad`, `condado`, `ciudad`, `tipo_reportado`, `situacion`, `desde`, `hasta`
- **Tipo:** **hechos del período**
- **Acotado por:** zonas contratadas (§3)

**El filtro `situacion` combina los tres hechos de §2**: `en_curso`, `cerrado`, `duplicado`,
`descartado`.

> ⚠️ **`borrador` se retiró al implementar.** No es derivable de los tres hechos: un caso en borrador
> es indistinguible de cualquier otro caso activo. Vive en el histórico, que este listado no lee.
>
> Y **`cerrado` exige además que el caso no apunte a otro**: sin esa condición, un duplicado que
> conservara hora de fin saldría en los dos filtros y dejarían de ser conjuntos disjuntos — contando
> el mismo hecho dos veces, que es el defecto que §2 existe para evitar. **No hay campo «estado» en la respuesta**: van `activo`, `horafin` y
`duplicado_de` por separado.

**Un caso sin ubicación resoluble aparece** con calle, ciudad y condado ausentes (FR-026). No se
omite: es una anomalía real —y además nunca podrá acotarse a ninguna zona—.

---

### L2 — Despachos · `FR-003` · OT22/OT23

- **Tabla:** `Fact_Despacho`
- **Campos:** `iddespacho`*, `numero_caso`, `unidad`, `origen_despacho`, `fechahoradespacho`,
  `fechahorallegada`, `fechahoraretiro`, `retiro_forzado`, `en_transito`
- **Orden:** `fechahoradespacho DESC` · **Cursor:** compuesto `fechahoradespacho|iddespacho`
- **Filtros:** `origen`, `unidad`, `caso`, `en_transito`, `desde`, `hasta`
- **Tipo:** **hechos del período**
- **Acceso:** solo roles internos
- **Catálogo:** `idunidademergencia` → `Dim_UnidadEmergencia`; `idorigendespacho` →
  `Dim_OrigenDespacho`

**`en_transito` se deriva de las horas del propio despacho** (research D5): despachado, sin llegada y
sin retiro. **No se consulta el histórico de estados del despacho.**

**El retiro forzado se distingue del normal**: es la traza de que la central retiró a una unidad en
vez de que la unidad terminara su parte.

**Varios despachos por caso conviven**, cada uno con sus horas: un caso puede acumular intentos de
varios orígenes.

---

### L3 — Fotografías de evidencia · `FR-004`, `FR-024` · OT24 / OP40, OP42

- **Tabla:** `Dim_EvidenciaFoto`
- **Campos:** `idevidenciafoto`*, `numero_caso`, `autor`, `url`, `sincronizado`,
  **`hora_captura`**, **`hora_registro`**
- **Orden:** `fechahora DESC` · **Cursor:** compuesto `fechahora|idevidenciafoto`
- **Filtros:** `sincronizado`, `caso`, `autor`, `desde`, `hasta`
- **Tipo:** **hechos del período**
- **Acceso:** solo roles internos

**⚠️ La hora de captura es la del sitio**, y se devuelve tal cual. La hora de registro sale de la
**columna de sincronización propia** de esta tabla.

---

### L4 — Notas de campo · `FR-004`, `FR-024` · OT24 / OP40, OP42

- **Tabla:** `Dim_NotaAccidente`
- **Campos:** `idnotaaccidentes`*, `numero_caso`, `autor`, `nota`, `tipo`, `sincronizado`,
  **`hora_captura`**, **`hora_registro`**
- **Orden:** `fechahora DESC` · **Cursor:** compuesto `fechahora|idnotaaccidentes`
- **Filtros:** `sincronizado`, `tipo`, `caso`, `autor`, `desde`, `hasta`
- **Tipo:** **hechos del período**
- **Acceso:** solo roles internos

**⚠️ Asimetría con las fotografías** (research D3): la nota **no tiene columna de sincronización
propia**. Su hora de registro es la marca genérica de última modificación de la fila.

| | Hora de captura | Hora de registro |
|---|---|---|
| Fotografía | `fechahora` | columna de sincronización propia |
| **Nota** | `fechahora` | **marca genérica de modificación** |

Tomar la columna equivocada devolvería la hora de última modificación como si fuera la de captura, y
**el error sería invisible** en las notas registradas en línea —donde ambas coinciden—, apareciendo
solo en las capturadas sin conexión, que son justamente el caso que importa.

> **Deuda anotada.** Que la nota carezca de columna propia de sincronización es una asimetría del
> modelo. Mientras siga así, cualquier consulta sobre sincronización de notas depende de una columna
> genérica que una actualización futura pisaría.

---

### L5 — Cierres de caso · `FR-005`, `FR-025` · OT25 / OP45

- **Tabla:** `Fact_CierreAccidente`
- **Campos:** `idaccidente`* (número de caso), `resultado_atencion`, `calificacion`,
  `observaciones_finales`
- **Orden:** `idaccidente DESC` · **Cursor:** escalar
- **Filtros:** `resultado`, `sin_observaciones`, `con_calificacion`
- **Tipo:** **estado actual** — ver nota
- **Acceso:** solo roles internos

**⚠️ Una calificación ausente no es un cero** (research D6). En una escala, cero es el peor valor:
presentar «no se calificó» como «se calificó con la nota mínima» invertiría el significado, y un
promedio que incluyera esos ceros hundiría la media sin que nadie lo note.

**Nota sobre el período.** El registro de cierre **no tiene fecha propia**: la hora de fin vive en el
caso. Por eso se declara como listado de **estado actual** y no acepta rango genérico. Filtrar
cierres por fecha exige cruzar con el caso, y eso lo haría compuesto.

\* Los identificadores marcados son de uso interno **salvo el número de caso**, que es lenguaje de
negocio y sí se muestra (`design-system.md` §8).

---

## 5. Reglas transversales

**Resolución geográfica.** Se reutiliza el repositorio de catálogo que resuelve un nivel a un
conjunto de calles. Para el acotamiento: condados contratados → ciudades → calles, **una vez por
petición**, no por fila.

**Ni coordenadas ni identidad.** Ningún listado devuelve la posición del accidente ni lee las tablas
de conductores, implicados o vehículos (research D4).

**Centinelas.** El cliente de la base ya devuelve ausencia. Un caso sin hora de fin, un despacho sin
llegada, una calificación sin valor y unas observaciones vacías llegan como «no hay», y **se
muestran como ausentes**.

**Paginación.** Keyset, `limit + 1`.

**Retraso de ingesta.** 5–15 s. Un caso recién cerrado puede seguir apareciendo activo. No se
compensa.

---

## 6. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|ACC-1786569480560-3023", "limit": 50, "has_next": true },
    "filtros": { "severidad": 3, "situacion": "cerrado" },
    "acotado_a": "zonas_contratadas"
  }
}
```

`acotado_a` toma aquí un valor propio del eje: `zonas_contratadas` o `todos`. Sin él, un cliente no
puede distinguir «no hubo accidentes graves» de «no hubo accidentes graves **en mis zonas**».

---

## 7. Resumen

| # | Listado | Tabla | Tipo | Cuidado |
|---|---|---|---|---|
| L1 | Casos | `Fact_Accidente` | Período opcional | ⚠️ tres hechos, no un estado · ⛔ sin coordenadas · acotado por zona |
| L2 | Despachos | `Fact_Despacho` | Período opcional | En tránsito se deriva de las horas, no del histórico |
| L3 | Fotografías | `Dim_EvidenciaFoto` | Período opcional | ⚠️ hora de captura ≠ hora de registro |
| L4 | Notas de campo | `Dim_NotaAccidente` | Período opcional | ⚠️ ídem, **y con otra columna de origen** |
| L5 | Cierres | `Fact_CierreAccidente` | Estado actual | ⚠️ calificación ausente ≠ cero |
