# Research — Informes Tácticos Simples de Red Operativa (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el código y el esquema reales. La primera es la más importante:
el eje de acotamiento por organización **no generalizó limpiamente**, y conviene saber por qué.

---

## D1 — «Pertenecer a una organización» significa dos cosas distintas en el código ⚠️

**Hallazgo.** La misma pregunta —¿a qué organización pertenece este usuario?— tiene **dos respuestas
incompatibles** según qué departamento la haga:

| Criterio | Dónde | Quién resuelve |
|---|---|---|
| **Ser administrador local de la cuenta** | `red_operativa/services/proveedor_access_service.py:23` (`find_by_admin_local`), y `suscripciones` que lo importa | **Solo una persona por cuenta** |
| **Estar vinculado a la cuenta** | `soporte_cliente/services/cliente_lookup_service.py:14` y `seguimiento/views/cliente_expediente_views.py:70`, sobre la tabla de vínculos | **Cualquier miembro** |

El módulo de Suscripciones se planificó suponiendo el segundo criterio. **La implementación que
importa usa el primero.** Con el criterio estricto, un empleado de una empresa proveedora que no sea
el administrador local **no resolvería a ninguna cuenta** y recibiría un rechazo en todos los
listados.

**Decisión.** El resolutor transversal acepta el criterio de pertenencia como **parámetro
explícito**, no lo fija. Cada listado declara cuál usa:

- **Red Operativa y Suscripciones** → administrador local, para no ampliar en un informe el acceso
  que la pantalla operativa restringe.
- **Soporte** (cuando llegue) → vínculo a la cuenta, por la misma razón invertida.

**Rationale.** La regla del contrato común es que **un informe nunca sea más amplio que la pantalla
operativa del mismo dato**. Como las pantallas operativas de estos departamentos usan criterios
distintos, unificar el resolutor a un solo criterio rompería esa regla en un departamento u otro.
Parametrizarlo es lo que permite respetar ambas.

**Alternativas descartadas.**
- *Unificar al criterio amplio (vínculo)* — ampliaría en informe el acceso que Red Operativa y
  Suscripciones restringen en pantalla. Es exactamente la puerta trasera que la regla prohíbe.
- *Unificar al criterio estricto (administrador local)* — dejaría sin acceso a los usuarios de
  Soporte que hoy sí lo tienen.

> **La generalización de Suscripciones quedó corta, y esto lo demuestra.** El eje «organización» se
> diseñó allí como si la pertenencia fuese un concepto único. No lo es. Corregirlo ahora, con dos
> departamentos que lo usan, es barato; hacerlo con cinco no lo habría sido.

---

## D2 — La disponibilidad de una unidad no cabe en un listado ⚠️

**Hallazgo.** `Dim_UnidadEmergencia` **no tiene columna de estado operativo**. Los cuatro estados
—`Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`
(`core/repositories/despacho/historial_estado_unidad_repository.py:13-17`)— viven **solo en el
histórico**, y se obtienen con `get_current_estado()`, que hace **una consulta por unidad**
(`list_by_unidad(id, limit=1)`).

**Decisión.** El listado de flota informa de **composición**: placa, tipo, capacidad, proveedor,
ubicación y condición de **alta o baja**. **No incluye disponibilidad operativa.** La respuesta
declara su propio alcance (FR-008).

**Rationale.** Incluirla exigiría N+1 consultas por página, o agregar el histórico para quedarse con
el último registro por unidad y volver a cruzar — compuesto en ambos casos.

**Y la razón de fondo, que no es de rendimiento:** `activo` significa **existe**, no **puede
acudir**. Un listado filtrado por `activo = true` y presentado como flota disponible contaría
unidades fuera de servicio, ocupadas o ya en camino a otro accidente. En los tres módulos anteriores
un error así inflaba una cifra comercial; **aquí produce una decisión de cobertura sobre unidades
que no pueden atender nada.**

**Alternativa descartada.** *Incluir el estado aceptando N+1 consultas* — degradaría el listado por
debajo del objetivo de 2 s con flotas grandes, y seguiría siendo la respuesta correcta a la pregunta
equivocada: el estado que devolvería es el del instante de la consulta, no el de cuando el
consumidor lo lea.

---

## D3 — La jerarquía geográfica ya tiene resolución por lotes

**Hallazgo.** `core/repositories/accidentes/ubicacion_catalogo_repository.py:72-81` ya resuelve la
cadena por lotes: `WHERE idciudad IN (…)` y `WHERE idcondado IN (…)`, no una consulta por fila.

**Decisión.** Se reutiliza ese patrón. Para una página de unidades: una consulta de condados con el
conjunto de identificadores distintos, y una de ciudades si hiciera falta. **Dos consultas de
catálogo por página**, independientemente del número de filas.

**Rationale.** Era el riesgo que la spec anotaba —una consulta por fila haría inviable el objetivo de
2 s— y resulta que el repositorio ya lo resolvió para el registro de accidentes. Reutilizar supera a
inventar, y además mantiene una sola forma de nombrar la geografía en todo el sistema.

**Nota.** La unidad se ubica por **condado** (`Dim_UnidadEmergencia.idcondado`), no por ciudad ni
calle. La cadena a resolver es más corta de lo que la spec temía: condado y, para contexto, el
estado geográfico al que pertenece.

---

## D4 — Los estados de región son cinco, y dos significan lo contrario de lo que parecen

**Hallazgo.** Los estados que el código maneja son:

| Estado | Dónde se fija | Significa |
|---|---|---|
| `En_Validación` | protocolo de validación | Aún no opera |
| `Producción` | aprobación del Director Tecnológico | Opera con normalidad |
| `En_Alerta` | `despublicacion_automatica_service.py:23` | **Opera, pero con cobertura degradada** |
| `Despublicada` | manual o automática | Ya no opera |
| Rechazo definitivo | `remediacion_region_service.py:39` | Descartada tras validación fallida |

**Decisión.** El listado expone los cinco y **no agrupa `En_Alerta` con `Despublicada`**.

**Rationale.** `En_Alerta` es una región **operativa** cuya cobertura se degradó — es candidata a
despublicarse, no despublicada. Agruparlas ocultaría exactamente la ventana en la que OT13 puede
actuar: retirar una región *antes* de que se quede sin continuidad. Es la misma clase de error que
confundir «en disputa» con «impaga» en Suscripciones.

---

## D5 — Una baja forzada dejó un accidente sin unidad

**Hallazgo.** `apps/red_operativa/services/baja_unidad_service.py:16-17` define dos tipos:
`Normal` y `Forzada_con_reasignación`, y el segundo se fija **cuando la unidad tenía un despacho
activo**, guardando además el identificador del caso afectado.

**Decisión.** El listado de bajas distingue ambos tipos y devuelve **el caso afectado** en las
forzadas, como ausencia en las normales.

**Rationale.** No es una etiqueta descriptiva: es la traza de impacto que el SRS exige. Una baja
forzada significa que un accidente se quedó sin la unidad que lo atendía y hubo que reasignar. Un
listado que sumara ambos tipos convertiría un incidente operativo en una estadística de rotación de
flota.

---

## D6 — Qué se expone de una unidad, y qué no

**Hallazgo.** `Dim_UnidadEmergencia` contiene `contactoproveedor`, además de `latitud` y `longitud`
—la **última posición conocida** de la unidad—.

**Decisión.** El listado expone placa, tipo, capacidad, proveedor, condado y condición de alta.
**No expone la posición ni el contacto.** Columnas enumeradas, prohibido `SELECT *`.

**Rationale.** La constitución trata la geolocalización como dato sensible sujeto a control de
acceso y auditoría (Principio V y Restricciones adicionales). La posición de una unidad no aporta
nada a un listado de composición de flota —para seguir una unidad en tránsito existe el módulo de
seguimiento, con su propio control—, así que exponerla sería ampliar la superficie sin ganancia. El
contacto del proveedor es dato personal por el mismo criterio aplicado en Ventas y CRM.

---

## D7 — Formas de cursor y tipo de cada listado

Se reutiliza la paginación keyset. Nada nuevo.

| Listado | Tipo | Orden por defecto | Cursor |
|---|---|---|---|
| Flota | Estado actual | `idunidademergencia DESC` | Escalar |
| Bajas de unidad | **Período opcional** | `fechahora DESC` | Compuesto `fecha\|idbajaunidad` |
| Regiones | Estado actual | `idregionoperativa DESC` | Escalar |
| Intentos de validación | **Período opcional** | `fechahora DESC` | Compuesto `fecha\|idvalidacionregion` |

**Nota sobre «regiones detenidas más de N días».** Se resuelve con la fecha de última actualización
de la región traducida a fecha de corte, que viaja al filtro. El número de días se calcula en el
servicio con reloj inyectable, como en los módulos anteriores.
