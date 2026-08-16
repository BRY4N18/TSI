-- Informe #1 — Distribución por severidad · OT21 · origen: OP32
--
-- Cuántos casos hubo de cada gravedad en el período, y qué peso tiene cada una.
--
-- ⚠️ Ningún caso queda fuera del reparto
-- --------------------------------------
-- Un caso sin severidad registrada aparece bajo **'Desconocido'**, no
-- desaparece. Filtrar los que no tienen severidad daría un reparto que suma
-- menos que el total del período, y nadie que mire solo este informe podría
-- notarlo: los porcentajes seguirían sumando 100 % **entre ellos**.
--
-- Es la misma razón por la que el porcentaje se calcula sobre el total del
-- período y no sobre el total de los clasificados.

SELECT
    toDate({desde:Date})                          AS periodo,
    coalesce(severidad, 'Desconocido')            AS severidad,
    count()                                       AS casos,
    round(count() / sum(count()) OVER (), 4)      AS pct
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY severidad
ORDER BY casos DESC, severidad
