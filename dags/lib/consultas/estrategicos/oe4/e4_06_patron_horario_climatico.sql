-- E4-06 patrón horario y climático. 3 casos con clima: cobertura parcial.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    franja_horaria AS franja,
    toDayOfWeek(fecha) AS dia_semana,
    coalesce(condicion_clima, 'sin_dato') AS condicion_clima,
    count() AS casos,
    countIf(condicion_clima IS NOT NULL AND condicion_clima != 'sin_dato') AS casos_con_clima,
    if(
        countIf(condicion_clima IS NOT NULL AND condicion_clima != 'sin_dato')
            < {muestra_minima:UInt32},
        'parcial',
        'completa'
    ) AS cobertura
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, franja, dia_semana, condicion_clima
ORDER BY periodo, dia_semana, franja
