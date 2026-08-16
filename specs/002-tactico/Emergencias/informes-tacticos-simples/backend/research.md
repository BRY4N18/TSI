# Research — Informes Tácticos Simples de Emergencias (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el código real. La primera resuelve el riesgo que podía eliminar
una historia entera.

---

## D1 — El acotamiento por zona sí es un filtro: el patrón ya existe ✅

**El riesgo que la spec dejó abierto queda descartado.**
`historial_emergencias_service.py:183` implementa `_resolver_calles_por_ubicacion`, y su propia
documentación lo declara como el patrón estándar del sistema:

> *«Mismo patrón de `AccidenteRepository.list_activos`: resuelve ciudad/estado a un set de `idcalle`
> sobre el que filtrar (Pinot no hace JOIN aquí).»*

Resuelve un nivel geográfico a un **conjunto de calles** encadenando catálogos —estado → condados →
ciudades → calles— y el repositorio filtra con ese conjunto en la consulta.

**Decisión.** El acotamiento por zonas contratadas usa **ese mismo patrón**: se resuelven los
condados contratados a un conjunto de calles **antes** de consultar, y el filtro viaja a la base.
**La User Story 1 se mantiene íntegra.**

**Rationale.** No hay que inventar nada: la cadena que hace falta —condado → ciudades → calles— es un
nivel más corta que la que el sistema ya resuelve para un estado completo. Si aquello es viable,
esto lo es con más razón.

**Incoherencia que conviene señalar.** El mismo fichero contiene las dos formas: el filtro por
ubicación usa el conjunto resuelto (bien), y el acotamiento del cliente resuelve el condado **fila a
fila mientras recorre** (`:87-93`). Son dos maneras de hacer lo mismo conviviendo a diez líneas de
distancia, y la segunda es la que la spec descartó.

**Riesgo residual, acotado.** El tamaño del conjunto depende de cuántos condados tenga contratados un
cliente. Está limitado por el negocio —nadie contrata «todas las zonas»— y el sistema ya construye
conjuntos mayores para filtrar por estado completo. **Se acepta**, con una prueba de rendimiento que
lo ejercite con varias zonas.

**Alternativa descartada.** *Mantener la comprobación fila a fila* — no es un filtro: el número de
filas recorridas crece cuando las zonas del cliente son escasas, y el trabajo por fila incluye
resolver la ubicación.

---

## D2 — El caso no guarda su estado, pero sí lo suficiente para distinguir las tres situaciones

**Hallazgo.** `Fact_Accidente` **no tiene columna de estado**. El estado formal vive en el histórico
de estados, y obtenerlo exige el último registro por caso — la misma forma que la disponibilidad de
una unidad y el motivo de una credencial inactiva.

**Pero sí guarda tres hechos que bastan:**

| Hecho registrado en el caso | Permite distinguir |
|---|---|
| `activo` | Si sigue en curso |
| `horafin` | Si terminó su atención |
| `idaccidenteorigen` | Si es duplicado, y de qué caso |

| Situación | Cómo se reconoce |
|---|---|
| **Cerrado** | Inactivo **con** hora de fin |
| **Fusionado** | Inactivo **apuntando** a otro caso |
| **Descartado** | Inactivo **sin** hora de fin **ni** caso origen |

**Decisión.** El listado devuelve los **tres hechos** y deja que el consumidor los lea. **No devuelve
un campo «estado» inferido**, y **no consulta el histórico**.

**Rationale.** Devolver un estado calculado a partir de esas tres columnas sería una **inferencia
presentada como dato**. Funcionaría hoy porque el sistema garantiza que cerrado, descartado y
fusionado son mutuamente excluyentes —lo declara `FusionarReportesService.PROHIBIDOS_PADRE`—, pero
esa garantía vive en otro módulo y podría cambiar sin que este se entere.

Devolver los hechos es más honesto y no pierde información: quien necesite el estado formal tiene los
informes agregados, que lo leen de donde está.

**Y la consecuencia de no distinguirlos** justifica el cuidado: un recuento de «casos inactivos»
sumaría **emergencias atendidas, falsas alarmas y duplicados**, presentando el trabajo realizado y
el ruido descartado como la misma cosa.

---

## D3 — Fotografías y notas no guardan la hora de subida igual ⚠️

**Hallazgo.** Los dos registros de evidencia son asimétricos:

| Registro | Hora de captura | Hora de subida |
|---|---|---|
| **Fotografía** | `fechahora` | `fecha_sincronizacion` — **columna propia** |
| **Nota de campo** | `fechahora` | `fecha_actualizacion` — **la marca genérica de la fila** |

La nota **no tiene columna de sincronización**. Su hora de subida es la marca de última modificación,
que es lo que la revisión anterior verificó: *«la nota capturada offline quedó con `fechahora` = hora
del sitio y `fecha_actualizacion` = hora de la subida, 131 s después»*.

**Decisión.** Los dos listados devuelven **hora de captura** y **hora de registro**, cada uno tomando
la segunda de donde le corresponde. Se documenta la asimetría en el contrato.

**Rationale.** Es la regla central del módulo de evidencia: la hora que vale es la del sitio, no la
de la subida. Tomar la columna equivocada en las notas devolvería la hora de la última modificación
como si fuera la de captura, y el error sería **invisible** en las notas registradas en línea —donde
ambas coinciden— apareciendo solo en las capturadas sin conexión, que son justamente el caso que
importa.

**Prueba obligatoria.** Una nota capturada sin conexión debe mostrar **dos horas distintas**; una
registrada en línea, dos horas iguales. Es el contraste que demuestra que no se está sellando la
hora de subida.

> **Anotar como deuda.** Que la nota no tenga columna de sincronización propia es una asimetría del
> modelo, no de esta spec. Mientras siga así, cualquier consulta sobre sincronización de notas
> depende de una columna genérica que cualquier actualización futura pisaría.

---

## D4 — Ni coordenadas ni identidad de personas

**Hallazgo.** `Fact_Accidente` guarda latitud y longitud del accidente. Las tablas de conductores,
implicados y vehículos guardan identidad, edad y estado de las personas.

**Decisión.** El listado de casos expone la ubicación **por nombre** —calle, ciudad, condado— y
**no** las coordenadas. Ninguno de los cinco listados lee las tablas de personas.

**Rationale.** La constitución trata la geolocalización y la identidad de las personas implicadas en
accidentes como dato sensible sujeto a control de acceso y auditoría, y lo dice de forma expresa en
sus restricciones adicionales. Un listado táctico responde *dónde y de qué gravedad*, no *en qué
coordenada exacta ni a quién*.

Es el mismo criterio aplicado a la posición de las unidades en Red Operativa, y aquí con más motivo:
un volcado de coordenadas de accidentes con severidad es un mapa de siniestralidad exportable.

---

## D5 — Una misión en tránsito es un despacho sin llegada ni retiro

**Hallazgo.** `Fact_Despacho` guarda `fechahoradespacho`, `fechahorallegada`, `fechahoraretiro` y
`retiro_forzado`. El estado del despacho vive aparte, en su propio histórico.

**Decisión.** El filtro «misiones en tránsito» se resuelve con las **horas del propio despacho**:
despachada, sin llegada y sin retiro. **No se consulta el histórico de estados del despacho.**

**Rationale.** Mismo criterio que D2: las horas son hechos del despacho; el estado formal no. Y
aquí la lectura es unívoca —una unidad despachada que no ha llegado ni se ha retirado está en
camino—, así que no hace falta inferir nada.

**El retiro forzado se distingue del normal** porque el despacho lo registra explícitamente. Es la
traza de que la central retiró a una unidad en vez de que la unidad terminara su parte.

---

## D6 — Una calificación ausente no es un cero

**Hallazgo.** El cierre de un caso admite calificación opcional. La base analítica convierte los
enteros vacíos en ausencia de valor, y el cliente ya lo traduce correctamente.

**Decisión.** La calificación ausente se devuelve **como ausente**, nunca como cero.

**Rationale.** En una escala de calificación, cero es el peor valor posible. Presentar «no se
calificó» como «se calificó con la nota mínima» invertiría el significado en el punto exacto donde
más engaña: un promedio de calificaciones que incluya los ceros de los casos sin calificar hundiría
la media sin que nadie lo note.

El cliente de la base ya devuelve ausencia para el centinela de entero, así que **no hace falta
código nuevo**; sí una prueba que lo fije.

---

## D7 — Formas de cursor y tipo de cada listado

Se reutiliza la paginación keyset. Nada nuevo.

| Listado | Tipo | Orden por defecto | Cursor |
|---|---|---|---|
| Casos | **Período opcional** | `fechahoraaccidente DESC` | Compuesto `fechahoraaccidente\|idaccidente` |
| Despachos | **Período opcional** | `fechahoradespacho DESC` | Compuesto `fechahoradespacho\|iddespacho` |
| Fotografías | **Período opcional** | `fechahora DESC` | Compuesto `fechahora\|idevidenciafoto` |
| Notas de campo | **Período opcional** | `fechahora DESC` | Compuesto `fechahora\|idnotaaccidentes` |
| Cierres | **Período opcional** | `idaccidente DESC` | Escalar |

**Nota sobre el cursor de casos.** `idaccidente` es texto —el número de caso—, así que el desempate
compara cadenas. Es determinista, que es lo único que el cursor necesita garantizar.

**Nota sobre los cierres.** El registro de cierre no tiene fecha propia: la hora de fin vive en el
caso. El listado ordena por caso y toma el rango de fechas de la hora de fin **del propio cierre
cuando exista**; si el filtro por período resultara imposible sin cruzar con el caso, se declara como
listado de estado actual. **A verificar en implementación.**
