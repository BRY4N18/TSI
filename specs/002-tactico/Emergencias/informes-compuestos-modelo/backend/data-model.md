# Data Model — Informes Compuestos de Emergencias

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo **no define un modelo de datos propio**: consume el
[modelo analítico](../../../modelo-analitico/) y le añade lo que le falta.

Aquí están (1) los 26 informes con su grano y su fuente exacta, y (2) las siete ampliaciones que
siete de ellos exigen.

---

## 1. Los 26 informes

**Leyenda de cobertura:** ✅ el modelo lo sostiene hoy · 🟡 exige una métrica nueva · 🆕 exige un
hecho nuevo.

> ⚠️ **16 de estos 26 ya tienen endpoint construido** contra Pinot o contra el almacén. La columna
> *Endpoint hoy* lo marca. Ver la corrección de alcance en [`plan.md`](plan.md): solo se migran los
> **3 defectuosos**; los 13 correctos conviven vigilados por una prueba de contraste.

| Marca | Significa |
|---|---|
| 🔵 | Ya existe endpoint y **es correcto** — no se migra ahora |
| 🔴 | Ya existe endpoint y **da cifras equivocadas** — se migra |
| ⚪ | No existe: se construye |

### OT21 — Registrar el incidente con calidad *(6 informes, 6 ✅)*

| # | Informe | Grano de salida | Hecho | Cobertura | Endpoint hoy |
|--:|---|---|---|:--:|:--:|
| 1 | Distribución por severidad | severidad × período | `hecho_accidente` | ✅ | 🔵 |
| 2 | Distribución por zona | condado × período | `hecho_accidente` | ✅ | 🔵 |
| 3 | Completitud de campos críticos | período | `hecho_accidente` | ✅ | 🔴 |
| 4 | Descarte y fusión de reportes | período | `hecho_accidente` | ✅ | 🔵 |
| 5 | Ranking de ubicaciones con más casos | calle o condado | `hecho_accidente` × `dim_geografia` | ✅ | 🔵 |
| 6 | Impacto humano por ubicación | condado × período | `hecho_accidente` | ✅ | 🔵 |

**#3 es el que corrige el defecto del catálogo.** Se mide como
`idseveridad IS NOT NULL AND idcalle IS NOT NULL` **sobre el modelo**, donde la ausencia es ausencia
real. La misma expresión sobre el sistema operativo es siempre cierta, porque allí no hay nulos sino
centinelas.

**#4 usa `fue_descartado` y `es_duplicado`**, que el modelo deriva de los estados reales. El sistema
operativo marca `activo = false` para descartado, fusionado **y** cerrado, así que su columna no
sirve para distinguirlos.

### OT22 — Asignar y despachar *(7 informes, 7 ✅)*

| # | Informe | Grano de salida | Hecho | Cobertura | Endpoint hoy |
|--:|---|---|---|:--:|:--:|
| 7 | Asignación automática vs manual | origen × período | `hecho_despacho` | ✅ | 🔵 |
| 8 | Tiempo de reportado a confirmado | período | `hecho_accidente` | ✅ | 🔵 |
| 9 | Tiempo de respuesta por severidad | severidad × período | `hecho_despacho` | ✅ | 🔵 |
| 10 | Rechazo y timeout por unidad | unidad × período | `hecho_despacho` | ✅ | 🔵 |
| 11 | Carga por unidad | unidad × período | `hecho_despacho` | ✅ | 🔵 |
| 12 | Ratio demanda / capacidad por condado | condado × período | `hecho_accidente` + `dim_unidad` | ✅ | 🔴 |
| 13 | Despachos resueltos al primer intento | período | `hecho_despacho` | ✅ | ⚪ |

**#12 corrige un defecto documentado gracias a la dimensión versionada.** La capacidad de un período
son las **versiones de unidad vigentes entonces** en ese condado, no las unidades activas hoy. El
informe actual usa la flota actual: un ratio de hace tres meses se calcula contra unidades que quizá
no existían.

**#13 solo es calculable con grano de intento**: `numero_intento = 1 AND resultado = 'confirmado'`.
Con grano de caso, los intentos fallidos desaparecen.

### OT23 — Acompañar la misión *(3 informes, 3 ✅)*

| # | Informe | Grano de salida | Hecho | Cobertura | Endpoint hoy |
|--:|---|---|---|:--:|:--:|
| 14 | Pérdida de señal | hueco detectado | `hecho_ping_unidad` | ✅ | 🔴 |
| 15 | Abortos y pérdidas de misión | período × proveedor | `hecho_despacho` | ✅ | 🔵 |
| 16 | Desviación de llegada frente a la referencia | unidad × período | `hecho_despacho` | ✅ | ⚪ |

**#14** filtra por `segundos_desde_anterior > umbral`. El hueco ya está medido en la carga: detectarlo
es un filtro por columna, no una función de ventana sobre 59 045 filas.

**#16** es el de la referencia derivada (research D5). Su cálculo tiene dos partes:

```
referencia(condado, severidad, fecha) =
    mediana de (hora_llegada − fechahora_despacho)
    sobre los despachos del MISMO condado y severidad,
    con llegada registrada,
    en la ventana [fecha − 90 días, fecha)          ← anterior al despacho medido

desviacion = (hora_llegada − fechahora_despacho) − referencia
```

⚠️ **Si la ventana tiene menos de `MUESTRA_MINIMA` despachos con llegada, no hay referencia** y la
desviación es **ausente**, no cero.

### OT24 — Documentar con evidencia *(5 informes, 0 ✅)*

| # | Informe | Grano de salida | Hecho | Cobertura | Endpoint hoy |
|--:|---|---|---|:--:|:--:|
| 17 | Cobertura de evidencia por severidad y región | severidad × condado | `hecho_accidente` | 🟡 `num_notas` | ⚪ |
| 18 | Latencia de sincronización offline | período | `hecho_evidencia` | 🆕 | ⚪ |
| 19 | Completitud del enriquecimiento | período | `hecho_accidente` | 🟡 3 métricas | ⚪ |
| 20 | Volumen de evidencia **por unidad** | unidad × período | `hecho_evidencia` | 🆕 | ⚪ |
| 21 | Escaladas de severidad originadas en sitio | período | `hecho_accidente` | 🟡 2 métricas | ⚪ |

**#20 entrega menos de lo que pide el catálogo**, y es deliberado: sin desglose por técnico de campo
(research D6).

### OT25 — Cerrar el caso *(5 informes, 3 ✅)*

| # | Informe | Grano de salida | Hecho | Cobertura | Endpoint hoy |
|--:|---|---|---|:--:|:--:|
| 22 | Tiempo de asignado a cerrado | período | `hecho_accidente` | ✅ | 🔵 |
| 23 | Cierres forzados | período × proveedor | `hecho_despacho` | ✅ | 🔵 |
| 24 | Distribución de resultados y calificación media | severidad × condado | `hecho_accidente` | 🟡 2 métricas | ⚪ |
| 25 | Envejecimiento de la cartera de casos abiertos | tramo de antigüedad | `hecho_accidente` | ✅ | ⚪ |
| 26 | Retiros forzados frente a finalizaciones normales | proveedor × período | `hecho_despacho` | ✅ | ⚪ |

**#25 depende de que un caso abierto no tenga fecha de cierre.** El modelo lo garantiza: un hito no
alcanzado va ausente. Si llevara la fecha de carga, **todos los casos abiertos aparecerían cerrados**
y la cartera saldría vacía.

---

## 2. Las siete ampliaciones del modelo

Todas siguen el §4.bis del contrato de esquema. **Ninguna crea una tabla por informe.**

### 2.1 Métricas nuevas en `hecho_accidente`

```sql
ALTER TABLE hecho_accidente ADD COLUMN num_notas               Nullable(Int32);
ALTER TABLE hecho_accidente ADD COLUMN num_conductores         Nullable(Int32);
ALTER TABLE hecho_accidente ADD COLUMN num_implicados          Nullable(Int32);
ALTER TABLE hecho_accidente ADD COLUMN num_elementos_clima     Nullable(Int32);
ALTER TABLE hecho_accidente ADD COLUMN num_escaladas_severidad Nullable(Int32);
ALTER TABLE hecho_accidente ADD COLUMN severidad_inicial       Nullable(String);
ALTER TABLE hecho_accidente ADD COLUMN resultado_atencion      Nullable(String);
ALTER TABLE hecho_accidente ADD COLUMN calificacion            Nullable(Int32);
```

⚠️ **Todas `Nullable`, y la distinción importa en dos sentidos opuestos:**

- Los **recuentos** (`num_*`) van a **`0` cuando el caso existe y no tiene ninguno**: cero notas es
  una medición. Van **ausentes** sólo en las filas cargadas antes de que la métrica existiera.
- `severidad_inicial`, `resultado_atencion` y `calificacion` van **ausentes cuando no se registraron**.
  Una calificación de `0` sería la peor nota posible, no «sin calificar».

**`observaciones_finales` no se copia**: es texto libre y puede contener material interno.

### 2.2 `hecho_evidencia` — hecho de transacción, grano una evidencia

```sql
CREATE TABLE IF NOT EXISTS hecho_evidencia (
    idevidencia          Int32,
    tipo                 String,            -- foto | nota
    fecha                Date,              -- de la captura; clave de partición
    fechahora_captura    DateTime,
    fechahora_sincronia  Nullable(DateTime),   -- NULL = aún sin sincronizar

    idaccidente          String,
    sk_unidad            UInt64,            -- versión de unidad vigente al capturar
    idunidademergencia   Int32,
    proveedor            String,
    idseveridad          Nullable(Int32),
    severidad            Nullable(String),
    condado              Nullable(String),

    segundos_hasta_sincronia Nullable(Int32),
    categoria_nota       Nullable(String),  -- el tipo de nota; NULL en las fotos

    cargado_en           DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idunidademergencia, idevidencia)
```

**Por qué un hecho y no métricas del caso:** tiene **dos instantes propios** —capturada y
sincronizada— y su grano no es el caso: un caso puede tener varias evidencias con latencias muy
distintas. Contarlas en el caso respondería «cuántas hubo» pero nunca «cuánto tardaron».

**Fotos y notas en la misma tabla** porque comparten grano, dimensiones y preguntas. Separarlas
obligaría a unir dos hechos para responder «cobertura de foto **y** nota», que es justamente el
informe #17.

⚠️ **`idusuario` no se copia**, aunque ambas fuentes lo traen. Es la decisión de research D6.

⚠️ **`fechahora_sincronia` ausente significa «aún no sincronizada»**, no «sincronizada en la época
cero». La latencia de esas evidencias es ausente, no infinita ni cero.

### 2.3 Lo que NO se añade, y por qué

| Se pidió | No se añade | Motivo |
|---|---|---|
| Un hecho de cambios de severidad | Se resuelve como métrica del caso | Su fuente tiene **1 fila** para 4 252 casos. Un hecho, un flujo y un DAG para eso es coste sin retorno |
| Desglose por técnico de campo | Nada | Identidad de persona; exclusión sin excepciones |
| Coordenadas para estimar llegada | Nada | Excluidas por diseño; la referencia se deriva del histórico |
| `observaciones_finales` | Nada | Texto libre |

---

## 3. Entidades de salida de un informe

Todo informe devuelve **filas agregadas** con esta forma común:

| Campo | Qué es |
|---|---|
| **Clave de agrupación** | Una o dos: período, severidad, condado, unidad, proveedor, origen o tramo |
| **Medidas** | Recuentos, porcentajes, medianas o promedios, según el informe |
| **Denominador** | Presente cuando hay porcentaje, para que se pueda comprobar la fracción |
| **Cobertura del dato** | Cuántas filas del período aportaron la medida, cuando puede haber ausencias |

**El denominador no es decorativo.** Un `12,5 %` sobre 8 casos y sobre 8 000 casos son afirmaciones
muy distintas, y un tablero que sólo muestre el porcentaje las presenta igual.

---

## 4. Reglas de consulta que este módulo hereda

Del [contrato de consumo](../../../modelo-analitico/contracts/contrato-consumo.md), con las dos que
más importan aquí:

| Regla | Qué obliga |
|---|---|
| **Versión final** | Obligatoria en `hecho_accidente`, `hecho_despacho` y las 5 dimensiones. **Prohibida** en `hecho_estado_unidad`, `hecho_ping_unidad` y `hecho_evidencia` |
| **Contar filas no es contar casos** | El grano de despacho es el intento: 4 314 intentos son 3 651 casos |
| **Ausencia ≠ cero** | En denominadores, medianas y promedios |
| **Desconocido cuenta** | Las filas cuya dimensión no se resolvió entran en los totales, etiquetadas |
