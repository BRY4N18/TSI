-- Informe #9 — Suspensión y reactivación · OT07

SELECT
    formatDateTime(toStartOfMonth({hasta:Date}), '%Y-%m') AS mes,
    countIf(estado_derivado = 'suspendida'
        AND (fecha_suspension IS NULL
             OR toDate(fecha_suspension) BETWEEN {desde:Date} AND {hasta:Date})) AS suspendidas,
    countIf(fecha_reactivacion IS NOT NULL
        AND toDate(fecha_reactivacion) BETWEEN {desde:Date} AND {hasta:Date}) AS reactivadas,
    if(count() = 0, NULL,
        round(countIf(estado_derivado = 'suspendida') / count(), 4)) AS pct_suspension,
    if(countIf(estado_derivado = 'suspendida'
            OR fecha_reactivacion IS NOT NULL) = 0, NULL,
        round(
            countIf(fecha_reactivacion IS NOT NULL
                AND toDate(fecha_reactivacion) BETWEEN {desde:Date} AND {hasta:Date})
            / countIf(estado_derivado = 'suspendida'
                OR fecha_reactivacion IS NOT NULL),
            4
        )) AS pct_reactivacion
FROM hecho_suscripcion FINAL
WHERE {desde:Date} <= {hasta:Date}
  AND (
        (
            estado_derivado = 'suspendida'
            AND toDate(ifNull(fecha_suspension, fecha_alta)) BETWEEN {desde:Date} AND {hasta:Date}
        )
        OR (
            fecha_reactivacion IS NOT NULL
            AND toDate(fecha_reactivacion) BETWEEN {desde:Date} AND {hasta:Date}
        )
      )
GROUP BY mes
HAVING suspendidas > 0 OR reactivadas > 0
ORDER BY mes
