-- Informe #10 — Tiempo de resolución de solicitudes · OT07
--
-- Las pendientes van **aparte**, nunca como cero. Una rechazada cuenta como
-- resuelta. Sin desglose por administrador.
-- ⚠️ FINAL prohibido.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m') AS mes,
    countIf(esta_resuelta = 1)                      AS resueltas,
    countIf(esta_resuelta = 0)                      AS pendientes,
    quantileExact(0.5)(segundos_resolucion)         AS segundos_mediana
FROM hecho_solicitud_cambio_plan
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY mes
ORDER BY mes
