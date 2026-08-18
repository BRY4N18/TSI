-- C3 · Rendimiento por agente · OT19
--
-- ⚠️ CLAVE del agente, jamás nombre.
-- ⚠️ avg ignora nulos; sin_resolver dice cuántos ignoró.

SELECT
    idagente AS id_agente,
    count()                              AS asignados,
    countIf(hora_resolucion IS NOT NULL AND fue_reabierto = 0) AS resueltos,
    countIf(desenlace_sla = 'incumplido') AS incumplidos,
    countIf(fue_reabierto = 1)           AS reabiertos,
    round(avg(segundos_resolucion), 0)   AS media_resolucion_s,
    countIf(segundos_resolucion IS NULL) AS sin_resolver
FROM hecho_ticket FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND tiene_agente = 1
  AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
GROUP BY idagente
ORDER BY incumplidos DESC, id_agente
