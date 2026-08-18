-- C5 · Tablero de cola · OT20
--
-- ⚠️ Sustituye al tablero actual. Con corte temporal las cifras diferirán
-- a propósito: el original devuelve toda la cola.
-- {sin_periodo:UInt8} = 1 omite el filtro de fechas (cola completa).

SELECT
    multiIf(
        {agrupar_por:String} = 'prioridad', coalesce(prioridad, 'sin prioridad'),
        {agrupar_por:String} = 'tipo', coalesce(tipo, 'sin tipo'),
        {agrupar_por:String} = 'agente',
            if(tiene_agente = 0, 'sin asignar', toString(idagente)),
        coalesce(estado, 'sin estado')
    ) AS clave,
    count()                                 AS tickets,
    countIf(tiene_agente = 0)               AS sin_agente,
    countIf(hora_primera_respuesta IS NULL) AS sin_primera_respuesta,
    countIf(desenlace_sla = 'incumplido')   AS incumplidos
FROM hecho_ticket FINAL
WHERE ({sin_periodo:UInt8} = 1 OR fecha BETWEEN {desde:Date} AND {hasta:Date})
  AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
GROUP BY clave
ORDER BY tickets DESC, clave
