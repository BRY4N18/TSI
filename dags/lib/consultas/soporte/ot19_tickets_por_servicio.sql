-- C4 · Tickets por servicio afectado · OT19
--
-- Hoy idservicio es nulo en todos los tickets. La fila «sin servicio» es la
-- evidencia de que la asignación no se registra.

SELECT
    t.idservicio AS id_servicio,
    coalesce(s.nombre, 'sin servicio') AS servicio,
    count() AS tickets,
    countIf(t.desenlace_sla = 'incumplido') AS incumplidos
FROM hecho_ticket AS t FINAL
LEFT JOIN (SELECT id_servicio, nombre FROM dim_servicio FINAL) AS s
       ON t.idservicio = s.id_servicio
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({idagente:Int32} = -1 OR t.idagente = {idagente:Int32})
GROUP BY id_servicio, servicio
ORDER BY tickets DESC, servicio
