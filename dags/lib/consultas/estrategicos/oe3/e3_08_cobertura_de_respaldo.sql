-- Informe E3-08 — Cobertura de respaldo por condado vecino
-- Desbloqueado al cargar dim_condado_vecino (research D3).
--
-- ⚠️ DISPONIBLE, NO EXISTENTE
-- Un vecino con unidades dadas de alta pero todas ocupadas, en misión o
-- fuera de servicio no es respaldo. Se lee el último estado de
-- hecho_estado_unidad (transacción: PROHIBIDO FINAL) y solo cuenta
-- `Activa`. Es el error que Red Operativa documentó como el más caro.
--
-- ⚠️ UN CONDADO SIN VECINOS APARECE, NO SE OMITE
-- LEFT JOIN desde la geografía. Un INNER JOIN con la vecindad haría
-- desaparecer precisamente el caso peor.
--
-- {desde:Date} etiqueta el período; el último estado se toma hasta
-- {hasta:Date} inclusive.

WITH
condados AS (
    SELECT
        g.idcondado AS idcondado,
        g.condado   AS condado
    FROM (
        SELECT idcondado, any(condado) AS condado
        FROM dim_geografia FINAL
        WHERE idcondado != -1
        GROUP BY idcondado
    ) AS g
    INNER JOIN (
        SELECT DISTINCT coalesce(condado, 'Desconocido') AS condado
        FROM hecho_accidente FINAL
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
          AND fue_descartado = 0
          AND es_duplicado = 0
    ) AS a ON a.condado = g.condado
),
vecindad AS (
    SELECT
        idcondado,
        idcondadovecino
    FROM dim_condado_vecino FINAL
    WHERE idcondado != -1
      AND idcondadovecino != -1
),
ultimo_estado AS (
    SELECT
        idunidademergencia,
        argMax(estado_nuevo, fechahora) AS estado,
        argMax(sk_unidad, fechahora)    AS sk_unidad
    FROM hecho_estado_unidad
    WHERE fecha <= {hasta:Date}
    GROUP BY idunidademergencia
),
unidades_disponibles AS (
    SELECT
        coalesce(u.idcondado, -1) AS idcondado
    FROM ultimo_estado AS e
    INNER JOIN dim_unidad AS u FINAL ON u.sk_unidad = e.sk_unidad
    WHERE e.estado = 'Activa'
      AND u.idunidademergencia != -1
)
SELECT
    toDate({desde:Date})                         AS periodo,
    c.condado                                    AS condado,
    count(DISTINCT v.idcondadovecino)            AS vecinos,
    uniqExactIf(d.idcondado, d.idcondado != 0 AND d.idcondado IS NOT NULL)
                                                 AS vecinos_con_unidad_disponible,
    if(
        count(DISTINCT v.idcondadovecino) = 0,
        NULL,
        round(
            uniqExactIf(d.idcondado, d.idcondado != 0 AND d.idcondado IS NOT NULL)
            / count(DISTINCT v.idcondadovecino),
            4
        )
    )                                            AS pct_respaldo
FROM condados AS c
LEFT JOIN vecindad AS v ON v.idcondado = c.idcondado
LEFT JOIN unidades_disponibles AS d ON d.idcondado = v.idcondadovecino
GROUP BY c.condado
ORDER BY c.condado
