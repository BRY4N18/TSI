-- E5-15 Antigüedad de activas. Cerradas aparte.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    countIf(c.fecha_baja IS NULL) AS activas,
    countIf(c.fecha_baja IS NOT NULL) AS cerradas,
    round(
        avgIf(
            dateDiff('day', toDate(c.fecha_alta), {hasta:Date}),
            c.fecha_baja IS NULL AND c.fecha_alta IS NOT NULL
        ),
        1
    ) AS dias_antiguedad_media
FROM dim_cliente AS c FINAL
WHERE {desde:Date} <= {hasta:Date}
  AND c.idcliente != -1
GROUP BY periodo
ORDER BY periodo
