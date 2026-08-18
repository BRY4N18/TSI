-- Antigüedad media por tipo y plan · OT17
--
-- Activo: hasta hoy. Con baja: hasta fecha_baja. Reutiliza dim_plan.

SELECT
    c.tipo AS tipo_cliente,
    p.nombre AS plan,
    count() AS clientes,
    round(
        median(
            dateDiff(
                'day',
                toDate(c.fecha_alta),
                if(c.fecha_baja IS NULL, today(), toDate(c.fecha_baja))
            )
        ),
        1
    ) AS dias_mediana
FROM dim_cliente AS c FINAL
LEFT JOIN (
    SELECT idcliente, argMax(idplan, fecha) AS idplan
    FROM hecho_suscripcion FINAL
    GROUP BY idcliente
) AS s ON s.idcliente = c.idcliente
LEFT JOIN dim_plan AS p FINAL ON p.idplan = s.idplan
WHERE c.fecha_alta IS NOT NULL
  AND toDate(c.fecha_alta) <= {hasta:Date}
  AND {desde:Date} <= {hasta:Date}
GROUP BY tipo_cliente, plan
ORDER BY tipo_cliente, plan
