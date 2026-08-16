# Research — Informes Compuestos de Red Operativa

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Seis decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — Versionar la región reutiliza el mecanismo, no lo amplía ⚠️

**Hallazgo.** El ciclo de vida de una región —Definida, En validación, Producción, Despublicada—
vive en **una sola columna** de `Dim_RegionOperativa`, sin fecha y sin historial. Es el mismo caso,
letra por letra, que unidad→proveedor.

Y el catálogo de informes se apoyaba en la tabla equivocada: `Dim_RegionOperativaEstadoRegion` no
guarda estados de ciclo de vida sino la relación región ↔ **estado geográfico** (su `idestadoregion`
apunta a `'Ciudad de Mexico'`).

**Decisión (del usuario, 2026-08-14).** Versionar la región con el **mecanismo ya construido**:
`dags/lib/dimensiones/versionado.py`, sin modificarlo.

**Rationale.** Que sirva a una segunda entidad sin tocarlo es **la prueba de que es genérico**. Si
hubiera que adaptarlo, no sería un mecanismo sino una solución particular con nombre general — y la
tercera entidad volvería a pagarlo.

Las tres propiedades que la región hereda gratis:

1. Una versión nueva **solo si el estado cambió**; recargar sin cambios no escribe nada.
2. La primera versión **abre por la izquierda** y cubre todo el pasado, en vez de dejar los hechos
   anteriores sin versión que los cubra.
3. `inicio_es_real = 0` declara que esa fecha **no es un cambio observado**.

**Lo que no entrega, dicho claro.** El pasado no se reconstruye. No habrá despublicaciones anteriores
a la primera carga — no porque no ocurrieran, sino porque nadie las guardó (FR-034).

**Alternativa descartada.** *Reconstruir desde `Dim_ValidacionRegion`* — registra intentos de
validación, no cambios de estado. Una región puede despublicarse sin que medie validación alguna, así
que la historia reconstruida sería **plausible e incompleta**, que es peor que declararla ausente.

---

## D2 — Los estados de unidad se agrupan por texto, no uniendo con su catálogo ⚠️

**Hallazgo.** `Dim_EstadoUnidadEmergencia` define **3** estados: Activa (1), Ocupada (2), Fuera de
servicio (3). `Fact_HistorialEstadoUnidad` usa además **`idestadounidademergencia = 4`**
(«En Misión») en **6 de sus 45 transiciones**, y una fila con `estadonuevo` nulo.

**Decisión.** Los informes agrupan por el **texto que registró la operación**, que
`hecho_estado_unidad` ya copia. **No se crea una dimensión de estado de unidad**, y ninguna consulta
une con el catálogo del origen.

**Rationale.** Unir con el catálogo es lo correcto en un modelo bien formado, y aquí **pierde el
13 % de las transiciones sin que nada falle**: una unión interna las descarta y una externa las deja
sin etiqueta. Crear la dimensión desde un catálogo incompleto propagaría el hueco al modelo, donde
sería más difícil de ver.

**Alternativa descartada.** *Completar el catálogo en el modelo, añadiendo el estado 4* — el modelo
estaría inventando un catálogo que el sistema operativo no tiene, y la discrepancia dejaría de verse
justo donde hay que arreglarla: en el origen.

**Lo que no resuelve este módulo.** Que el catálogo esté incompleto es un defecto de la capa
operativa. Queda anotado en el catálogo global de informes.

---

## D3 — Qué merece un hecho y qué no

**Hallazgo.** Siete informes necesitan datos que el modelo no tiene: bajas de unidad, validaciones de
región, vecindad entre condados, alta de unidad y el ciclo de vida de la región.

**Decisión.**

| Dato | Forma en el modelo | Por qué |
|---|---|---|
| Baja de unidad | **Hecho de transacción** | Tiene instante propio, tipo y motivo; su grano no es la unidad |
| Validación de región | **Hecho de transacción** | Ídem: una región tiene varios intentos, y el ordinal es lo que mide la tasa al primer intento |
| Región y su ciclo de vida | **Dimensión versionada** | Es una entidad con estado que cambia |
| Vecindad entre condados | **Atributo de `dim_geografia`** | Es una relación estática entre entidades ya modeladas |
| Alta de unidad | **Columna de `dim_unidad`** | Es un atributo de la unidad, no un suceso con vida propia |

**Rationale.** La regla del §4.bis: si pertenece a una entidad ya modelada, es una columna. Un hecho
se justifica cuando hay **un instante propio y un grano distinto**. La baja y la validación lo tienen;
el alta y la vecindad, no.

**Alternativa descartada.** *Un hecho de vecindad* — sería una tabla de dos filas sin instante, con
un flujo y un DAG. Coste sin retorno.

---

## D4 — La disponibilidad se mide en tiempo, no en transiciones ⚠️

**Hallazgo.** `hecho_estado_unidad` guarda `segundos_en_estado_anterior`, calculado al cargar. La
tentación es medir disponibilidad contando transiciones a «Activa».

**Decisión.** La disponibilidad declarada es **la fracción del período en que la unidad estuvo
Activa**, sumando duraciones. Y el tiempo en el **estado vigente al final del período** cuenta
**hasta el fin del período**, no hasta el último cambio.

**Rationale.** Contar transiciones mide agitación, no disponibilidad: una unidad que alternó veinte
veces no es más disponible que una que estuvo activa todo el mes sin moverse.

Lo del último tramo no es un detalle: una unidad activa desde el día 1 y sin cambios **no tiene
ninguna transición dentro del período**. Medida por transiciones, su disponibilidad sería 0 % —
exactamente al revés de la verdad.

**Y una unidad sin ninguna transición conocida** queda con disponibilidad **ausente**, no 0 %: no se
sabe en qué estado estuvo (FR-008).

**Alternativa descartada.** *Contar el último estado conocido y extrapolarlo al período entero* —
convierte un dato desconocido en una afirmación, que es la clase de mentira que este modelo persigue.

---

## D5 — El umbral de cobertura crítica lo pone el informe

**Hallazgo.** El sistema operativo **no define ningún umbral de cobertura**:
`Dim_ParametrosDespacho` tiene **0 filas**, igual que `Dim_ParametrosSeguimiento`.

**Decisión.** El umbral es **parámetro de la consulta**, con **1 unidad disponible por condado** por
defecto, y se documenta como criterio del informe, no como política de la empresa.

**Rationale.** Es coherente con D3 del modelo —los parámetros son de la pregunta, no de la carga— y
evita el error que ya cometió el informe de pérdida de señal: hornear el umbral en el flujo, de modo
que cambiarlo exigía recargar la tabla entera.

**La honestidad importa aquí.** Un informe titulado «condados en cobertura crítica» sugiere que
alguien definió qué es crítico. Nadie lo hizo: el valor por defecto es una convención de este
informe, y debe decirlo.

---

## D6 — El segundo departamento debe costar menos que el primero

**Hallazgo.** Emergencias construyó el cargador de consultas, el repositorio de lectura, la
resolución de período, los permisos y las pruebas transversales de las dos reglas que no avisan.

**Decisión.** Este módulo **no crea ninguna pieza de infraestructura**. Solo aporta sus consultas,
sus dos dimensiones, sus dos hechos y sus endpoints.

**Rationale.** Es la comprobación de la tesis del modelo. Si el segundo departamento necesitara
inventar plomería propia, el patrón no escalaría a los seis restantes, y los 108 informes del
catálogo volverían a ser 108 soluciones particulares.

**Consecuencia sobre el orden de trabajo.** Este módulo **depende de que las fases 1 y 2 de
Emergencias estén implementadas**. No de sus informes —ninguno— sino de su plomería. Es la única
dependencia entre departamentos, y conviene que sea explícita.
