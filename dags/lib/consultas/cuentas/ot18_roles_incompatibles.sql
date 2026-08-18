-- Usuarios con roles incompatibles · OT18
--
-- ⚠️ pares vacío → cero filas. El multi-rol es el mecanismo previsto.
-- ⚠️ Devuelve idusuario y ambos roles, nunca el nombre de la persona.
-- ClickHouse 24.8 no admite `idrol < idrol` en ON; se cruza contra el par.

WITH
    pares AS (
        SELECT
            splitByChar(':', pair)[1] AS rol_a,
            splitByChar(':', pair)[2] AS rol_b
        FROM (
            SELECT arrayJoin(
                if(
                    {pares:String} = '',
                    emptyArrayString(),
                    splitByChar(',', {pares:String})
                )
            ) AS pair
        )
        WHERE pair != ''
    ),
    por_usuario AS (
        SELECT
            idusuario,
            groupArray(rol) AS roles
        FROM dim_usuario_rol FINAL
        WHERE es_activo = 1
        GROUP BY idusuario
    )
SELECT
    u.idusuario AS idusuario,
    p.rol_a AS rol_a,
    p.rol_b AS rol_b,
    concat(p.rol_a, ':', p.rol_b) AS par_declarado
FROM por_usuario AS u
CROSS JOIN pares AS p
WHERE has(u.roles, p.rol_a)
  AND has(u.roles, p.rol_b)
  AND p.rol_a != p.rol_b
  AND {pares:String} != ''
  AND {desde:Date} <= {hasta:Date}
ORDER BY idusuario, rol_a, rol_b
