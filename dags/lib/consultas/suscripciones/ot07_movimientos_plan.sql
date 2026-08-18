-- Informe #7 — Movimientos de plan · OT07
--
-- El tipo sale del delta de precio, no del nivel.
-- Distingue aprobada de aplicada. FINAL prohibido.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m') AS mes,
    tipo_movimiento,
    count()                                        AS solicitudes,
    round(sum(delta_precio), 2)                    AS delta_ingreso_total,
    countIf(estado = 'aprobada')                   AS aprobadas,
    countIf(estado = 'aplicada')                   AS aplicadas,
    'USD'                                          AS moneda,
    'del movimiento'                               AS periodicidad
FROM hecho_solicitud_cambio_plan
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY mes, tipo_movimiento
ORDER BY mes, solicitudes DESC, tipo_movimiento
