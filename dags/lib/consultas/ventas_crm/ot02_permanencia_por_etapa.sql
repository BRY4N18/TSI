-- Informe #2 — Permanencia por etapa · OT02 · CU-T03
--
-- ⚠️ INCLUYE EL TRAMO ABIERTO
-- ---------------------------
-- La etapa vigente al final del periodo cuenta **hasta el fin del periodo**,
-- y esos prospectos se informan en `abiertos`. Sin eso, los estancados —los
-- que el informe existe para encontrar— no aparecerian, y quien lleva semanas
-- sin moverse se veria como el mas rapido (no hay transicion que cierre su
-- tramo, asi que no habria duracion).
--
-- El tramo abierto se mide desde que entro a la etapa (ultima transicion, o
-- `fecha_registro` si no hay ninguna), no recortado a `{desde}`: un estancado
-- de tres semanas tiene que mostrar tres semanas.

WITH vigentes AS (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
),
visibles AS (
    SELECT
        p.idprospecto,
        p.etapa_actual,
        p.fecha_registro
    FROM dim_prospecto AS p FINAL
    LEFT JOIN vigentes AS v ON v.idprospecto = p.idprospecto
    WHERE p.fecha_registro IS NOT NULL
      AND toDate(p.fecha_registro) <= {hasta:Date}
      AND (
          {idejecutivo:Int32} = -1
          OR v.vigente = {idejecutivo:Int32}
      )
),
ultima AS (
    SELECT
        idprospecto,
        argMax(etapa_nueva, (fechahora, idtransicion)) AS etapa_en_corte,
        max(fechahora) AS fechahora_ultima
    FROM hecho_transicion_embudo
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
),
tramos AS (
    SELECT
        t.etapa_anterior AS etapa,
        t.segundos_en_etapa_anterior AS segundos,
        t.idprospecto AS idprospecto,
        0 AS abierto
    FROM hecho_transicion_embudo AS t
    INNER JOIN visibles AS vis ON vis.idprospecto = t.idprospecto
    WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND t.segundos_en_etapa_anterior IS NOT NULL
      AND t.etapa_anterior IS NOT NULL
      AND t.etapa_anterior != ''

    UNION ALL

    SELECT
        etapa,
        segundos,
        idprospecto,
        1 AS abierto
    FROM (
        SELECT
            -- ⚠️ LEFT JOIN sin coincidencia rellena String con '' y DateTime
            -- con la epoca cero, no con NULL. `ifNull` a secas no cae a
            -- `etapa_actual` / `fecha_registro`, el estancado sin transiciones
            -- queda fuera del tramo abierto —justo a quien el informe existe
            -- para encontrar— y quien lleva semanas sin moverse desaparece.
            ifNull(nullIf(u.etapa_en_corte, ''), vis.etapa_actual) AS etapa,
            dateDiff(
                'second',
                ifNull(
                    nullIf(u.fechahora_ultima, toDateTime(0)),
                    vis.fecha_registro
                ),
                toDateTime({hasta:Date}) + INTERVAL 1 DAY - INTERVAL 1 SECOND
            ) AS segundos,
            vis.idprospecto AS idprospecto
        FROM visibles AS vis
        LEFT JOIN ultima AS u ON u.idprospecto = vis.idprospecto
    ) AS abierto_calc
    WHERE etapa NOT IN ('Ganado', 'Perdido')
      AND etapa IS NOT NULL
      AND etapa != ''
)
SELECT
    toDate({desde:Date})                         AS periodo,
    etapa                                        AS etapa,
    uniqExact(idprospecto)                       AS prospectos_medidos,
    round(median(segundos))                      AS segundos_mediana,
    uniqExactIf(idprospecto, abierto = 1)        AS abiertos
FROM tramos
WHERE etapa IS NOT NULL AND etapa != ''
GROUP BY etapa
ORDER BY segundos_mediana DESC, etapa
