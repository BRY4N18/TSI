-- Informe E6-04 — Origen de asignación (automática, manual, escalado a zona)
-- Parte de ot22_asignacion_automatica_vs_manual. Añade granularidad, condado y
-- la mediana de respuesta.
--
-- ⚠️ Escalado_zona ES UN ORIGEN PROPIO
-- No se suma a «manual»: es el sistema pidiendo ayuda fuera de la zona, que no
-- es lo mismo que una decisión humana ni que una asignación automática que
-- funcionó. Sumarlo ocultaría cuándo el sistema se queda sin cobertura local.
-- Los porcentajes de los tres suman 100 %.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    if({por_condado:UInt8} = 1, coalesce(condado, 'Desconocido'), '') AS condado,
    origen_despacho                                             AS origen,
    count()                                                     AS despachos,
    round(count() / sum(count()) OVER (PARTITION BY periodo, condado), 4) AS pct,
    round(
        medianIf(
            dateDiff('second', fechahora_despacho, hora_llegada) / 60,
            hora_llegada IS NOT NULL
        ),
        1
    )                                                           AS mediana_min
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, condado, origen
ORDER BY periodo, condado, despachos DESC, origen
