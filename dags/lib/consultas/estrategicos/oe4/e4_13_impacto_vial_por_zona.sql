-- E4-13 impacto vial. Dos denominadores: duración y distancia no coinciden.
-- Las filas anteriores a la columna nueva tienen distancia NULL, no cero.

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
    count() AS casos,
    countIf(duracion_minutos IS NOT NULL) AS casos_con_duracion,
    countIf(distancia_millas IS NOT NULL) AS casos_con_distancia,
    round(avgIf(duracion_minutos, duracion_minutos IS NOT NULL), 1) AS duracion_media,
    round(avgIf(distancia_millas, distancia_millas IS NOT NULL), 2) AS distancia_media
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, condado
ORDER BY periodo, condado
