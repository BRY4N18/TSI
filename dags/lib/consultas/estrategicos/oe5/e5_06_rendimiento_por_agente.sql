-- E5-06 Carga por agente. Clave idagente, jamás nombre.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    t.idagente AS idagente,
    count() AS asignados,
    countIf(t.hora_resolucion IS NOT NULL AND t.fue_reabierto = 0) AS resueltos,
    countIf(t.desenlace_sla = 'incumplido') AS incumplidos,
    countIf(t.fue_reabierto = 1) AS reabiertos,
    round(avg(t.segundos_resolucion), 0) AS media_resolucion_s
FROM hecho_ticket AS t FINAL
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND t.tiene_agente = 1
GROUP BY periodo, idagente
ORDER BY periodo, incumplidos DESC, idagente
