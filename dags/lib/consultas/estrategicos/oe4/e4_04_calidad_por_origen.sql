-- E4-04 calidad central vs campo. categoria_nota de evidencia; sin desglose por persona.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(a.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(a.fecha),
            toStartOfYear(a.fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    if(e.categoria_nota = 'campo', 'campo', 'central') AS origen,
    count() AS casos,
    round(avg(if(
        a.severidad IS NOT NULL AND a.tipo_reportado IS NOT NULL
            AND a.hora_confirmacion IS NOT NULL AND a.condado IS NOT NULL,
        1, 0
    )), 4) AS pct_completitud
FROM hecho_accidente AS a FINAL
LEFT JOIN (
    SELECT idaccidente, any(categoria_nota) AS categoria_nota
    FROM hecho_evidencia
    GROUP BY idaccidente
) AS e ON e.idaccidente = a.idaccidente
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, origen
ORDER BY periodo, origen
