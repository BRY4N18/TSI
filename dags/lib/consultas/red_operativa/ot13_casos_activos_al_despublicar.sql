-- Informe — Casos activos al despublicar una región · OT13
--
-- Cuántos casos seguían abiertos cuando su región se retiró.
--
-- Es la medida de si la retirada fue ordenada. Despublicar una región con casos
-- en curso deja gente esperando a una unidad que ya no se va a despachar.
--
-- ⚠️ LA MEDIDA SOLO ES EXACTA DESDE QUE EL MODELO VERSIONA (FR-034)
-- ------------------------------------------------------------------
-- El origen **no historiza el cambio de estado de una región**. Una
-- despublicación anterior a la primera carga del modelo no dejó rastro, así que
-- un resultado vacío aquí **no significa «nunca pasó»**: significa «no lo
-- vimos».
--
-- Las dos se leen igual en una pantalla, y la primera es tranquilizadora — que es
-- exactamente por lo que hace falta decirlo. El endpoint publica
-- `medida_exacta_desde` junto a la cifra, y esta consulta devuelve
-- `despublicaciones_observadas` aunque valga cero: sin ese contexto, una tabla
-- vacía pasaría por un historial impecable.
--
-- Hoy no hay ninguna despublicación registrada, así que el informe sale vacío. Es
-- correcto y está declarado.
--
-- Solo cuentan las versiones con `inicio_es_real = 1`: las que abren por la
-- izquierda no fechan la despublicación, solo dicen que ya estaba despublicada
-- cuando el modelo empezó a mirar, y restar contra esa fecha daría cincuenta y
-- seis años de casos acumulados.

SELECT
    r.idregionoperativa                                     AS idregion,
    r.nombre_region                                         AS region,
    r.despublicada_en                                       AS despublicada_en,
    coalesce(a.casos_activos, 0)                            AS casos_activos,
    coalesce(a.casos_graves, 0)                             AS casos_graves
FROM (
    SELECT
        idregionoperativa                                           AS idregionoperativa,
        any(nombre_region)                                          AS nombre_region,
        nullIf(minIf(valido_desde,
                     estado_ciclo_vida = 'Despublicada' AND inicio_es_real = 1),
               toDateTime(0))                                       AS despublicada_en
    FROM dim_region FINAL
    WHERE idregionoperativa != -1 AND valido_desde <= toDateTime({hasta:Date})
    GROUP BY idregionoperativa
) AS r
LEFT JOIN (
    SELECT
        g.idregionoperativa                                 AS idregionoperativa,
        countIf(a.hora_cierre IS NULL)                      AS casos_activos,
        countIf(a.hora_cierre IS NULL
                AND a.severidad IN ('Grave', 'Fatal'))      AS casos_graves
    FROM (
        SELECT idcondado, condado, any(idregionoperativa) AS idregionoperativa
        FROM dim_geografia FINAL
        WHERE idcondado != -1
        GROUP BY idcondado, condado
    ) AS g
    LEFT JOIN (
        SELECT condado, hora_cierre, severidad
        FROM hecho_accidente FINAL
        WHERE fue_descartado = 0 AND es_duplicado = 0
    ) AS a ON a.condado = g.condado
    GROUP BY g.idregionoperativa
) AS a ON a.idregionoperativa = r.idregionoperativa
-- Solo las despublicadas de forma observada: el informe habla de retiradas, no
-- de regiones vivas.
WHERE r.despublicada_en IS NOT NULL
ORDER BY casos_activos DESC, region
