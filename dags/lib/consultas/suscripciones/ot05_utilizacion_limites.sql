-- Informe #12 — Utilización de límites · OT05
--
-- ⚠️ Ninguna columna de llamadas API, ni vacía. Un `llamadas: null` afirmaría
-- consumo cero. `nota_dimension_pendiente` declara que esa dimensión llega
-- con Partners.
-- Unidades: `dim_unidad` vigente. Usuarios: aún no hay dimensión propia.

SELECT
    s.idcliente,
    s.plan,
    countDistinct(u.idunidademergencia) AS unidades_usadas,
    p.limite_unidades                   AS unidades_limite,
    CAST(NULL AS Nullable(Int32))       AS usuarios_usados,
    p.limite_usuarios                   AS usuarios_limite,
    'La dimensión de consumo de API llegará con Partners; este informe no afirma consumo cero.'
                                        AS nota_dimension_pendiente
FROM hecho_suscripcion AS s FINAL
INNER JOIN dim_plan AS p FINAL ON p.idplan = s.idplan
LEFT JOIN dim_unidad AS u FINAL
    ON u.idcliente = s.idcliente AND u.es_vigente = 1 AND u.idunidademergencia != -1
WHERE s.estado_derivado = 'vigente'
  AND toDate(s.fecha_alta) <= {hasta:Date}
  AND {desde:Date} <= {hasta:Date}
GROUP BY s.idcliente, s.plan, p.limite_unidades, p.limite_usuarios
ORDER BY s.idcliente
