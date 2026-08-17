# Data Model — OE4, Inteligencia Predictiva

**Fecha:** 2026-08-16 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../002-tactico/modelo-analitico/) y le añade **dos
columnas a un hecho existente**. Ninguna tabla nueva.

---

## 1. Lo que se consume

| Tabla | Tipo | ¿`FINAL`? | Qué aporta |
|---|---|:--:|---|
| `hecho_accidente` | Instantánea acumulada | **Sí** | Completitud, descarte, fusión, impacto humano y vial, enriquecimiento |
| `hecho_evidencia` | Transacción | **No — falla** | Foto y nota por separado, y la categoría de la nota |
| `dim_geografia` | Dimensión | **Sí** | Jerarquía calle → ciudad → condado |
| `dim_severidad` | Dimensión | **Sí** | El orden por gravedad |

**No se lee `dim_region`** (#38) ni `dim_unidad`: OE4 mide el **expediente**, no la flota.

**Y se retira una fuente:** `indice_calidad_historico` deja de ser fuente de nada. Se conserva **solo
para contraste** mientras dure la migración.

---

## 2. Las dos ampliaciones

Ambas siguen el §4.bis del contrato de esquema. **Las dos son `ALTER TABLE … ADD COLUMN` sobre
`hecho_accidente`**, sin recargar los otros hechos.

```sql
ALTER TABLE hecho_accidente ADD COLUMN distancia_millas Nullable(Float64);
ALTER TABLE hecho_accidente ADD COLUMN condicion_clima  Nullable(String);
```

### 2.1 `distancia_millas` — desbloquea E4-13

**Origen:** `Fact_Accidente.distanciamillas`. Medido: **4 200 de 4 252 casos (98,8 %)**.

⚠️ **`Nullable`, nunca con valor por defecto.** Las filas cargadas antes de que la métrica existiera
no tienen el dato. Rellenarlas con `0` hundiría el promedio de extensión afectada y presentaría «no
lo medíamos» como «no hubo afectación» — en un informe que **se vende a municipios**.

### 2.2 `condicion_clima` — completa E4-06, con su escasez

**Origen:** `Dim_ElementoClimaticosAccidente` → `Dim_EstadosClimas.condicionclima`.

Medido: **3 casos de 4 252 (0,07 %)**, cada uno con exactamente **un** elemento climático.

**Por qué desnormalizada y no una dimensión.** Es el criterio con el que Emergencias resolvió las
escaladas de severidad: una fuente de tres filas no justifica una tabla, un flujo y un DAG. Una
columna en la carga existente cuesta casi nada.

> ⚠️ **La cardinalidad de hoy es 1:0..1, y el modelo del origen permite 1:N.** Una columna
> desnormalizada **elegiría uno en silencio** el día que un accidente tenga dos condiciones. Por eso
> la carga lleva una **prueba que falla si algún caso tiene más de un elemento climático**: convierte
> ese cambio en un fallo visible que obliga a rediseñar con un puente, en vez de en una cifra
> plausible.

---

## 3. Los nueve informes construibles

### US1 — la calidad del histórico *(4)*

| # | Informe | Grano de salida | Fuente | Medidas |
|---|---|---|---|---|
| **E4-01** | Índice consolidado de calidad | período | `hecho_accidente` × `hecho_evidencia` | 4 componentes **+** índice |
| **E4-02** | Completitud de campos críticos | período *(× condado)* | `hecho_accidente` | casos, completos, %, campos comprobados |
| **E4-03** | Campos con mayor tasa de ausencia | campo | `hecho_accidente` | ausencias y % **por campo** |
| **E4-04** | Calidad por origen: central vs campo | período × origen | `hecho_accidente` × `hecho_evidencia` | completitud comparada |

**La fórmula del índice de E4-01**, descifrada del legado y conservada:

```
índice = ( completitud + (1 − descarte) + (1 − fusión) + cobertura_evidencia ) / 4
```

⚠️ **Es una media sin ponderar**, así que la cobertura de evidencia pesa igual que la completitud de
campos críticos. Es discutible —un expediente sin severidad es peor que uno sin foto— y **no se
cambia aquí**: cambiar la fórmula y migrar el informe a la vez haría imposible saber cuál de los dos
movió las cifras.

**Y las cuatro componentes se publican por separado.** Un índice único dice que la calidad bajó y no
dice por qué, que es lo único accionable.

**La cobertura de evidencia se define explícitamente**: `con_foto`, `con_nota` y `con_ambas`, por
separado. Es lo que el legado no permite saber, y la causa de que sus cifras no se puedan reproducir
(research D2).

**E4-03 incluye todos los campos críticos, también los que no fallan nunca**, con cero. Un campo que
sale de la lista se confunde con un campo que nadie revisó.

### US2 — la inteligencia vendible *(4, los cuatro completos)*

| # | Informe | Grano de salida | Fuente | Medidas |
|---|---|---|---|---|
| **E4-05** | Concentración de siniestralidad | condado · ciudad · calle | `hecho_accidente` × `dim_geografia` | casos, top N, % acumulado |
| **E4-06** | Patrón horario y climático | franja × día · condición | `hecho_accidente` | casos por franja **y por condición** 🆕 |
| **E4-12** | Impacto humano por zona | período × severidad × condado | `hecho_accidente` | víctimas, heridos, fallecidos, casos con dato |
| **E4-13** | Impacto vial por zona | período × condado | `hecho_accidente` | duración y **distancia** 🆕 |

**Es el bloque que se vende**, y eso sube el listón de dos cosas:

1. **Ninguna ubicación por coordenadas.** Un mapa de siniestralidad con coordenadas exactas vendido a
   un tercero es una fuga con destinatario comercial.
2. **«Cero» y «no registrado» nunca se confunden.** E4-12 publica `casos_con_dato` como denominador
   real. Sumar los no registrados como ceros haría **bajar** el impacto humano total cada vez que
   empeora la calidad del registro — el indicador se movería al revés que la realidad.

⚠️ **E4-06 declara la escasez de su mitad climática.** Con 3 casos de 4 252, la parte climática **no
es un patrón**. La parte horaria tiene los 4 252 y sí lo es. La respuesta lo distingue.

### US3 — la aptitud del histórico *(1 construible)*

| # | Informe | Grano de salida | Fuente | Medidas |
|---|---|---|---|---|
| **E4-15** | Cobertura del histórico por zona | condado | `hecho_accidente` × `dim_geografia` | casos, umbral, **sin masa crítica** |

**El umbral es un parámetro y se publica en la respuesta.** Un «esta zona no tiene masa crítica» sin
decir contra qué umbral no es accionable. Referencia inicial: 500. Con los datos de hoy —2 158 y
2 094 casos— **ninguna zona se marca**, y esa es la respuesta correcta.

---

## 4. Los seis bloqueados

**Ninguno se publica** (`FR-OE4-021`).

| # | Informe | Prerrequisito | Historia |
|---|---|---|:--:|
| **E4-14** | Latencia de ingesta al analítico | Una marca de **primera aparición** por fila que sobreviva a la recarga idempotente | US3 |
| **E4-07** | Precisión del modelo *(BSC ≥80 %)* | `registro_modelos` | US4 |
| **E4-08** | Contraste predicción vs ocurrencia | `registro_predicciones` | US4 |
| **E4-09** | Unidades preposicionadas *(BSC ≥60 %)* | `registro_predicciones` | US4 |
| **E4-10** | Versiones del modelo | `registro_modelos` | US4 |
| **E4-11** | Productos de inteligencia *(BSC)* | `catalogo_productos_inteligencia` | US4 |

⚠️ **E4-14 cambió de bando en `/plan`.** No falta el dato: **la regla de idempotencia del modelo
impide medirlo**. Cada recarga hace `DROP PARTITION` e inserta de nuevo, así que `cargado_en` se
reescribe entero y nunca puede decir cuándo estuvo disponible un caso por primera vez. Medido: las
4 252 filas comparten el mismo `cargado_en`. Ver research D5.

> **Tres indicadores del BSC de este objetivo quedan sin fuente**: precisión del modelo, unidades
> preposicionadas y productos de inteligencia. Los tres son de la perspectiva de Aprendizaje y
> crecimiento, que es la de OE4. **El objetivo solo puede cubrir hoy la mitad de su propio tablero.**

---

## 5. Entidad de salida

La forma común de la capa. Lo propio de OE4:

| Campo | Qué es |
|---|---|
| **Claves de agrupación** | `periodo` + una o dos de: `condado` · `ciudad` · `calle` · `severidad` · `franja` · `campo` · `origen` |
| **Denominador** | Obligatorio con todo porcentaje. En E4-12, `casos_con_dato` |
| **Cobertura** | `parcial` cuando la muestra no sostiene la lectura — E4-06 climático, E4-11 |
| **Umbral** | E4-15 publica el suyo |

### Los objetivos de OE4

| Informe | Meta | Tipo | `cumple` |
|---|---|---|:--:|
| **E4-02** Completitud | ≥97 % | `CALIBRAR` | **`null`** |
| Los demás | — | — | sin objetivo |

⚠️ **Ningún `cumple` booleano en este módulo.** A diferencia de OE3, todas las metas de OE4 son
`[CALIBRAR]`, y las tres `[NORMATIVO]`-equivalentes de su tablero están bloqueadas. **Aquí sí aplica
la prueba transversal de OE6.**

---

## 6. Reglas de consulta heredadas

| Regla | Qué obliga aquí |
|---|---|
| **1 — ninguna tabla propia** | Se cumple: las dos ampliaciones son **columnas de un hecho existente** |
| **2 — versión final** | Obligatoria en `hecho_accidente`, `dim_geografia`, `dim_severidad`. **Prohibida** en `hecho_evidencia` |
| **3 — intentos ≠ casos** | No aplica: OE4 no lee `hecho_despacho` |
| **4 — ausencia ≠ cero** | Es **la regla central de este módulo**: víctimas no registradas, calificación sin registrar, campos sin dato y métricas nuevas en filas antiguas |
| **5 — historia o presente** | No aplica: no se agrupa por atributo versionado |
| **6 — desde cuándo es fiable** | ⚠️ Aplica a las **dos métricas nuevas**: E4-13 y E4-06 deben declarar desde cuándo existe su dato |
| **7 — filtrar por partición** | Toda consulta filtra `fecha`. E4-15 recorre el histórico entero, así que aquí pesa |
| **8 — sin dato sensible** | Reforzada: **estos informes se venden a terceros** |

---

## 7. Lo que este módulo NO cambia

| Se pidió | No se añade | Motivo |
|---|---|---|
| `registro_predicciones`, `registro_modelos`, `catalogo_productos_inteligencia` | Nada | Pertenecen al módulo operativo `predictive-ai-accident-rate`, no a esta capa |
| Marca de primera aparición por fila | Nada | Sería una **excepción a la regla de idempotencia**, que excede a este módulo |
| Eje de región | Nada | #38. E4-15 agrupa por condado |
| Dimensión de clima | Nada | 3 filas de origen. Se resuelve con una columna desnormalizada |
