-- Informe #5 — Efectividad del dunning · OT06
--
-- Escalon en días de mora. `En disputa` no entra.
-- ⚠️ FINAL prohibido sobre factura.

SELECT
    formatDateTime(toStartOfMonth({hasta:Date}), '%Y-%m') AS mes,
    escalon,
    countIf(estado_pago = 'Pendiente' AND dias_mora >= escalon)
        + countIf(estado_pago = 'Pagada' AND reintentos >= 1) AS facturas_en_escalon,
    countIf(estado_pago = 'Pagada' AND reintentos >= 1)        AS recuperadas,
    if(
        countIf(estado_pago = 'Pendiente' AND dias_mora >= escalon)
            + countIf(estado_pago = 'Pagada' AND reintentos >= 1) = 0,
        NULL,
        round(
            countIf(estado_pago = 'Pagada' AND reintentos >= 1)
            / (
                countIf(estado_pago = 'Pendiente' AND dias_mora >= escalon)
                + countIf(estado_pago = 'Pagada' AND reintentos >= 1)
            ),
            4
        )
    ) AS pct_recuperacion
FROM hecho_factura
ARRAY JOIN arrayMap(
    x -> toInt32(trim(BOTH ' ' FROM x)),
    splitByChar(',', {escalones_dunning:String})
) AS escalon
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND estado_pago NOT IN ('En disputa', 'Anulada')
  AND es_nota_credito = 0
GROUP BY mes, escalon
HAVING facturas_en_escalon > 0
ORDER BY mes, escalon
