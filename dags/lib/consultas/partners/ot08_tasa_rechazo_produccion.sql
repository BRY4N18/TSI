-- Tasa de rechazo de solicitudes de producción · OT08
--
-- Agrupa por motivo, nunca por persona. Solo cambios efectivos.

SELECT
    toStartOfMonth({desde:Date}) AS periodo,
    ifNull(motivo, '(sin motivo)') AS motivo,
    countIf(tipo_cambio = 'solicitud_promocion_produccion') AS solicitudes,
    countIf(tipo_cambio = 'rechazo_promocion_produccion') AS rechazadas,
    round(
        countIf(tipo_cambio = 'rechazo_promocion_produccion')
        / nullIf(countIf(tipo_cambio = 'solicitud_promocion_produccion'), 0),
        4
    ) AS pct_rechazo
FROM hecho_cambio_acceso
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND es_cambio_efectivo = 1
  AND tipo_cambio IN ('solicitud_promocion_produccion', 'rechazo_promocion_produccion')
GROUP BY periodo, motivo
ORDER BY periodo, motivo
