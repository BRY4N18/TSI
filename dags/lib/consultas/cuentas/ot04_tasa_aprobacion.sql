-- Tasa de aprobación frente a rechazo · OT04

SELECT
    toStartOfMonth(toDate(fecha_alta)) AS periodo,
    tipo AS tipo_organizacion,
    count() AS solicitudes,
    countIf(resultado_solicitud = 'aprobada') AS aprobadas,
    countIf(resultado_solicitud = 'rechazada') AS rechazadas,
    round(
        countIf(resultado_solicitud = 'aprobada')
        / nullIf(count(), 0),
        4
    ) AS pct
FROM dim_cliente FINAL
WHERE resultado_solicitud IS NOT NULL
  AND fecha_alta IS NOT NULL
  AND toDate(fecha_alta) BETWEEN {desde:Date} AND {hasta:Date}
  AND idcliente != -1
GROUP BY periodo, tipo_organizacion
ORDER BY periodo, tipo_organizacion
