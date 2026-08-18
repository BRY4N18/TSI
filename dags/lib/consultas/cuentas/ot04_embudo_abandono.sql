-- Embudo de abandono · OT04
--
-- ⚠️ Parte de dim_etapa_onboarding (catálogo explícito), no de lo observado.
-- Una etapa sin ningún cliente aparece con cero.

WITH
    llegadas AS (
        SELECT
            idetapa,
            countDistinct(idcliente) AS clientes_que_llegaron
        FROM hecho_onboarding
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idetapa
    ),
    ordenadas AS (
        SELECT
            e.orden,
            e.etapa,
            e.idetapa,
            ifNull(l.clientes_que_llegaron, 0) AS clientes_que_llegaron,
            lagInFrame(ifNull(l.clientes_que_llegaron, 0), 1, 0) OVER (
                ORDER BY e.orden
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS llegaron_anterior
        FROM dim_etapa_onboarding AS e FINAL
        LEFT JOIN llegadas AS l ON l.idetapa = e.idetapa
    )
SELECT
    orden,
    etapa,
    clientes_que_llegaron,
    if(
        orden = 1,
        if(clientes_que_llegaron = 0, NULL, 1.0),
        round(clientes_que_llegaron / nullIf(llegaron_anterior, 0), 4)
    ) AS pct_supera,
    if(
        orden = 1,
        0,
        greatest(llegaron_anterior - clientes_que_llegaron, 0)
    ) AS detenidos_aqui
FROM ordenadas
ORDER BY orden
