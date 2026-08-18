-- E1-01 MRR al cierre. Suma precio_mensualizado; no divide precio.
-- Vigente al cierre: alta ≤ hasta, no cancelada ni vencida en esa fecha.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    round(sum(s.precio_mensualizado), 2) AS mrr,
    count() AS recuento,
    countIf(s.precio_mensualizado IS NULL) AS sin_periodicidad
FROM hecho_suscripcion AS s FINAL
WHERE toDate(s.fecha_alta) <= {hasta:Date}
  AND (s.fecha_cancelacion IS NULL OR toDate(s.fecha_cancelacion) > {hasta:Date})
  AND (s.fecha_fin_prevista IS NULL OR toDate(s.fecha_fin_prevista) >= {hasta:Date})
  AND s.precio_mensualizado IS NOT NULL
ORDER BY periodo
