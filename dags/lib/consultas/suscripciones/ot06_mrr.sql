-- Informe #1 — MRR · OT06
--
-- Suma de precios **mensualizados** de las vigentes. La periodicidad ausente
-- no entra como cero: se cuenta en `sin_periodicidad`.
--
-- ⚠️ estado_derivado, nunca `activo`.
-- ⚠️ FINAL obligatorio: sin él una suscripción actualizada infla el MRR.
-- ⚠️ El mes natural es la dimensión; el rango viaja por contrato.

WITH
    toDate(concat({mes:String}, '-01')) AS inicio_mes,
    addMonths(inicio_mes, 1)            AS inicio_sig
SELECT
    {mes:String}                                                        AS mes,
    round(sumIf(precio_mensualizado, estado_derivado = 'vigente'
        AND precio_mensualizado IS NOT NULL), 2)                        AS mrr,
    round(sumIf(precio_mensualizado, estado_derivado = 'vigente'
        AND precio_mensualizado IS NOT NULL
        AND toDate(fecha_alta) >= inicio_mes
        AND toDate(fecha_alta) < inicio_sig), 2)                        AS nuevo,
    toDecimal64(0, 2)                                                   AS expansion,
    toDecimal64(0, 2)                                                   AS contraccion,
    round(sumIf(precio_mensualizado, estado_derivado = 'cancelada'
        AND precio_mensualizado IS NOT NULL
        AND fecha_cancelacion IS NOT NULL
        AND toDate(fecha_cancelacion) >= inicio_mes
        AND toDate(fecha_cancelacion) < inicio_sig), 2)                 AS baja,
    round(
        sumIf(precio_mensualizado, estado_derivado = 'vigente'
            AND precio_mensualizado IS NOT NULL
            AND toDate(fecha_alta) >= inicio_mes
            AND toDate(fecha_alta) < inicio_sig)
        - sumIf(precio_mensualizado, estado_derivado = 'cancelada'
            AND precio_mensualizado IS NOT NULL
            AND fecha_cancelacion IS NOT NULL
            AND toDate(fecha_cancelacion) >= inicio_mes
            AND toDate(fecha_cancelacion) < inicio_sig)
    , 2)                                                                AS variacion_neta,
    countIf(estado_derivado = 'vigente' AND precio_mensualizado IS NULL) AS sin_periodicidad,
    'USD'                                                               AS moneda,
    'mensual'                                                           AS periodicidad
FROM hecho_suscripcion FINAL
WHERE {desde:Date} <= {hasta:Date}
  AND toDate(fecha_alta) < inicio_sig
HAVING mrr != 0 OR nuevo != 0 OR baja != 0 OR sin_periodicidad != 0
ORDER BY mes
