-- C6 · Evolución temporal del incumplimiento · OT20
--
-- Los períodos sin tickets aparecen con cero (WITH FILL sobre el día, luego
-- se reagrupa). Un hueco se leería como un buen período.

SELECT
    multiIf(
        {granularidad:String} = 'mes', toStartOfMonth(dia),
        {granularidad:String} = 'semana', toStartOfWeek(dia),
        dia
    ) AS periodo,
    sum(con_compromiso) AS con_compromiso,
    sum(sin_compromiso) AS sin_compromiso,
    sum(tickets)        AS tickets,
    sum(cumplidos)      AS cumplidos,
    sum(incumplidos)    AS incumplidos,
    round(100.0 * sum(cumplidos) / nullIf(sum(con_compromiso), 0), 2) AS pct_cumplimiento,
    round(100.0 * sum(sin_compromiso) / nullIf(sum(tickets), 0), 2) AS pct_sin_compromiso,
    round(100.0 * sum(incumplidos) / nullIf(sum(con_compromiso), 0), 2) AS pct_incumplimiento,
    sum(motivo_pendiente_clasificar) AS motivo_pendiente_clasificar,
    sum(motivo_sin_compromiso)       AS motivo_sin_compromiso,
    sum(motivo_sin_config)           AS motivo_sin_config
FROM (
    SELECT
        fecha AS dia,
        countIf(tiene_compromiso = 1) AS con_compromiso,
        countIf(tiene_compromiso = 0) AS sin_compromiso,
        count() AS tickets,
        countIf(desenlace_sla = 'cumplido') AS cumplidos,
        countIf(desenlace_sla = 'incumplido') AS incumplidos,
        countIf(motivo_sin_compromiso = 'pendiente_clasificar') AS motivo_pendiente_clasificar,
        countIf(motivo_sin_compromiso = 'sin_compromiso') AS motivo_sin_compromiso,
        countIf(motivo_sin_compromiso = 'sin_config') AS motivo_sin_config
    FROM hecho_ticket FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY fecha
    ORDER BY fecha
    WITH FILL FROM {desde:Date} TO {hasta:Date} + INTERVAL 1 DAY STEP INTERVAL 1 DAY
)
GROUP BY periodo
ORDER BY periodo
