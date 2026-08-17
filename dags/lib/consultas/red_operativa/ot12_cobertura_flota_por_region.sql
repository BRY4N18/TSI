-- Informe — Cobertura de flota por región · OT12
--
-- Cuántas unidades cubren cada región operativa.
--
-- ⚠️ HOY DEVUELVE TODO BAJO «SIN REGIÓN», Y ESO ES LO CORRECTO
-- ------------------------------------------------------------
-- **No existe ninguna tabla que ate región y condado** en el origen. Se comprobó
-- sobre el catálogo entero: las únicas tablas de región son
-- `Dim_RegionOperativa`, `Dim_RegionOperativaEstadoRegion` —que guarda geografía,
-- no ciclo de vida— y `Dim_ValidacionRegion`.
--
-- La única pista es `Dim_RegionOperativa.idestado`, es decir el **estado**
-- geográfico. Derivar «condado → estado → región» tendría sentido si cada estado
-- tuviera una región, y hoy **las dos regiones del sistema comparten el mismo
-- estado**. Un diccionario `idestado → region` atribuiría todos los condados a
-- la última que devolviera Pinot, sin orden garantizado — con los datos de hoy,
-- todos a una región de pruebas.
--
-- La carga deja `idregionoperativa` **ausente** cuando el estado tiene más de una
-- región, así que este informe sale hoy con todo bajo «Sin región asignada». Es
-- información honesta y visible: la alternativa era una cobertura completa y
-- equivocada, que es el peor resultado posible porque nadie la cuestionaría.
--
-- Queda como **decisión pendiente #38**. Cuando exista la relación región↔condado
-- —o se confirme que una región es un estado— este informe empieza a repartir sin
-- tocar una línea.
--
-- El nombre de la región sale de `dim_region`, que está versionada: se toma la
-- versión **vigente al final del período**, no la de hoy. Una región despublicada
-- después no reescribe la cobertura de entonces.

SELECT
    -- ⚠️ `nullIf(..., '')` y no `coalesce` a secas: en ClickHouse un LEFT JOIN
    -- sin coincidencia rellena con el **valor por defecto del tipo**, no con
    -- NULL. Una región sin resolver vuelve como cadena vacía y `coalesce` no
    -- dispara, así que la fila saldría con la región **en blanco** — que se lee
    -- como un fallo de maquetación y significa que no se sabe qué región cubre
    -- ese condado. Es el mismo defecto que ya apareció en el ranking de
    -- ubicaciones de Emergencias.
    coalesce(nullIf(r.nombre_region, ''), 'Sin región asignada')   AS region,
    coalesce(nullIf(r.estado_ciclo_vida, ''), 'Desconocido')       AS estado_ciclo_vida,
    uniqExact(g.idcondado)                                  AS condados,
    uniqExact(u.idunidademergencia)                         AS unidades,
    -- Unidades por condado: una región con veinte unidades en un condado y
    -- ninguna en los otros cinco no está cubierta, está concentrada.
    if(
        uniqExact(g.idcondado) = 0,
        NULL,
        round(uniqExact(u.idunidademergencia) / uniqExact(g.idcondado), 2)
    )                                                       AS unidades_por_condado
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
) AS u ON u.idcondado = g.idcondado
LEFT JOIN (
    SELECT idregionoperativa, nombre_region, estado_ciclo_vida
    FROM dim_region FINAL
    WHERE valido_desde <= toDateTime({hasta:Date})
      AND (valido_hasta IS NULL OR valido_hasta > toDateTime({hasta:Date}))
) AS r ON r.idregionoperativa = g.idregionoperativa
GROUP BY region, estado_ciclo_vida
ORDER BY unidades DESC, region
