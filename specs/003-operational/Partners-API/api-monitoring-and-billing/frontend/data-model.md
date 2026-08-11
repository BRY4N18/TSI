# Data Model — Monitoreo y Facturación de API (Frontend)

> **Ninguna entidad nueva.** Esta capa no persiste nada: solo transforma respuestas del backend en
> view-models. Las entidades reales (`Fact_APIIntegracion`, `Fact_LogLlamadaAPI`, `Fact_Factura`)
> viven en [`../backend/data-model.md`](../backend/data-model.md) y **no se redefinen aquí**.

## El problema que este archivo resuelve

El backend devuelve **centinelas y `null` con significado**, y ese significado se pierde si cada
plantilla lo interpreta por su cuenta. Aquí se fija una sola traducción, en un solo sitio.

---

## 1) `ConsumoPartnerVM` — panel del partner (`GET /partners/{id}/metricas`)

| Campo del backend | Tipo | View-model | Regla |
|---|---|---|---|
| `llamadas` | INT | `llamadas` | Directo |
| `errores` | INT | `errores` | Directo |
| `latencia_media_ms` | DOUBLE | `latenciaMediaMs` | Directo |
| `cupo_mensual` | INT | `cupoMensual` | `-1` (centinela `SIN_CUPO`) → `null` |
| `porcentaje_consumido` | DOUBLE \| **null** | `porcentaje` | `null` → **«No aplica — sin cupo configurado»** |
| `llamadas_excedentes` | INT | `excedenteLlamadas` | Directo; `0` es un valor legítimo |
| `excedente_estimado` | DOUBLE \| **null** | `excedenteImporte` | `null` → **«No aplica — sin tarifa configurada»** |
| `entorno` | STRING | `entorno` | Siempre visible en texto, no solo en color |
| `datos_hasta` | LONG | `datosHasta` | Marca del último dato consultable |
| `periodo.desde/hasta` | LONG | `periodo` | Rango del período vigente |

**Regla única de centinelas (`monitoreo.types.ts`):**

```
null  →  { valor: null, leyenda: '<motivo>' }   // se renderiza «No aplica»
0     →  { valor: 0,    leyenda: '' }           // se renderiza «0»
```

> **`null` y `0` no son lo mismo y nunca deben colapsar.** `0 %` significa «no has consumido nada»;
> `null` significa «no hay cupo contra el que comparar». Un partner sin cupo que vea «0 %» concluirá
> que no está consumiendo, que es falso. El backend ya tomó esta decisión (`_porcentaje` devuelve
> `None` a propósito); esta capa la respeta en vez de rellenarla.

**Estado derivado del cupo** — el único cálculo propio de esta capa:

| Condición | `estadoCupo` | Token | Copy |
|---|---|---|---|
| `porcentaje` es `null` | `sin-cupo` | `informacion` | «Sin cupo configurado» |
| `porcentaje` < 80 | `holgado` | `informacion` | — |
| 80 ≤ `porcentaje` < 100 | `cerca` | `informacion` | «Te acercas a tu cupo mensual» |
| `porcentaje` ≥ 100 | `excedido` | **`informacion`** | «Excedente estimado: {importe}. Tu servicio no se interrumpe.» |

> **Los cuatro estados usan el MISMO token.** No es un descuido de la tabla: es el tie-breaker de
> `plan.md`. `excedido` **no** es un estado de alarma, es un estado de compra (RN-APM-002).

---

## 2) `LogLlamadaVM` — consola (`GET /logs-api`)

| Campo | View-model | Regla |
|---|---|---|
| `idlogllamadaapi` | `id` | `JetBrains Mono`, texto plano, **nunca link** |
| `endpoint`, `metodohttp` | `endpoint`, `metodo` | Directo |
| `codigohttp` | `codigo` + `clase` | Ver clasificación abajo |
| `latencia` | `latenciaMs` | Directo |
| `iporigen` | `ipOrigen` | **INT en el esquema** → se formatea a notación con puntos |
| `fechallamada` | `fechaHora` | Fecha local |

**Clasificación del código — es lo que decide el lenguaje de la fila:**

| Rango | `clase` | Cómo se presenta |
|---|---|---|
| 2xx | `exito` | Neutro |
| **429** | `ritmo` | **Caso propio**: «Límite de ritmo». No cuenta como consumo facturable |
| 4xx (resto) | `cliente` | **Autodiagnóstico del partner** (RN-APM-009): informativo, no alarma |
| 5xx | `plataforma` | Fallo nuestro: aquí sí corresponde lenguaje de incidencia |

> **El `429` se separa del resto de 4xx a propósito.** Agruparlos haría que un partner al que
> simplemente se le está limitando el ritmo creyera que sus peticiones están mal formadas.

---

## 3) `ReporteMensualVM` — reporte (`GET /reportes-consumo`)

| Campo | Regla |
|---|---|
| `llamadas`, `errores`, `latencia_media_ms` | Directo |
| `periodo` (año, mes) | Elegido por el usuario; viaja en la URL para poder compartirse |
| `entorno` | Siempre `Producción` (RN-APM-001), declarado en pantalla |

**Comparación** — se piden dos períodos y se derivan:

```
variacion = actual - comparado
variacionPct = comparado > 0 ? (variacion / comparado) * 100 : null
```

> **División por cero explícita.** Si el período comparado tuvo 0 llamadas, la variación porcentual
> es `null` («sin base de comparación»), no `Infinity` ni `100 %`.

**Mes sin consumo:** `llamadas = 0` es una **respuesta válida**, no un vacío de error
(`research.md` Decision 7).

---

## 4) `ExcepcionFacturacionVM` — cola del Administrador (`BE-DELTA-04/05`)

| Campo | Regla |
|---|---|
| `tipo` | `reintentos_agotados` \| `no_tarificable` — **discriminador obligatorio** |
| `idpartner`, `nombrePartner` | El nombre es lo que se muestra; el id viaja en el payload |
| `periodo` | Período del corte |
| `importe` | Solo en `reintentos_agotados`; en `no_tarificable` **no hay importe porque no hay factura** |
| `intentos` | Solo en `reintentos_agotados` (0–3) |
| `ultimoResultado` | Motivo del último fallo |
| `accionSugerida` | Derivado del `tipo`, no del backend |

**Acción sugerida por tipo:**

| `tipo` | Qué pasó | Acción sugerida |
|---|---|---|
| `reintentos_agotados` | La factura existe; su emisión falló 3 veces (1 h, 6 h, 24 h) | Emitirla manualmente |
| `no_tarificable` | **No hay factura**: el plan no tiene `precio_excedente_llamada` | Configurar la tarifa del plan (CU-O26) y reejecutar el corte |

> **En `no_tarificable` la columna de importe va vacía, no en cero.** Un `0,00` sugeriría que se
> facturó nada; la verdad es que no se pudo calcular cuánto.

---

## Estados de la interfaz (los tres no felices)

Los cuatro listados usan los componentes compartidos `app-list-loading-skeleton`,
`app-list-error-state` y `app-list-empty-state`. El copy exacto de cada uno está en
[`research.md`](./research.md) Decision 7 — **no se duplica aquí** para que no diverjan.

## Fuera de este modelo

Los cálculos de consumo, excedente y tarifa son del backend (`MetricasConsumoService`,
`TarificacionExcedenteService`). Esta capa **no recalcula nada**: si un importe se ve mal, el
defecto está en el backend y allí se corrige, no maquillándolo aquí.
