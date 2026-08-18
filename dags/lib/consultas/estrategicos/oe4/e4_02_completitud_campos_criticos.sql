-- E4-02 completitud de campos críticos. El porcentaje sin la lista de campos
-- se leería como «el expediente es perfecto».

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    if({por_condado:UInt8} = 1, coalesce(condado, 'Desconocido'), '') AS condado,
    count() AS casos,
    countIf(
        severidad IS NOT NULL AND tipo_reportado IS NOT NULL
        AND hora_confirmacion IS NOT NULL AND condado IS NOT NULL AND ciudad IS NOT NULL
    ) AS completos,
    round(
        countIf(
            severidad IS NOT NULL AND tipo_reportado IS NOT NULL
            AND hora_confirmacion IS NOT NULL AND condado IS NOT NULL AND ciudad IS NOT NULL
        ) / nullIf(count(), 0),
        4
    ) AS pct_completitud,
    5 AS campos_comprobados
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, condado
ORDER BY periodo, condado
