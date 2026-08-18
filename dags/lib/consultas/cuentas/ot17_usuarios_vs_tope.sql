-- Usuarios por cliente frente al tope del plan · OT17
--
-- ⚠️ pct_cobertura_pertenencia: hoy ~9,5 %. Sin él, ocupación se lee como real.
-- ⚠️ Cliente sin plan: pct_ocupacion ausente, nunca 0 %.
-- Los usuarios sin pertenencia no se reparte entre clientes.

WITH
    cobertura AS (
        SELECT
            round(
                countIf(tiene_pertenencia = 1) / nullIf(count(), 0),
                4
            ) AS pct_cobertura_pertenencia
        FROM dim_usuario_organizacion FINAL
    ),
    usuarios AS (
        SELECT
            idcliente,
            count() AS usuarios_conocidos
        FROM dim_usuario_organizacion FINAL
        WHERE tiene_pertenencia = 1
          AND idcliente IS NOT NULL
        GROUP BY idcliente
    ),
    plan_actual AS (
        SELECT idcliente, argMax(idplan, fecha) AS idplan
        FROM hecho_suscripcion FINAL
        GROUP BY idcliente
    )
SELECT
    c.idcliente AS idcliente,
    ifNull(u.usuarios_conocidos, 0) AS usuarios_conocidos,
    p.limite_usuarios AS tope_plan,
    if(
        p.limite_usuarios IS NULL,
        NULL,
        round(ifNull(u.usuarios_conocidos, 0) / nullIf(p.limite_usuarios, 0), 4)
    ) AS pct_ocupacion,
    (SELECT pct_cobertura_pertenencia FROM cobertura) AS pct_cobertura_pertenencia
FROM dim_cliente AS c FINAL
LEFT JOIN usuarios AS u ON u.idcliente = c.idcliente
LEFT JOIN plan_actual AS s ON s.idcliente = c.idcliente
LEFT JOIN (SELECT idplan, limite_usuarios FROM dim_plan FINAL) AS p
    ON p.idplan = s.idplan
WHERE c.idcliente != -1
  AND {desde:Date} <= {hasta:Date}
ORDER BY idcliente
