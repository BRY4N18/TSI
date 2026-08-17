-- Informe E6-02 — Tiempo de respuesta por severidad
-- Parte de ot22_tiempo_respuesta_por_severidad, pero mide el intervalo del KPI:
-- `hora_primera_llegada − fechahora_accidente` sobre el CASO, no despacho→llegada
-- sobre el intento. El catálogo pedía el JOIN con despacho; el modelo ya tiene
-- el hito en el hecho. Ordenado por `dim_severidad.orden`, no alfabéticamente.
--
-- Los casos sin severidad resuelta aparecen como 'Desconocido' y no se descartan:
-- filtrarlos dejaría fuera precisamente los peor registrados.
--
-- Mismos tres filtros que E6-01 (con llegada, no descartado, no duplicado).

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(a.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(a.fecha),
            toStartOfYear(a.fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    coalesce(a.severidad, 'Desconocido')                        AS severidad,
    coalesce(s.orden, 99)                                       AS orden,
    count()                                                     AS casos,
    round(
        median(dateDiff('second', a.fechahora_accidente, a.hora_primera_llegada) / 60),
        1
    )                                                           AS mediana_min,
    if(
        count() >= {muestra_minima:UInt32},
        round(
            quantile(0.95)(dateDiff('second', a.fechahora_accidente, a.hora_primera_llegada) / 60),
            1
        ),
        NULL
    )                                                           AS p95_min
FROM hecho_accidente AS a FINAL
LEFT JOIN dim_severidad AS s FINAL ON s.severidad = a.severidad
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND a.hora_primera_llegada IS NOT NULL
  AND a.fue_descartado = 0
  AND a.es_duplicado = 0
GROUP BY periodo, severidad, orden
ORDER BY periodo, orden, severidad
