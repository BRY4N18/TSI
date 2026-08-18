-- E4-12 impacto humano. Cero heridos ≠ no registrado: casos_con_dato es el denominador.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    coalesce(condado, 'Desconocido') AS condado,
    coalesce(severidad, 'Desconocido') AS severidad,
    count() AS casos,
    countIf(num_heridos IS NOT NULL) AS casos_con_dato,
    sumIf(num_heridos, num_heridos IS NOT NULL) AS heridos,
    sumIf(num_fallecidos, num_fallecidos IS NOT NULL) AS fallecidos,
    sumIf(num_victimas, num_victimas IS NOT NULL) AS victimas
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, condado, severidad
ORDER BY periodo, condado, severidad
