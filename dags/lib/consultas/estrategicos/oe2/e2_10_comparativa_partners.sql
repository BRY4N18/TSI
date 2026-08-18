-- E2-10 Comparativa. Ceros visibles. Organización, no contacto.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    p.nombre_partner AS partner,
    ifNull(l.llamadas, 0) AS llamadas,
    round(ifNull(l.errores, 0) / nullIf(l.llamadas, 0), 4) AS pct_error,
    ifNull(l.errores, 0) AS errores,
    ifNull(l.llamadas, 0) AS denominador,
    round(l.p95, 1) AS latencia_p95_ms
FROM dim_partner AS p FINAL
LEFT JOIN (
    SELECT
        idpartner,
        count() AS llamadas,
        countIf(clase_resultado != 'exito') AS errores,
        quantileExact(0.95)(latencia_ms) AS p95
    FROM hecho_llamada_api
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY idpartner
) AS l ON l.idpartner = p.idpartner
WHERE p.idpartner != -1
  AND p.estado = 'activo'
  AND {desde:Date} <= {hasta:Date}
ORDER BY periodo, partner
