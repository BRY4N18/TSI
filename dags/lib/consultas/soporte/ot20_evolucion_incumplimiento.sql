-- C6 · Evolución temporal del incumplimiento · OT20
--
-- Los períodos sin tickets aparecen con cero (WITH FILL sobre el día, luego
-- se reagrupa). Un hueco se leería como un buen período.
--
-- ⚠️ `hecho_ticket AS t` y `t.motivo_sin_compromiso` **calificados a propósito**.
-- Sin el alias de tabla, `countIf(motivo_sin_compromiso = ...) AS
-- motivo_sin_compromiso` hace que el analizador resuelva el argumento contra su
-- **propio alias de salida** en vez de contra la columna, y ClickHouse rechaza
-- la consulta entera con ILLEGAL_AGGREGATION («agregado dentro de otro
-- agregado»). El informe devolvía 500, no una cifra equivocada.
--
-- ⚠️ Las columnas internas llevan sufijo `_dia` **y no pueden llamarse igual que
-- las de salida**. Con `sum(cumplidos) AS cumplidos`, el `sum(cumplidos)` de los
-- porcentajes se resolvía contra el alias de salida —que ya es un agregado— y
-- ClickHouse rechazaba la consulta entera con ILLEGAL_AGGREGATION. El informe
-- devolvía 500, no una cifra equivocada.

SELECT
    multiIf(
        {granularidad:String} = 'mes', toStartOfMonth(dia),
        {granularidad:String} = 'semana', toStartOfWeek(dia),
        dia
    ) AS periodo,
    sum(con_compromiso_dia) AS con_compromiso,
    sum(sin_compromiso_dia) AS sin_compromiso,
    sum(tickets_dia)        AS tickets,
    sum(cumplidos_dia)      AS cumplidos,
    sum(incumplidos_dia)    AS incumplidos,
    round(100.0 * sum(cumplidos_dia) / nullIf(sum(con_compromiso_dia), 0), 2) AS pct_cumplimiento,
    round(100.0 * sum(sin_compromiso_dia) / nullIf(sum(tickets_dia), 0), 2) AS pct_sin_compromiso,
    round(100.0 * sum(incumplidos_dia) / nullIf(sum(con_compromiso_dia), 0), 2) AS pct_incumplimiento,
    sum(motivo_pendiente_clasificar_dia) AS motivo_pendiente_clasificar,
    sum(motivo_sin_compromiso_dia)       AS motivo_sin_compromiso,
    sum(motivo_sin_config_dia)           AS motivo_sin_config
FROM (
    SELECT
        fecha AS dia,
        countIf(tiene_compromiso = 1) AS con_compromiso_dia,
        countIf(tiene_compromiso = 0) AS sin_compromiso_dia,
        count() AS tickets_dia,
        countIf(desenlace_sla = 'cumplido') AS cumplidos_dia,
        countIf(desenlace_sla = 'incumplido') AS incumplidos_dia,
        countIf(t.motivo_sin_compromiso = 'pendiente_clasificar') AS motivo_pendiente_clasificar_dia,
        countIf(t.motivo_sin_compromiso = 'sin_compromiso') AS motivo_sin_compromiso_dia,
        countIf(t.motivo_sin_compromiso = 'sin_config') AS motivo_sin_config_dia
    FROM hecho_ticket AS t FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY fecha
    ORDER BY fecha
    WITH FILL FROM {desde:Date} TO {hasta:Date} + INTERVAL 1 DAY STEP INTERVAL 1 DAY
)
GROUP BY periodo
ORDER BY periodo
