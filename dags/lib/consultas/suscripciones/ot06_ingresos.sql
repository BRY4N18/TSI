-- Informe #2 — Ingresos · OT06
--
-- ⚠️ Se suma `monto_con_signo`. Las notas de crédito restan solas.
-- ⚠️ `En disputa` no es impago: aquí se factura, no se cobra.
-- ⚠️ FINAL prohibido: este hecho es de transacción.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m') AS mes,
    ifNull(plan, '(sin plan)')                     AS plan,
    ifNull(tipo_cliente, '(sin tipo)')             AS tipo_cliente,
    round(sumIf(monto_total, es_nota_credito = 0), 2) AS facturado,
    round(sumIf(monto_total, es_nota_credito = 1), 2) AS notas_credito,
    round(sum(monto_con_signo), 2)                 AS ingreso_neto,
    'USD'                                          AS moneda,
    'del período'                                  AS periodicidad
FROM hecho_factura
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND estado_pago != 'Anulada'
GROUP BY mes, plan, tipo_cliente
ORDER BY mes, ingreso_neto DESC, plan
