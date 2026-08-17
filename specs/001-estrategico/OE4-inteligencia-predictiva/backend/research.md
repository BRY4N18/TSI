# Research — OE4, Registro Histórico como Ventaja Competitiva e Inteligencia Predictiva

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Todo lo de aquí se comprobó contra el stack levantado —`tactico-clickhouse` y el Pinot operativo— y
contra el código. Donde hay una cifra, se midió.

**Resultado neto: dos informes que la spec daba por parciales se completan, y uno que daba por
construible no lo es.** Los construibles pasan de 10 a 9, pero dos de ellos dejan de entregar la
mitad.

---

## D1 — La fórmula del índice legado, descifrada ✅

La spec asumía *«se toma la que `indice_calidad_historico` ya usa, salvo que la investigación
demuestre que está mal»*, sin saber cuál era. **Se dedujo de los datos**, y encaja en las seis filas
comprobadas sin un solo decimal de diferencia:

```
índice = ( completitud + (1 − descarte) + (1 − fusión) + cobertura_evidencia ) / 4
```

| Período | c | d | f | e | Índice legado | Fórmula |
|---|--:|--:|--:|--:|--:|--:|
| 2026-08-13 | 1 | 0 | 0,25 | 0,50 | 0,8125 | **0,8125** |
| 2026-08-12 | 1 | 0,25 | 0 | 1,00 | 0,9375 | **0,9375** |
| 2026-08-02 | 1 | 0,0857 | 0,0286 | 0 | 0,7214 | **0,7214** |

**Decisión:** se conserva la fórmula, con las **cuatro componentes publicadas por separado**
(`FR-OE4-008`). Cambiarla produciría una serie que parece continua con los 182 días ya calculados y
tiene un salto en medio, justo donde nadie mira.

**Lo que sí se documenta y el legado no dice:** es una **media aritmética sin ponderar**, así que la
cobertura de evidencia pesa lo mismo que la completitud de campos críticos. Es discutible —un
expediente sin severidad es peor que uno sin foto— pero **no se cambia aquí**: cambiar la fórmula y
migrar el informe a la vez haría imposible saber cuál de los dos movió las cifras.

---

## D2 — La divergencia de evidencia no se explica, y por eso el contraste era necesario ⚠️

La spec detectó que `pct_cobertura_evidencia` del legado no cuadra con el modelo, y **no afirmó** que
el legado estuviera mal. Se probaron **tres definiciones candidatas** y **ninguna reproduce el
legado**:

| Fecha | Legado | Solo foto | Solo nota | Foto **o** nota |
|---|--:|--:|--:|--:|
| 2026-08-13 | **0,50** | 0,00 | 0,25 | 0,25 |
| 2026-08-12 | **1,00** | 0,25 | 0,75 | 0,75 |
| 2026-08-02 | 0,00 | 0,00 | 0,00 | 0,00 |

El legado dice que 2 de 4 casos tenían evidencia el día 13 y 4 de 4 el día 12. En el modelo hay **3
fotografías y 51 notas en todo el histórico**, y ninguna combinación da esas cifras.

**Decisión:** E4-01 se migra a una consulta sobre el modelo con **definición explícita** —foto y nota
por separado, y su combinación—, y la prueba de contraste **declara la divergencia con su causa** en
vez de tolerarla o de dar por buena una de las dos.

**Por qué no se investiga más aquí.** Averiguar qué mide exactamente el legado exigiría reconstruir
un flujo que se va a retirar. El esfuerzo tiene mejor destino: publicar una definición que se pueda
leer en la consulta, que es lo que el legado no permite.

⚠️ **Y no se afirma que el legado esté mal.** Con tres fotografías en 4 252 casos, la diferencia son
dos y cuatro casos. Lo que sí se afirma es que **nadie puede saber cuál es correcta**, y eso ya es
motivo suficiente para sustituir una tabla precalculada por una consulta legible.

---

## D3 — E4-13 se completa: `distanciamillas` existe en el origen ✅

La spec lo daba por parcial —«solo duración»—. **Se comprobó y el dato está**:

```
SELECT COUNT(*) FROM Fact_Accidente WHERE distanciamillas > 0   →   4 200
```

**4 200 de 4 252 casos (98,8 %)** tienen distancia afectada. No es que el dato no exista: es que el
modelo analítico no lo cargó.

**Decisión:** añadir `distancia_millas Nullable(Float64)` como **métrica de `hecho_accidente`**,
siguiendo el §4.bis. `ALTER TABLE … ADD COLUMN`, sin recargar nada más.

⚠️ **Nullable y sin valor por defecto.** Las filas cargadas antes de que la métrica existiera no
tienen el dato, y rellenarlas con `0` hundiría cualquier promedio de extensión afectada y presentaría
«no lo medíamos» como «no hubo afectación».

**Por qué merece la pena:** E4-13 es uno de los dos informes que este objetivo **vende** —impacto
vial para municipios y Smart Cities—, y entregar solo la duración deja fuera la mitad del producto.
Con 98,8 % de cobertura, la mitad que falta es la que más se paga.

---

## D4 — E4-06 se completa estructuralmente, pero su dato es casi inexistente ⚠️

La spec lo daba por parcial porque `num_elementos_clima` es un recuento, no la condición. **La
condición sí existe en el origen**:

| Tabla del origen | Qué tiene | Filas |
|---|---|--:|
| `Dim_EstadosClimas` | `condicionclima`, temperatura, humedad, visibilidad, precipitación, viento | **3** |
| `Dim_ElementoClimaticosAccidente` | `idaccidente` → `idestadoclima` | **3** |

Y la cardinalidad en el modelo es **1:0..1**, no 1:N:

```
elementos_por_caso   casos
0                    4249
1                       3
```

**Decisión:** añadir `condicion_clima Nullable(String)` como **columna desnormalizada de
`hecho_accidente`**, no como dimensión ni como hecho puente.

**Por qué desnormalizada y no una dimensión.** Es el mismo criterio con el que Emergencias resolvió
las escaladas de severidad: *«su fuente tiene 1 fila para 4 252 casos. Un hecho, un flujo y un DAG
para eso es coste sin retorno.»* Aquí son 3 filas. Una columna en la carga existente cuesta casi
nada; una dimensión con su tarea y su sensor, no.

⚠️ **Y una prueba que falle si la cardinalidad cambia.** Hoy ningún caso tiene dos elementos
climáticos. Si mañana lo tuviera, una columna desnormalizada **elegiría uno en silencio**. La prueba
convierte ese cambio en un fallo visible que obliga a rediseñar con un puente, en vez de en una cifra
plausible.

**Lo que el informe podrá decir, y lo que no.** Con 3 casos de 4 252 (**0,07 %**), el patrón
climático **no es un patrón**. E4-06 entrega el patrón horario —que sí tiene los 4 252— y la parte
climática **con su escasez declarada**, igual que E4-11 con las escaladas.

**Alternativa descartada:** dejarlo parcial y no cargar el clima. Se descarta por el mismo criterio
que OE3 aplicó a los dos condados vecinos: *la escasez de datos se declara; la imposibilidad, no*. Y
el histórico va a crecer: cuando lo haga, el pipeline ya estará listo.

---

## D5 — E4-14 no es medible, y no por falta de datos ⛔

La spec lo daba por construible. **No lo es, y el motivo es estructural.**

E4-14 mide *«el retraso entre el hecho y su disponibilidad en el analítico»*, contra
`hecho_accidente.cargado_en`. Medido:

```
primera_carga:            2026-08-16 17:04:36
ultima_carga:             2026-08-16 17:04:36
dias_de_carga_distintos:  1
mediana:                  1 971 horas  (82 días)
p95:                      4 113 horas  (171 días)
```

**Las 4 252 filas tienen exactamente el mismo `cargado_en`.** Lo que la resta mide no es la latencia
de ingesta: es **la antigüedad de cada accidente respecto del día en que se hizo la carga completa**.

Y no se arregla esperando a que haya varias cargas. **La regla de idempotencia del modelo lo impide
por diseño:**

> *«Idempotencia: `ALTER TABLE … DROP PARTITION` del período, luego insertar.»*

Cada recarga **reescribe `cargado_en` de la partición entera**. La columna no puede medir cuándo
estuvo disponible un caso por primera vez, porque su valor se destruye en cada recarga — que es
justamente lo que hace la recarga fiable.

**Decisión:** E4-14 pasa a **no construible**, dentro de US3.

**Prerrequisito:** una marca de **primera aparición** por fila, que sobreviva a la recarga
idempotente. No es una columna más: es una excepción deliberada a la regla de idempotencia, y por eso
excede a este módulo.

**Alternativa descartada:** medir contra `max(cargado_en)` de la partición. Da lo mismo con más pasos:
sigue siendo la antigüedad del accidente, no la latencia de su ingesta.

---

## D6 — El umbral de masa crítica de E4-15

No hay valor de referencia en el marco, y la spec pedía decidirlo aquí.

**Decisión:** **parámetro configurable**, sin valor por defecto en la spec, con `500` como referencia
inicial y declarado en la respuesta.

**Por qué configurable y no fijo.** El número de casos que necesita un modelo depende del modelo, y
aquí no hay modelo todavía —E4-07 a E4-10 están bloqueados—. Fijar un umbral hoy sería inventar el
criterio de un entrenamiento que nadie ha diseñado.

**Por qué 500 como referencia.** Es el mismo orden que el módulo táctico usa como `muestra_minima`
alta en sus comprobaciones. Con los datos de hoy, los dos condados —2 158 y 2 094 casos— quedan **por
encima**, así que el informe no marcará nada; y esa es la respuesta correcta.

**El umbral se publica en la respuesta**, siempre. Un «esta zona no tiene masa crítica» sin decir
contra qué umbral no es accionable.

---

## D7 — Consultas propias con prueba de contraste, y el armazón de OE6

Igual que OE3. Cuatro informes de OE4 tienen equivalente táctico:

| Informe | Consulta táctica | ¿Publicada? |
|---|---|:--:|
| **E4-02** Completitud | `ot21_completitud_campos_criticos` | **Sí** *(migrada, corrige el defecto)* |
| **E4-05** Concentración | `ot21_ranking_ubicaciones` · `ot21_distribucion_zona` | Solo la segunda |
| **E4-12** Impacto humano | `ot21_impacto_humano` | No |
| **E4-01** Índice de calidad | — *(tabla legada)* | Endpoint legado |

**Decisión:** consultas propias en `dags/lib/consultas/estrategicos/oe4/`, con prueba de contraste.
Y se reutiliza el armazón de OE6 —`periodo_estrategico`, `objetivo`, `envelope`, repositorio— sin
duplicarlo.

**Y no se crea app nueva:** OE4 se añade a `informes_estrategicos`, como OE3.

---

## D8 — El acceso: dos autoridades sobre el mismo módulo

`acceso-estrategico.md` §4.4 asigna `DirectorDatos` a los quince, y `DirectorOperaciones` a los que
miden el expediente de accidente —E4-01 a E4-04, E4-12, E4-13—, porque el expediente es de su
departamento y su calidad se mide contra su operación.

**Decisión:** conjuntos **por informe**, reutilizando el mecanismo que OE3 introdujo. Aquí el reparto
es más simple —dos grupos, no tres— pero la prueba sigue siendo de **exclusión**: `DirectorOperaciones`
**no** accede a E4-05, E4-06, E4-14 ni E4-15, que son de analítica pura.

---

## D9 — El reparto de informes cambia respecto de la spec

Consecuencia de D3, D4 y D5:

| Historia | Spec original | Tras la investigación |
|---|---|---|
| **US1** Calidad del histórico | E4-01…E4-04 *(4 ✅)* | Igual *(4 ✅)* |
| **US2** Inteligencia vendible | E4-05, E4-06 ⚠️, E4-12, E4-13 ⚠️ *(4)* | **E4-05, E4-06, E4-12, E4-13 — los cuatro completos** *(4 ✅)* |
| **US3** Aptitud del histórico | E4-14, E4-15 *(2 ✅)* | **E4-15 ✅ · E4-14 ⛔** |
| **US4** Modelo predictivo ⛔ | 5 ⛔ | Igual *(5 ⛔)* |

**Construibles: 9, no 10.** Pero los dos informes de US2 que iban a entregar la mitad ahora entregan
el producto entero — y son precisamente **los dos que se venden**.

**Ampliaciones del modelo: dos**, ambas del §4.bis y ambas métricas o columnas de un hecho existente.
Ninguna tabla nueva.

---

## Resumen de incógnitas resueltas

| Incógnita | Estado |
|---|:--:|
| ¿Cuál es la fórmula del índice legado? | ✅ Descifrada y verificada en 6 filas (D1) |
| ¿Está mal el legado en la cobertura de evidencia? | ✅ Resuelta: **nadie puede saberlo**. Tres definiciones probadas, ninguna encaja (D2) |
| ¿Existe la distancia afectada? | ✅ Sí — 4 200 de 4 252. E4-13 se completa (D3) |
| ¿Existe la condición climática? | ✅ Sí, pero en **3 casos**. Se carga y se declara la escasez (D4) |
| ¿Es medible la latencia de ingesta? | ✅ Resuelta: **no**, y la idempotencia lo impide por diseño (D5) |
| ¿Cuál es el umbral de masa crítica? | ✅ Configurable, referencia 500, publicado en la respuesta (D6) |

**Ninguna `NEEDS CLARIFICATION` queda abierta.**
