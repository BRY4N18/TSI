-- Métricas de consumo por partner · OT09
--
-- Equivalente del endpoint ya construido; aquí hay p95 además de media.

WITH
    llamadas AS (
        SELECT
            idpartner,
            count() AS n,
            countIf(clase_resultado != 'exito') AS errores,
            avg(latencia_ms) AS media,
            quantileExact(0.95)(latencia_ms) AS p95
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idpartner
    )
SELECT
    toStartOfMonth({desde:Date}) AS periodo,
    p.nombre_partner AS partner,
    ifNull(l.n, 0) AS llamadas,
    ifNull(l.errores, 0) AS errores,
    round(l.media, 1) AS latencia_media_ms,
    round(l.p95, 1) AS latencia_p95_ms,
    ifNull(l.n, 0) AS muestras,
    p.limite_llamadas_mes AS cupo,
    if(
        p.limite_llamadas_mes IS NULL,
        NULL,
        round(ifNull(l.n, 0) / nullIf(p.limite_llamadas_mes, 0), 4)
    ) AS pct_consumido
FROM dim_partner AS p FINAL
LEFT JOIN llamadas AS l ON l.idpartner = p.idpartner
WHERE p.idpartner != -1
  AND {desde:Date} <= {hasta:Date}
ORDER BY partner
