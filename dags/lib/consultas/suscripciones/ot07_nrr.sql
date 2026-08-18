-- Informe #8 — NRR · OT07
--
-- Cohorte de clientes **existentes al inicio del mes**. Los nuevos se excluyen:
-- incluirlos convertiría el NRR en crecimiento bruto.
-- ⚠️ FINAL en hecho_suscripcion.

WITH
    toDate(concat({mes:String}, '-01')) AS inicio_mes,
    addMonths(inicio_mes, 1)            AS inicio_sig,
    cohorte AS (
        SELECT
            idcliente,
            precio_mensualizado,
            estado_derivado,
            fecha_cancelacion
        FROM hecho_suscripcion FINAL
        WHERE toDate(fecha_alta) < inicio_mes
          AND precio_mensualizado IS NOT NULL
          AND (
                estado_derivado = 'vigente'
                OR (
                    estado_derivado = 'cancelada'
                    AND fecha_cancelacion IS NOT NULL
                    AND toDate(fecha_cancelacion) >= inicio_mes
                )
              )
    )
SELECT
    {mes:String} AS mes,
    round(sum(precio_mensualizado), 2) AS mrr_inicial,
    toDecimal64(0, 2)                  AS expansion,
    toDecimal64(0, 2)                  AS contraccion,
    round(sumIf(precio_mensualizado, estado_derivado = 'cancelada'
        AND fecha_cancelacion IS NOT NULL
        AND toDate(fecha_cancelacion) >= inicio_mes
        AND toDate(fecha_cancelacion) < inicio_sig), 2) AS baja,
    if(sum(precio_mensualizado) = 0, NULL,
        round(
            toFloat64(sum(precio_mensualizado)
                - sumIf(precio_mensualizado, estado_derivado = 'cancelada'
                    AND fecha_cancelacion IS NOT NULL
                    AND toDate(fecha_cancelacion) >= inicio_mes
                    AND toDate(fecha_cancelacion) < inicio_sig)
            ) / toFloat64(sum(precio_mensualizado)),
            4
        )
    ) AS nrr,
    'USD'     AS moneda,
    'mensual' AS periodicidad
FROM cohorte
WHERE {desde:Date} <= {hasta:Date}
HAVING mrr_inicial != 0
ORDER BY mes
