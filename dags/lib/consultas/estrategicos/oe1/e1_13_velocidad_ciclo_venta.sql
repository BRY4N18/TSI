-- E1-13 Tiempo por etapa y ejecutivo vigente. Sin ficha de prospecto.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    ifNull(t.etapa_anterior, '(inicio)') AS etapa,
    a.idejecutivo AS idejecutivo,
    round(avg(t.segundos_en_etapa_anterior), 1) AS segundos_promedio,
    count() AS transiciones
FROM hecho_transicion_embudo AS t
INNER JOIN (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS idejecutivo
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
) AS a ON a.idprospecto = t.idprospecto
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND t.segundos_en_etapa_anterior IS NOT NULL
GROUP BY periodo, etapa, idejecutivo
ORDER BY periodo, etapa, idejecutivo
