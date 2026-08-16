-- Informe #2 — Distribución por zona · OT21 · origen: OP32
--
-- Cuántos casos hubo en cada condado, y qué peso tiene cada uno.
--
-- ⚠️ Un caso cuya calle no está en el catálogo aparece bajo 'Desconocido'
-- ----------------------------------------------------------------------
-- No desaparece. Perder un accidente del recuento porque falta una fila en un
-- catálogo de calles es inaceptable, y además invisible: los porcentajes de los
-- demás condados seguirían sumando 100 % entre ellos.

SELECT
    toDate({desde:Date})                          AS periodo,
    coalesce(condado, 'Desconocido')              AS condado,
    count()                                       AS casos,
    round(count() / sum(count()) OVER (), 4)      AS pct
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY condado
ORDER BY casos DESC, condado
