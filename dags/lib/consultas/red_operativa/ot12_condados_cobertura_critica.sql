-- Informe — Condados en cobertura crítica · OT12
--
-- Condados con menos unidades de las que marca el umbral, y si tienen vecinos a
-- los que recurrir.
--
-- ⚠️ UN CONDADO SIN VECINOS APARECE, SEÑALADO. NO SE OMITE
-- --------------------------------------------------------
-- Es la situación **más grave** que este informe puede reportar: pocas unidades y
-- ningún condado del que traerlas. La tentación al escribirlo es unir con la
-- vecindad y quedarse con lo que casa, y eso hace desaparecer precisamente el
-- caso peor — el informe de cobertura crítica dejaría fuera la cobertura más
-- crítica.
--
-- Por eso `condados_vecinos` es un atributo de `dim_geografia` y no una unión: un
-- array vacío es un valor, no una fila que falta.
--
-- ⚠️ `umbral_unidades` es UNA CONVENCIÓN DEL INFORME, NO UNA POLÍTICA
-- -------------------------------------------------------------------
-- El origen **no define ningún umbral de cobertura mínima**. El que se aplique
-- aquí es una convención de quien consulta, y por eso viaja como parámetro y se
-- devuelve en la respuesta: quien lea «3 condados en estado crítico» tiene que
-- poder ver contra qué número se midió. Sin eso, una cifra elegida por defecto
-- pasaría por una política de la empresa.
--
-- Las unidades se cuentan sobre la **versión vigente**: la pregunta es qué
-- cobertura hay ahora. `{hasta:Date}` acota hasta cuándo se considera vigente.

SELECT
    g.idcondado                                     AS idcondado,
    g.condado                                       AS condado,
    {umbral_unidades:UInt32}                        AS umbral_aplicado,
    coalesce(u.unidades, 0)                         AS unidades,
    length(g.condados_vecinos)                      AS vecinos_declarados,
    -- El caso peor, marcado y no omitido.
    length(g.condados_vecinos) = 0                  AS sin_alternativas,
    -- Unidades disponibles en los condados vecinos. Cero con vecinos declarados
    -- es distinto de cero sin ninguno: en el primer caso hay a quién llamar.
    coalesce(v.unidades_vecinas, 0)                 AS unidades_vecinas
FROM (
    SELECT
        idcondado                       AS idcondado,
        any(condado)                    AS condado,
        any(condados_vecinos)           AS condados_vecinos
    FROM dim_geografia FINAL
    WHERE idcondado != -1
    GROUP BY idcondado
) AS g
LEFT JOIN (
    SELECT idcondado, uniqExact(idunidademergencia) AS unidades
    FROM dim_unidad FINAL
    WHERE es_vigente = 1
      AND idunidademergencia != -1
      AND toDate(valido_desde) <= {hasta:Date}
    GROUP BY idcondado
) AS u ON u.idcondado = g.idcondado
-- ⚠️ La vecindad se explota con `arrayJoin` antes de unir. ClickHouse no admite
-- `has(izquierda.array, derecha.columna)` en un `ON` —falla con «join expression
-- contains column from left and right table»—, así que el array se convierte en
-- filas y la unión pasa a ser una igualdad normal.
--
-- El `arrayJoin` va sobre una copia de `g`, **no sobre `g`**: hacerlo en la
-- fuente multiplicaría las filas del condado por su número de vecinos y las
-- unidades propias se contarían varias veces.
LEFT JOIN (
    SELECT
        vecindad.idcondado                      AS idcondado,
        -- ⚠️ `uniqExactIf` y no `uniqExact`: el LEFT JOIN sin coincidencia
        -- rellena con el **valor por defecto del tipo** —`0`—, no con NULL, y
        -- `uniqExact` lo contaria como una unidad distinta. Un condado vecino
        -- sin ninguna unidad saldria con **una**, y la cobertura critica diria
        -- que hay a quien recurrir cuando no lo hay.
        --
        -- Es la tercera vez que este relleno muerde en el proyecto: ya paso con
        -- el nombre de calle del ranking de Emergencias y con el nombre de
        -- region de la cobertura por region.
        uniqExactIf(u.idunidademergencia, u.idunidademergencia != 0) AS unidades_vecinas
    FROM (
        SELECT idcondado, arrayJoin(condados_vecinos) AS idvecino
        FROM (
            SELECT idcondado, any(condados_vecinos) AS condados_vecinos
            FROM dim_geografia FINAL
            WHERE idcondado != -1
            GROUP BY idcondado
        )
    ) AS vecindad
    LEFT JOIN (
        SELECT idcondado, idunidademergencia
        FROM dim_unidad FINAL
        WHERE es_vigente = 1 AND idunidademergencia != -1
    ) AS u ON u.idcondado = vecindad.idvecino
    GROUP BY vecindad.idcondado
) AS v ON v.idcondado = g.idcondado
WHERE coalesce(u.unidades, 0) < {umbral_unidades:UInt32}
ORDER BY sin_alternativas DESC, unidades ASC, condado
