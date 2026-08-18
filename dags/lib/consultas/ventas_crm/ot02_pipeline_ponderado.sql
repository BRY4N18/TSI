-- Informe #4 — Pipeline ponderado por etapa · OT02 · CU-T03
--
-- ⚠️ `pesos_etapa` ES UNA CONVENCION DEL INFORME, NO UNA POLITICA
-- --------------------------------------------------------------
-- El sistema operativo no define ninguna ponderacion. Los pesos van
-- hardcodeados y se declaran en `meta.filtros` para que la cifra sea
-- auditable: «valor ponderado del pipeline» suena a cifra corporativa y no lo es.
--
-- Default: Nuevo=0.1, Contactado=0.2, Calificado=0.4, Propuesta=0.6,
-- Negociación=0.8. Ganado y Perdido no entran: ya no son pipeline.

WITH vigentes AS (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
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
abiertos AS (
    SELECT
        -- ⚠️ `nullIf(e.etapa, '')`: LEFT JOIN sin coincidencia rellena String
        -- con '', no NULL. Sin esto, el prospecto sin transiciones queda fuera
        -- del pipeline (`!= ''`) aunque siga abierto en `etapa_actual`.
        ifNull(nullIf(e.etapa, ''), p.etapa_actual) AS etapa,
        p.valor_estimado                            AS valor_estimado
    FROM dim_prospecto AS p FINAL
    LEFT JOIN vigentes AS v ON v.idprospecto = p.idprospecto
    LEFT JOIN etapa_al_corte AS e ON e.idprospecto = p.idprospecto
    WHERE p.fecha_registro IS NOT NULL
      AND toDate(p.fecha_registro) <= {hasta:Date}
      AND ifNull(nullIf(e.etapa, ''), p.etapa_actual) NOT IN ('Ganado', 'Perdido')
      AND ifNull(nullIf(e.etapa, ''), p.etapa_actual) IS NOT NULL
      AND ifNull(nullIf(e.etapa, ''), p.etapa_actual) != ''
      AND (
          {idejecutivo:Int32} = -1
          OR v.vigente = {idejecutivo:Int32}
      )
)
SELECT
    toDate({desde:Date})                         AS periodo,
    etapa                                        AS etapa,
    count()                                      AS prospectos,
    sum(valor_estimado)                          AS valor_bruto,
    multiIf(
        etapa = 'Nuevo', 0.1,
        etapa = 'Contactado', 0.2,
        etapa = 'Calificado', 0.4,
        etapa = 'Propuesta', 0.6,
        etapa IN ('Negociación', 'Negociacion'), 0.8,
        0
    )                                            AS peso,
    round(
        sum(valor_estimado) * multiIf(
            etapa = 'Nuevo', 0.1,
            etapa = 'Contactado', 0.2,
            etapa = 'Calificado', 0.4,
            etapa = 'Propuesta', 0.6,
            etapa IN ('Negociación', 'Negociacion'), 0.8,
            0
        ),
        2
    )                                            AS valor_ponderado
FROM abiertos
GROUP BY etapa
ORDER BY peso, etapa
