-- Informe #4 — Cobro al primer intento · OT06
--
-- Distingue pagada sin reintentos de pagada tras reintentos.
-- ⚠️ `En disputa` no entra: no es un cobro.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m') AS mes,
    countIf(estado_pago = 'Pagada' AND es_nota_credito = 0) AS pagadas,
    countIf(pagada_primer_intento = 1)                      AS primer_intento,
    countIf(estado_pago = 'Pagada' AND es_nota_credito = 0
        AND pagada_primer_intento = 0)                      AS tras_reintentos,
    if(countIf(estado_pago = 'Pagada' AND es_nota_credito = 0) = 0, NULL,
        round(countIf(pagada_primer_intento = 1)
            / countIf(estado_pago = 'Pagada' AND es_nota_credito = 0), 4))
                                                            AS pct_primer_intento
FROM hecho_factura
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND estado_pago NOT IN ('En disputa', 'Anulada')
  AND es_nota_credito = 0
GROUP BY mes
ORDER BY mes
