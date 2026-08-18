-- E4-05 concentración. Ubicación por nombre, nunca por coordenadas.
-- «Desconocido» entra para que la suma iguale el total del período.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    multiIf(
        {nivel:String} = 'ciudad', coalesce(nullIf(ciudad, ''), 'Desconocido'),
        {nivel:String} = 'calle', concat(coalesce(ciudad, ''), ' / ', toString(idcalle)),
        coalesce(nullIf(condado, ''), 'Desconocido')
    ) AS zona,
    count() AS casos,
    round(count() / nullIf(sum(count()) OVER (PARTITION BY periodo), 0), 4) AS pct
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, zona
ORDER BY periodo, casos DESC
LIMIT {top:UInt32} BY periodo
