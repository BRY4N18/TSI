-- E1-04 Embudo por transiciones. Etapas del histórico con cero en el período aparecen.

WITH catalogo AS (
    SELECT DISTINCT etapa_nueva AS etapa
    FROM hecho_transicion_embudo
    WHERE etapa_nueva != ''
    UNION DISTINCT
    SELECT DISTINCT etapa_anterior AS etapa
    FROM hecho_transicion_embudo
    WHERE etapa_anterior IS NOT NULL AND etapa_anterior != ''
),
conteo AS (
    SELECT
        etapa_nueva AS etapa,
        count() AS transiciones
    FROM hecho_transicion_embudo
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY etapa_nueva
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
    c.etapa,
    ifNull(n.transiciones, 0) AS transiciones
FROM catalogo AS c
LEFT JOIN conteo AS n ON n.etapa = c.etapa
WHERE {desde:Date} <= {hasta:Date}
ORDER BY transiciones DESC, etapa
