-- E4-01 índice consolidado. Media sin ponderar de las cuatro componentes.
-- La fórmula se conserva del legado a propósito: cambiarla al migrar
-- haría imposible saber qué movió las cifras.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(a.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(a.fecha),
            toStartOfYear(a.fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    count() AS casos,
    round(avg(if(
        a.severidad IS NOT NULL AND a.tipo_reportado IS NOT NULL
            AND a.hora_confirmacion IS NOT NULL AND a.condado IS NOT NULL,
        1, 0
    )), 4) AS pct_completitud,
    round(avg(a.fue_descartado), 4) AS pct_descarte,
    round(avg(a.es_duplicado), 4) AS pct_fusion,
    countIf(a.num_evidencias > 0) AS con_foto,
    countIf(a.num_notas > 0) AS con_nota,
    countIf(a.num_evidencias > 0 AND a.num_notas > 0) AS con_ambas,
    round(avg(if(a.num_evidencias > 0 OR a.num_notas > 0, 1, 0)), 4) AS pct_cobertura_evidencia,
    round(
        (
            avg(if(
                a.severidad IS NOT NULL AND a.tipo_reportado IS NOT NULL
                    AND a.hora_confirmacion IS NOT NULL AND a.condado IS NOT NULL,
                1, 0
            ))
            + (1 - avg(a.fue_descartado))
            + (1 - avg(a.es_duplicado))
            + avg(if(a.num_evidencias > 0 OR a.num_notas > 0, 1, 0))
        ) / 4,
        4
    ) AS indice_consolidado
FROM hecho_accidente AS a FINAL
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo
ORDER BY periodo
