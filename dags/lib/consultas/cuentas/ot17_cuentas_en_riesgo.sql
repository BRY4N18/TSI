-- Cuentas en riesgo: sin sesión en N días · OT17
--
-- ⚠️ sin_actividad_conocida = 1 si nunca hubo sesión. Nunca 0 días.
-- LEFT JOIN sobre hecho_sesion rellena DateTime/Int32 con 1970 y 0: se filtra.

WITH
    miembros AS (
        SELECT idusuario, idcliente
        FROM dim_usuario_organizacion FINAL
        WHERE tiene_pertenencia = 1
    ),
    ultimas AS (
        SELECT
            idusuario,
            CAST(max(fechahora_inicio) AS Nullable(DateTime)) AS ultima_sesion
        FROM hecho_sesion
        GROUP BY idusuario
    )
SELECT
    c.idcliente AS idcliente,
    max(u_s.ultima_sesion) AS ultima_sesion,
    if(
        count(u_s.ultima_sesion) = 0,
        NULL,
        dateDiff('day', toDate(max(u_s.ultima_sesion)), today())
    ) AS dias_sin_actividad,
    if(count(u_s.ultima_sesion) = 0, 1, 0) AS sin_actividad_conocida
FROM dim_cliente AS c FINAL
LEFT JOIN miembros AS u ON u.idcliente = c.idcliente
LEFT JOIN ultimas AS u_s ON u_s.idusuario = u.idusuario
WHERE c.idcliente != -1
  AND {desde:Date} <= {hasta:Date}
GROUP BY c.idcliente
HAVING
    sin_actividad_conocida = 1
    OR dias_sin_actividad >= {dias_inactividad:Int32}
ORDER BY idcliente
