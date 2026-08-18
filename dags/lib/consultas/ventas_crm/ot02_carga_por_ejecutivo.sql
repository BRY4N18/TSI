-- Informe #3 — Carga por ejecutivo · OT02 · CU-T03
--
-- ⚠️ ATRIBUYE AL EJECUTIVO VIGENTE EN EL MOMENTO MEDIDO
-- ----------------------------------------------------
-- `activos` y `valor_pipeline` se resuelven al corte `{hasta}`: reasignar
-- despues no reescribe la carga de un periodo anterior. `conversiones` se
-- atribuyen al ejecutivo vigente **en el instante de la conversion**, no al
-- de hoy.
--
-- El ejecutivo se identifica por su clave, no por su nombre. Es el unico
-- informe del departamento que desglosa por persona, y lo hace porque la
-- pregunta *es* la cartera.

WITH vigentes_al_corte AS (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS idejecutivo
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
),
etapa_al_corte AS (
    SELECT
        idprospecto,
        argMax(etapa_nueva, (fechahora, idtransicion)) AS etapa
    FROM hecho_transicion_embudo
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
),
activos AS (
    SELECT
        v.idejecutivo                              AS idejecutivo,
        count()                                    AS activos,
        sum(p.valor_estimado)                      AS valor_pipeline
    FROM dim_prospecto AS p FINAL
    INNER JOIN vigentes_al_corte AS v ON v.idprospecto = p.idprospecto
    LEFT JOIN etapa_al_corte AS e ON e.idprospecto = p.idprospecto
    -- ⚠️ `nullIf(e.etapa, '')`: LEFT JOIN sin coincidencia rellena String con
    -- '' , no NULL. `ifNull` a secas no cae a `etapa_actual` y el prospecto
    -- sin transiciones quedaria con etapa vacia.
    WHERE ifNull(nullIf(e.etapa, ''), p.etapa_actual) NOT IN ('Ganado', 'Perdido')
      AND (
          {idejecutivo:Int32} = -1
          OR v.idejecutivo = {idejecutivo:Int32}
      )
    GROUP BY v.idejecutivo
),
conversiones AS (
    SELECT
        vigente.idejecutivo AS idejecutivo,
        count()             AS conversiones
    FROM (
        SELECT
            t.idtransicion,
            argMax(a.idejecutivo, (a.fechahora, a.idasignacion)) AS idejecutivo
        FROM hecho_transicion_embudo AS t
        INNER JOIN hecho_asignacion_prospecto AS a
            ON a.idprospecto = t.idprospecto
        WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
          AND t.etapa_nueva = 'Ganado'
          -- La desigualdad va en WHERE, no en ON: ClickHouse 24.8 rechaza
          -- `fechahora <=` en el JOIN sin `allow_experimental_join_condition`.
          AND a.fechahora <= t.fechahora
        GROUP BY t.idtransicion
    ) AS vigente
    WHERE {idejecutivo:Int32} = -1
       OR vigente.idejecutivo = {idejecutivo:Int32}
    GROUP BY vigente.idejecutivo
),
ejecutivos AS (
    SELECT idejecutivo FROM activos
    UNION DISTINCT
    SELECT idejecutivo FROM conversiones
)
SELECT
    toDate({desde:Date})                         AS periodo,
    e.idejecutivo                                AS idejecutivo,
    ifNull(act.activos, 0)                       AS activos,
    ifNull(act.valor_pipeline, 0)                AS valor_pipeline,
    ifNull(conv.conversiones, 0)                 AS conversiones
FROM ejecutivos AS e
LEFT JOIN activos AS act ON act.idejecutivo = e.idejecutivo
LEFT JOIN conversiones AS conv ON conv.idejecutivo = e.idejecutivo
ORDER BY activos DESC, idejecutivo
