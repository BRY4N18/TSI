-- Informe #13 — Severidades habilitadas vs usadas · OT05
--
-- Primer informe del proyecto que une el dominio financiero con el operativo.
-- Una habilitada y no usada aparece: el cliente paga por algo que no necesita.
-- Los casos se agregan por severidad para no inflar el recuento al cruzar.

SELECT
    s.plan,
    ifNull(nullIf(sev.severidad, ''), concat('id:', toString(s.idseveridad))) AS severidad,
    toUInt8(1) AS habilitada,
    ifNull(casos.n, 0) AS casos_atendidos
FROM (
    SELECT DISTINCT s.plan, idseveridad
    FROM hecho_suscripcion AS s FINAL
    INNER JOIN dim_plan AS p FINAL ON p.idplan = s.idplan
    ARRAY JOIN p.severidades_habilitadas AS idseveridad
    WHERE s.estado_derivado = 'vigente'
      AND toDate(s.fecha_alta) <= {hasta:Date}
      AND {desde:Date} <= {hasta:Date}
) AS s
LEFT JOIN dim_severidad AS sev FINAL ON sev.idseveridad = s.idseveridad
LEFT JOIN (
    SELECT idseveridad, count() AS n
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY idseveridad
) AS casos ON casos.idseveridad = s.idseveridad
ORDER BY s.plan, s.idseveridad
