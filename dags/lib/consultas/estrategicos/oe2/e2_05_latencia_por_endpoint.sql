-- E2-05 Latencia por endpoint. p95 NULL bajo muestra_minima.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    endpoint_path,
    count() AS muestras,
    round(avg(latencia_ms), 1) AS latencia_media_ms,
    if(
        count() >= {muestra_minima:UInt32},
        round(quantileExact(0.95)(latencia_ms), 1),
        NULL
    ) AS latencia_p95_ms,
    if(count() >= {muestra_minima:UInt32}, 1, 0) AS percentil_fiable
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, endpoint_path
ORDER BY periodo, endpoint_path
