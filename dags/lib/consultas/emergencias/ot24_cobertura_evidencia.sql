-- Informe #17 — Cobertura de evidencia por severidad y región · OT24
--
-- De los casos del período, cuántos llevan foto, cuántos nota, cuántos las dos y
-- cuántos ninguna.
--
-- Los cuatro grupos son excluyentes y suman el total
-- --------------------------------------------------
-- «Con foto» aquí significa **solo foto**. Si incluyera los que además tienen
-- nota, los porcentajes sumarían más de 100 % y el reparto dejaría de leerse. Y
-- hay una razón mejor: «solo foto» y «foto y nota» son dos situaciones
-- distintas, porque un caso grave documentado solo con imágenes y sin una sola
-- nota es precisamente el que hay que mirar.
--
-- ⚠️ Los casos SIN NINGUNA evidencia son el motivo del informe
-- ------------------------------------------------------------
-- Se cuentan con un `LEFT JOIN` **desde los casos**, no con un `JOIN` desde las
-- evidencias. La diferencia lo es todo: partiendo de las evidencias, un caso sin
-- ninguna no aparece en ninguna fila, y la cobertura saldría del 100 % siempre —
-- el informe diría que todo está documentado justamente porque no ve lo que
-- falta.
--
-- Los casos sin ubicación o sin severidad salen bajo 'Desconocido', igual que en
-- el resto del catálogo: filtrarlos dejaría fuera los peor registrados, que son
-- los que más probablemente tampoco se documentaron.

SELECT
    coalesce(a.severidad, 'Desconocido')            AS severidad,
    coalesce(a.condado, 'Desconocido')              AS condado,
    count()                                         AS casos,
    countIf(e.fotos > 0 AND e.notas = 0)            AS solo_foto,
    countIf(e.fotos = 0 AND e.notas > 0)            AS solo_nota,
    countIf(e.fotos > 0 AND e.notas > 0)            AS foto_y_nota,
    countIf(e.fotos = 0 AND e.notas = 0)            AS sin_evidencia,
    round(countIf(e.fotos > 0 OR e.notas > 0) / count(), 4) AS pct_con_alguna
FROM hecho_accidente AS a FINAL
LEFT JOIN (
    SELECT
        idaccidente                     AS idaccidente,
        countIf(tipo = 'foto')          AS fotos,
        countIf(tipo = 'nota')          AS notas
    FROM hecho_evidencia
    GROUP BY idaccidente
) AS e ON e.idaccidente = a.idaccidente
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY severidad, condado
ORDER BY casos DESC, severidad, condado
