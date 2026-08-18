-- Churn por cohorte de alta (BSC) · OT17
--
-- ⚠️ Agrupa por cohorte de alta, no por mes de baja.
-- ⚠️ FINAL obligatorio: dim_cliente es ReplacingMergeTree.

SELECT
    cohorte_alta,
    count() AS clientes_iniciales,
    countIf(
        fecha_baja IS NOT NULL
        AND toDate(fecha_baja) BETWEEN {desde:Date} AND {hasta:Date}
    ) AS bajas,
    round(
        countIf(
            fecha_baja IS NOT NULL
            AND toDate(fecha_baja) BETWEEN {desde:Date} AND {hasta:Date}
        ) / nullIf(count(), 0),
        4
    ) AS pct_churn,
    nullIf(
        arrayStringConcat(
            arrayFilter(
                x -> x != '',
                groupUniqArray(ifNull(motivo_baja, ''))
            ),
            ', '
        ),
        ''
    ) AS motivo
FROM dim_cliente FINAL
WHERE cohorte_alta IS NOT NULL
  AND ({mes_cohorte:String} = '' OR cohorte_alta = {mes_cohorte:String})
  AND {desde:Date} <= {hasta:Date}
GROUP BY cohorte_alta
ORDER BY cohorte_alta
