-- Informe — Mercados activos · OT11
--
-- Cuántas regiones hay en cada estado del ciclo de vida.
--
-- ⚠️ EL ESTADO ES EL DEL CICLO DE VIDA, NO LA GEOGRAFÍA
-- ------------------------------------------------------
-- El origen confunde las dos: `Dim_RegionOperativa.estadoregion` vale
-- «Producción» —el ciclo de vida— y `Dim_EstadoRegion.estadoregion` vale «Ciudad
-- de Mexico» —geografía—, con el mismo nombre de columna. Y
-- `Dim_RegionOperativaEstadoRegion`, que el catálogo de informes citaba como
-- fuente del primero, relaciona con **el segundo**.
--
-- La carga las separa en `estado_ciclo_vida` y `estado_geo`. Leer la equivocada
-- aquí devolvería todas las regiones bajo «Ciudad de Mexico» o ninguna bajo
-- «Producción», y **las dos respuestas parecen plausibles**: con dos regiones,
-- «2 de 2» y «0 de 2» son cifras que nadie cuestiona sin conocer el dato.
--
-- ⚠️ Se lee la versión **vigente al final del período**, no la de hoy
-- -------------------------------------------------------------------
-- `dim_region` está versionada. Despublicar una región mañana no debe reescribir
-- el recuento de mercados activos de este mes: el informe de marzo consultado en
-- agosto tiene que seguir diciendo lo que decía en marzo.
--
-- Las regiones se cuentan aunque no tengan condados asignados. Hoy es el caso de
-- todas —ver la decisión #38, no existe relación región↔condado— y excluirlas
-- dejaría el informe vacío por un hueco del origen que no tiene que ver con si el
-- mercado está activo.

SELECT
    toDate({hasta:Date})                                    AS corte,
    estado_ciclo_vida                                       AS estado_ciclo_vida,
    count()                                                 AS regiones,
    round(count() / sum(count()) OVER (), 4)                AS pct,
    -- Publicar los nombres hace el informe accionable: «3 en validación» no dice
    -- cuáles hay que empujar.
    -- ⚠️ Se llama `regiones_incluidas` y no `nombres`. La comprobación de dato
    -- sensible caza cualquier columna con «nombres» y **hace bien en dudar**: una
    -- columna llamada asi es ambigua tambien para quien lee el informe, que no
    -- sabe si son nombres de regiones o de personas. El arreglo es el nombre, no
    -- una excepcion en la comprobacion.
    arraySort(groupArray(nombre_region))                    AS regiones_incluidas
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
)
GROUP BY estado_ciclo_vida
ORDER BY regiones DESC, estado_ciclo_vida
