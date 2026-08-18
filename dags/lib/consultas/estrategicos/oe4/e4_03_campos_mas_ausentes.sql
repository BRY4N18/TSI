-- E4-03 ranking de ausencia. Incluye campos con cero ausencias:
-- uno que desaparece de la lista se confunde con uno que nadie revisó.

SELECT campo, ausencias, casos, round(ausencias / nullIf(casos, 0), 4) AS pct_ausencia
FROM (
    SELECT 'severidad' AS campo,
           countIf(severidad IS NULL) AS ausencias,
           count() AS casos
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    UNION ALL
    SELECT 'tipo_reportado', countIf(tipo_reportado IS NULL), count()
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    UNION ALL
    SELECT 'hora_confirmacion', countIf(hora_confirmacion IS NULL), count()
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    UNION ALL
    SELECT 'condado', countIf(condado IS NULL), count()
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    UNION ALL
    SELECT 'ciudad', countIf(ciudad IS NULL), count()
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
)
ORDER BY pct_ausencia DESC, campo
