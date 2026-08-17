-- Informe — Tiempo desde la pérdida de cobertura hasta la despublicación · OT13
--
-- Cuánto tarda una región en retirarse una vez que deja de tener flota.
--
-- ⚠️ UNA REGIÓN SIN DESPUBLICAR NO CUENTA COMO DESPUBLICADA EN CERO DÍAS (FR-035)
-- ------------------------------------------------------------------------------
-- No aparece en el cálculo. Un `0` diría que se retiró **inmediatamente**, que es
-- la mejor marca posible, y la pondría a la cabeza de la lista de reacciones más
-- rápidas — justo la región que sigue publicada sin cobertura, que es el caso que
-- este informe existe para encontrar.
--
-- Aparece en `aun_publicadas_sin_flota`, que es un recuento aparte y una alarma
-- distinta: aquélla mide reacción, ésta mide inacción.
--
-- ⚠️ LA MEDIDA SOLO ES EXACTA DESDE QUE EL MODELO VERSIONA (FR-034)
-- ------------------------------------------------------------------
-- El origen **no historiza el cambio de estado de una región**: guarda el
-- presente y lo sobrescribe. La primera versión de cada región abre por la
-- izquierda con `inicio_es_real = 0`, así que una despublicación anterior a la
-- primera carga **no dejó rastro**.
--
-- Eso significa que un histórico vacío aquí **no quiere decir «nunca pasó»**:
-- quiere decir «no lo vimos». Las dos se leen igual en una pantalla, y la
-- primera es tranquilizadora. Por eso el endpoint publica `medida_exacta_desde`
-- junto a la cifra, y por eso esta consulta devuelve `despublicaciones_medidas`
-- aunque valga cero: sin ese contexto, «0 días de media» sería un elogio.
--
-- Solo cuentan las versiones con `inicio_es_real = 1`: las que abren por la
-- izquierda no dicen cuándo se despublicó la región, dicen que ya lo estaba.

SELECT
    toDate({hasta:Date})                                        AS corte,
    countIf(despublicada_en IS NOT NULL)                        AS despublicaciones_medidas,
    -- La otra cara, y la alarma de verdad: sin flota y todavía publicadas.
    countIf(despublicada_en IS NULL AND unidades = 0)           AS aun_publicadas_sin_flota,
    count()                                                     AS regiones,
    round(medianIf(dias_hasta_despublicar, despublicada_en IS NOT NULL))
                                                                AS mediana_dias,
    maxIf(dias_hasta_despublicar, despublicada_en IS NOT NULL)  AS maximo_dias
FROM (
    SELECT
        r.idregionoperativa                     AS idregionoperativa,
        r.despublicada_en                       AS despublicada_en,
        coalesce(u.unidades, 0)                 AS unidades,
        -- Ausente mientras no se haya despublicado. Ver la nota de arriba: un
        -- cero seria la mejor marca posible para la peor situacion.
        if(
            r.despublicada_en IS NULL,
            NULL,
            dateDiff('day', r.publicada_en, r.despublicada_en)
        )                                       AS dias_hasta_despublicar
    FROM (
        SELECT
            idregionoperativa                                       AS idregionoperativa,
            nullIf(minIf(valido_desde, estado_ciclo_vida = 'Producción'),
                   toDateTime(0))                                   AS publicada_en,
            -- ⚠️ Solo `inicio_es_real = 1`: una version que abre por la
            -- izquierda no fecha la despublicacion, solo dice que ya estaba
            -- despublicada cuando el modelo empezo a mirar. `nullIf` porque
            -- `minIf` sin filas que cumplan devuelve la epoca cero, no NULL.
            nullIf(minIf(valido_desde,
                         estado_ciclo_vida = 'Despublicada' AND inicio_es_real = 1),
                   toDateTime(0))                                   AS despublicada_en
        FROM dim_region FINAL
        WHERE idregionoperativa != -1 AND valido_desde <= toDateTime({hasta:Date})
        GROUP BY idregionoperativa
    ) AS r
    LEFT JOIN (
        SELECT
            g.idregionoperativa                                             AS idregionoperativa,
            uniqExactIf(un.idunidademergencia, un.idunidademergencia != 0)  AS unidades
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
)
ORDER BY corte
