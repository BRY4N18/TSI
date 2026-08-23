-- OT04 — Embudo de onboarding: dónde se detienen las cuentas.
--
-- ⚠️ **Llegar a una etapa y superarla no son lo mismo**, y hasta el 2026-08-23
-- esta consulta no podía distinguirlo: `hecho_onboarding` solo recibía etapas
-- **completadas**, así que toda llegada era también una superación y el embudo
-- devolvía 100 % en cada paso (decisión #45). El abandono era literalmente
-- invisible: las etapas que nadie hacía no existían como filas.
--
-- Desde que el origen declara las etapas obligatorias al aprobar la cuenta, la
-- tabla trae las dos cosas y `completada` las separa:
--
--   * **llegó**    — hay fila para ese cliente en esa etapa.
--   * **superó**   — esa fila está en `completada = 1`.
--   * **se detuvo aquí** — llegó y no superó. Eso es el abandono observado,
--     sin umbral de inactividad ni inferencia: es un hecho registrado.
--
-- `pct_supera` pasa a medirse **dentro de la etapa** —superaron / llegaron— y no
-- comparando con la etapa anterior. La cadena anterior daba un porcentaje
-- correcto solo mientras cada llegada implicara una superación; ahora que no lo
-- implica, compararse con el paso previo mezclaría dos cosas distintas.
WITH
    paso AS (
        SELECT
            idetapa,
            countDistinct(idcliente)                        AS clientes_que_llegaron,
            countDistinctIf(idcliente, completada = 1)      AS clientes_que_superaron
        FROM hecho_onboarding
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idetapa
    )
SELECT
    e.orden                                                 AS orden,
    e.etapa                                                 AS etapa,
    ifNull(p.clientes_que_llegaron, 0)                      AS clientes_que_llegaron,
    ifNull(p.clientes_que_superaron, 0)                     AS clientes_que_superaron,
    -- Ausente, no cero, cuando nadie llegó: un 0 % se leería como «todos se
    -- atascaron aquí», y lo cierto es que nadie pasó por esta etapa.
    if(
        ifNull(p.clientes_que_llegaron, 0) = 0,
        NULL,
        round(p.clientes_que_superaron / p.clientes_que_llegaron, 4)
    )                                                       AS pct_supera,
    greatest(
        ifNull(p.clientes_que_llegaron, 0) - ifNull(p.clientes_que_superaron, 0),
        0
    )                                                       AS detenidos_aqui
FROM dim_etapa_onboarding AS e FINAL
LEFT JOIN paso AS p ON p.idetapa = e.idetapa
ORDER BY orden
