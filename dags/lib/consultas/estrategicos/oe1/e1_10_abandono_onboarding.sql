-- E1-10 Abandono de onboarding contra el catálogo. Ceros del catálogo visibles.

WITH llegadas AS (
    SELECT
        o.idetapa,
        countDistinct(o.idcliente) AS clientes
    FROM hecho_onboarding AS o
    WHERE o.fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY o.idetapa
)
SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    e.orden AS orden,
    e.etapa AS etapa,
    ifNull(l.clientes, 0) AS clientes_completados
FROM dim_etapa_onboarding AS e FINAL
LEFT JOIN llegadas AS l ON l.idetapa = e.idetapa
WHERE {desde:Date} <= {hasta:Date}
ORDER BY e.orden
