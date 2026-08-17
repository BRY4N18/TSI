# Data Model — OE3, Escalabilidad Multi-Región sin Degradación

**Fecha:** 2026-08-16 · **Research:** [`research.md`](research.md)

Este módulo consume el [modelo analítico](../../../002-tactico/modelo-analitico/) y le añade
**una dimensión**, que es lo que desbloquea E3-08.

---

## 1. Lo que se consume

| Tabla | Tipo | ¿`FINAL`? | Qué aporta |
|---|---|:--:|---|
| `hecho_accidente` | Instantánea acumulada | **Sí** | Hitos del caso, completitud, demanda por condado |
| `hecho_despacho` | Instantánea acumulada | **Sí** | Grano de intento: primer intento, origen, tiempos |
| `hecho_estado_unidad` | Transacción | **No — falla** | Capacidad vigente y disponibilidad |
| `hecho_ping_unidad` | Transacción | **No — falla** | Huecos de señal GPS |
| `dim_unidad` | Dimensión **versionada** | **Sí** | La flota **de cada período**, no la de hoy |
| `dim_geografia` | Dimensión | **Sí** | Condado |

**No se lee `dim_region`.** Ver `research.md` D4 y `decisiones-pendientes.md` #38.

---

## 2. La única ampliación: `dim_condado_vecino`

Sigue el §4.bis del contrato de esquema. **Es aditiva**: dimensión nueva, ningún hecho se recarga.

```sql
CREATE TABLE IF NOT EXISTS dim_condado_vecino (
    idcondado        Int32,
    condado          String,
    idcondadovecino  Int32,
    condado_vecino   String,
    version          DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idcondado, idcondadovecino)
```

**Origen:** `Dim_CondadoVecino` del sistema operativo, filtrando `activo = true`, con los nombres
resueltos contra `Dim_Condado`. Medido: **2 filas, simétricas** (1↔2).

**Por qué una dimensión y no una métrica del hecho.** La vecindad es una propiedad **del territorio**,
no de un accidente ni de un despacho. Guardarla en un hecho la repetiría por cada fila y obligaría a
recargarlo cada vez que cambie el mapa.

**Por qué `ReplacingMergeTree` sin versionar.** La adyacencia física entre dos condados no cambia; si
cambiara, sería otro mapa. Versionarla abriría versiones cada vez que alguien corrigiera una etiqueta.
Es el mismo criterio que `dim_region` aplica a su geografía.

⚠️ **Necesita su fila «desconocida»** en `dags/lib/dimensiones/desconocido.py`, o los condados que no
resuelvan vecino desaparecerán en la primera unión.

---

## 3. Los siete informes construibles

**Leyenda:** ✅ el modelo lo sostiene · 🆕 necesita la dimensión nueva.

### US1 — el rendimiento del despacho *(4 informes)*

| # | Informe | Grano de salida | Fuente | Medidas | Meta |
|---|---|---|---|---|---|
| **E3-02** | Latencia operativa de asignación | período *(× condado)* | `hecho_accidente` | mediana, p95, casos, sobre umbral | **`<2 min p95`** ✅ |
| **E3-03** | Evolución de la latencia p95 | período | `hecho_accidente` | serie de p95, variación | — |
| **E3-10** | Tasa de error de registro | período *(× condado)* | `hecho_accidente` | casos, incompletos, tasa, **campos comprobados** | **`<1 %`** ✅ |
| **E3-11** | Despachos al primer intento | período *(× condado)* | `hecho_despacho` | primeros intentos, confirmados, % | `≥90 %` ⚪ |

**E3-02 mide `hora_primera_asignacion − fechahora_accidente`**, una resta dentro de la misma fila.
⚠️ **No mide `segundos_respuesta` del despacho** (oferta → confirmación, p95 28 s): la meta de
RNF-DES-001 habla del proceso completo desde el registro. Ver `research.md` D1.

**E3-10 es el complemento de la completitud**: `1 − pct_completitud`. Y **publica la lista de campos
que comprueba** — hoy severidad y calle—, porque un 0 % permanente sin esa lista se lee como «el
registro es perfecto» cuando dice «los dos campos que miro están completos».

**E3-11 exige grano de intento**: `numero_intento = 1 AND resultado = 'confirmado'`. Con grano de
caso los intentos fallidos desaparecen y el indicador sube solo.

### US2 — la tensión de la capacidad *(3 informes)*

| # | Informe | Grano de salida | Fuente | Medidas | |
|---|---|---|---|---|:--:|
| **E3-07** | Ratio demanda / capacidad | período × condado | `hecho_accidente` + `dim_unidad` | casos, unidades vigentes, ratio | ✅ |
| **E3-08** | Cobertura de respaldo por condado | condado | `dim_condado_vecino` + `hecho_estado_unidad` + `dim_unidad` | vecinos, vecinos con unidad disponible | 🆕 |
| **E3-13** | Pérdida de señal GPS | período × unidad | `hecho_ping_unidad` | huecos, duración, unidades afectadas | ✅ |

⚠️ **La capacidad de E3-07 son las versiones de unidad vigentes en el período**, no la flota actual.
Usar `es_vigente = 1` calcularía un ratio de hace tres meses contra unidades que quizá no existían —
el defecto que la dimensión versionada existe para corregir.

**Un condado con demanda y ninguna unidad vigente se declara «sin capacidad»**, no con ratio infinito.
Es el hallazgo operativo más valioso del informe: una zona donde una emergencia no tiene quién la
atienda.

**E3-08 combina las dos disponibilidades:** que el vecino exista (`dim_condado_vecino`) y que tenga al
menos una unidad **disponible** —último estado de `hecho_estado_unidad`, no la mera existencia de la
unidad—. Es la distinción que Red Operativa documentó: *existir no es estar disponible*.

---

## 4. Los siete bloqueados, y qué los desbloquea

**Ninguno se publica** (`FR-OE3-017`).

### US3 — maduración regional *(3)*

| # | Informe | Prerrequisito |
|---|---|---|
| **E3-04** | Tiempo de puesta en operación *(≤30 días `[NORMATIVO]`)* | Fecha real de entrada en producción por región |
| **E3-05** | Curva de maduración 30/60/90 días | Ídem + eje de región (#38) |
| **E3-06** | Rendimiento por cohorte de antigüedad | Ídem |

**Los tres los desbloquea el mismo cambio**: historizar el estado de región en el sistema operativo,
que hoy se sobrescribe. La misma tabla puente de #38 resolvería además el eje.

### US4 — lo que el sistema no registra ni produce *(4)*

| # | Informe | Prerrequisito | Tipo de bloqueo |
|---|---|---|---|
| **E3-12** | Tiempo de reasignación manual *(≤30 s `[NORMATIVO]`)* | Que la aplicación registre «asignación automática sin candidatas» con su instante | Suceso no instrumentado |
| **E3-01** | Uptime por región *(≥99,99 % `[NORMATIVO]`)* | Integrar el monitoreo de infraestructura | Fuente externa |
| **E3-09** | Margen operativo *(≥30 %)* | Fuente de costos por región | Fuente externa |
| **E3-14** | Cobertura de pruebas | Herramienta de cobertura | **No es informe de negocio** |

⚠️ **E3-12 cambió de bando durante la investigación.** La spec lo daba por construible; medido, **1 082
de 1 083 despachos manuales no siguen a ningún intento automático**, así que el suceso que mide —una
falla del algoritmo seguida de intervención— prácticamente no ocurre en los datos, y en ningún caso
se registra como evento. Ver `research.md` D2.

---

## 5. Entidad de salida

La misma forma que OE6, heredada del envelope común:

| Campo | Qué es | ¿Siempre? |
|---|---|:--:|
| **Claves de agrupación** | `periodo` + una de: `condado` · `unidad` | Sí |
| **Medidas** | Mediana, p95, recuentos, ratios o porcentajes | Sí |
| **Denominador** | El total sobre el que se calculó cada porcentaje | Cuando hay % |
| **Excluidos** | Filas fuera por hito ausente | Cuando puede haberlas |

Y en `meta`: `periodo`, `comparacion`, `objetivo`, `cobertura`, y `alcance` donde haga falta.

### Lo que distingue a OE3 del resto de la capa

**`objetivo.cumple` es booleano en E3-02 y E3-10.** Son las dos únicas metas `[NORMATIVO]` medibles
de toda la capa estratégica hasta hoy.

| Informe | Meta | Tipo | `cumple` |
|---|---|---|:--:|
| **E3-02** | `<2 min p95` | `NORMATIVO` | **booleano** |
| **E3-10** | `<1 %` | `NORMATIVO` | **booleano** |
| **E3-11** | `≥90 %` | `CALIBRAR` | `null` |
| E3-03, E3-07, E3-08, E3-13 | — | — | sin objetivo |

⚠️ **La prueba transversal de OE6 —«ningún `cumple` booleano»— no aplica aquí.** Copiarla haría fallar
exactamente los dos informes que este módulo aporta de nuevo a la capa.

---

## 6. Reglas de consulta heredadas

| Regla | Qué obliga aquí |
|---|---|
| **1 — ninguna tabla propia** | Se cumple: la única ampliación es una **dimensión compartida**, no una tabla de informe |
| **2 — versión final** | Obligatoria en `hecho_accidente`, `hecho_despacho`, `dim_unidad`, `dim_geografia`, `dim_condado_vecino`. **Prohibida** en `hecho_estado_unidad` y `hecho_ping_unidad` |
| **3 — intentos ≠ casos** | E3-11 cuenta intentos; E3-02, E3-03, E3-07 y E3-10 cuentan casos |
| **4 — ausencia ≠ cero** | Un caso sin asignación no entra en E3-02 con tiempo cero |
| **5 — historia o presente** | ⚠️ **Aquí sí aplica, y es crítica**: E3-07 usa la lectura **histórica** de `dim_unidad`. La actual reescribiría el pasado |
| **6 — desde cuándo es fiable** | E3-07 agrupa por versión de unidad, cuyo `inicio_es_real = 0`: **debe declarar desde cuándo su atribución es exacta** |
| **7 — filtrar por partición** | Toda consulta filtra `fecha`. E3-03 usa ventanas amplias, así que aquí pesa más |
| **8 — sin dato sensible** | Se cumple por construcción |

---

## 7. Lo que este módulo NO cambia

| Se pidió | No se añade | Motivo |
|---|---|---|
| Eje de región | Nada | Falta la relación región↔condado en el operativo (#38) |
| Historial de estado de región | Nada | El operativo sobrescribe el estado. Desbloquea US3 entera |
| Evento «algoritmo sin candidatas» | Nada | Instrumentación de la aplicación, no del analítico |
| Uptime, costos, cobertura de pruebas | Nada | Fuentes externas al sistema |
