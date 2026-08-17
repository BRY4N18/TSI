-- Informe — Regiones en riesgo · OT13
--
-- Regiones **en producción** cuya cobertura de flota está por debajo del umbral.
--
-- ⚠️ Solo las que están en producción, según su versión vigente
-- --------------------------------------------------------------
-- Una región `Definida` o `En validación` no está en riesgo por tener pocas
-- unidades: todavía no opera, y es normal que no las tenga. Meterlas aquí
-- llenaría la lista de falsas alarmas precisamente con las regiones que están
-- haciendo lo correcto, y la lista dejaría de mirarse.
--
-- Y una región **ya despublicada** tampoco está en riesgo: el riesgo ya se
-- materializó, y volver a señalarla es ruido sobre una decisión ya tomada.
--
-- El estado se lee de la versión **vigente al corte**, no de la actual. Una
-- región despublicada mañana no debe desaparecer del informe de riesgo de este
-- mes: si estaba en riesgo en marzo, el informe de marzo tiene que decirlo — de
-- hecho es la evidencia de que el riesgo se veía venir.
--
-- ⚠️ `umbral_unidades` es una convención del informe
-- ---------------------------------------------------
-- El sistema **no define ninguna cobertura mínima por región**. El número lo pone
-- quien consulta, viaja como parámetro y se devuelve en la respuesta: sin verlo,
-- «2 regiones en riesgo» pasaría por una política de la empresa.
--
-- ⚠️ Hoy ninguna región tiene condados asignados —decisión #38, no existe
-- relación región↔condado en el origen— así que todas salen con **0 unidades** y
-- por tanto en riesgo. Es información honesta y visible: la alternativa sería
-- atribuir la flota a una región elegida arbitrariamente.

SELECT
    toDate({hasta:Date})                                    AS corte,
    r.idregionoperativa                                     AS idregion,
    r.nombre_region                                         AS region,
    r.estado_ciclo_vida                                     AS estado_ciclo_vida,
    {umbral_unidades:UInt32}                                AS umbral_aplicado,
    coalesce(c.condados, 0)                                 AS condados,
    coalesce(u.unidades, 0)                                 AS unidades,
    -- Cuántas faltan para salir del riesgo. Publicarlo hace el informe
    -- accionable: «en riesgo» no dice cuánto esfuerzo cuesta salir.
    {umbral_unidades:UInt32} - coalesce(u.unidades, 0)      AS unidades_faltantes
FROM (
    SELECT
        idregionoperativa                       AS idregionoperativa,
        any(nombre_region)                      AS nombre_region,
        any(estado_ciclo_vida)                  AS estado_ciclo_vida
    FROM dim_region FINAL
    WHERE idregionoperativa != -1
      AND valido_desde <= toDateTime({hasta:Date})
      AND (valido_hasta IS NULL OR valido_hasta > toDateTime({hasta:Date}))
    GROUP BY idregionoperativa
) AS r
LEFT JOIN (
    SELECT idregionoperativa, uniqExact(idcondado) AS condados
    FROM dim_geografia FINAL
    WHERE idcondado != -1 AND idregionoperativa IS NOT NULL
    GROUP BY idregionoperativa
) AS c ON c.idregionoperativa = r.idregionoperativa
LEFT JOIN (
    SELECT
        g.idregionoperativa                     AS idregionoperativa,
        -- ⚠️ `uniqExactIf` y no `uniqExact`: el LEFT JOIN sin coincidencia
        -- rellena con el valor por defecto —`0`— y `uniqExact` lo contaría como
        -- una unidad. Una región sin ninguna saldría con una, y justo dejaría de
        -- aparecer en riesgo la que peor está.
        uniqExactIf(un.idunidademergencia, un.idunidademergencia != 0) AS unidades
    FROM (
        SELECT idcondado, any(idregionoperativa) AS idregionoperativa
        FROM dim_geografia FINAL
        WHERE idcondado != -1
        GROUP BY idcondado
    ) AS g
    LEFT JOIN (
        SELECT idcondado, idunidademergencia
        FROM dim_unidad FINAL
        WHERE es_vigente = 1 AND idunidademergencia != -1
    ) AS un ON un.idcondado = g.idcondado
    GROUP BY g.idregionoperativa
) AS u ON u.idregionoperativa = r.idregionoperativa
WHERE r.estado_ciclo_vida = 'Producción'
  AND coalesce(u.unidades, 0) < {umbral_unidades:UInt32}
ORDER BY unidades ASC, region
