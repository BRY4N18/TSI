-- C2 · Cumplimiento desglosado por plan · OT19
--
-- Los tickets sin plan se agrupan como 'sin plan', nunca se descartan.

SELECT
    t.idplan AS id_plan,
    coalesce(p.nombre, 'sin plan') AS plan,
    multiIf(
        {granularidad:String} = 'mes', toStartOfMonth(t.fecha),
        {granularidad:String} = 'semana', toStartOfWeek(t.fecha),
        toStartOfDay(t.fecha)
    ) AS periodo,

    countIf(t.tiene_compromiso = 1) AS con_compromiso,
    countIf(t.tiene_compromiso = 0) AS sin_compromiso,
    count()                         AS tickets,
    countIf(t.desenlace_sla = 'cumplido')   AS cumplidos,
    countIf(t.desenlace_sla = 'incumplido') AS incumplidos,

    round(100.0 * countIf(t.desenlace_sla = 'cumplido')
          / nullIf(countIf(t.tiene_compromiso = 1), 0), 2) AS pct_cumplimiento,
    round(100.0 * countIf(t.tiene_compromiso = 0)
          / nullIf(count(), 0), 2) AS pct_sin_compromiso,

    countIf(t.motivo_sin_compromiso = 'pendiente_clasificar') AS motivo_pendiente_clasificar,
    countIf(t.motivo_sin_compromiso = 'sin_compromiso')       AS motivo_sin_compromiso,
    countIf(t.motivo_sin_compromiso = 'sin_config')           AS motivo_sin_config
FROM hecho_ticket AS t FINAL
LEFT JOIN (SELECT idplan, nombre FROM dim_plan FINAL) AS p
       ON t.idplan = p.idplan
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({idagente:Int32} = -1 OR t.idagente = {idagente:Int32})
GROUP BY id_plan, plan, periodo
ORDER BY periodo, plan
