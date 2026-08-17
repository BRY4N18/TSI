-- Informe — Tiempo de puesta en operación de una región · OT11
--
-- Cuánto tarda una región desde su primera validación hasta entrar en producción.
--
-- ⚠️ UNA REGIÓN QUE NO LLEGÓ A PRODUCCIÓN DEVUELVE AUSENTE, NUNCA CERO
-- --------------------------------------------------------------------
-- Ni `dias = 0` ni `cumple_objetivo = false`. **No incumplió un plazo: todavía
-- está dentro de él.** Son cosas distintas y la diferencia decide qué se hace:
-- una región que incumplió necesita explicación, una que está en curso necesita
-- tiempo.
--
-- Un `0` además la pondría a la cabeza de la lista de las más rápidas, que es el
-- orden por el que alguien buscaría buenas prácticas.
--
-- ⚠️ `dias_objetivo` es UNA CONVENCIÓN DEL INFORME, NO UN COMPROMISO
-- -------------------------------------------------------------------
-- El sistema **no guarda ningún plazo** para poner una región en operación. El
-- que se aplique aquí lo pone quien consulta, y por eso viaja como parámetro y se
-- devuelve en la respuesta: sin verlo, «3 regiones fuera de objetivo» pasaría por
-- un incumplimiento de un acuerdo que nadie firmó.
--
-- ⚠️ La medida solo es exacta desde que el modelo versiona
-- --------------------------------------------------------
-- El origen no historiza el cambio de estado de una región: guarda el presente y
-- lo sobrescribe. La primera versión de cada región abre por la izquierda con
-- `inicio_es_real = 0`, así que para las regiones ya en producción antes de la
-- primera carga **no se sabe cuándo entraron**. El endpoint publica
-- `medida_exacta_desde` por esto.
--
-- Aquí eso se traduce en que el inicio se toma de la **primera validación**, que
-- sí tiene instante propio, y no del estado de la región.

SELECT
    r.idregionoperativa                                     AS idregion,
    r.nombre_region                                         AS region,
    r.estado_ciclo_vida                                     AS estado_actual,
    {dias_objetivo:UInt32}                                  AS dias_objetivo,
    -- ⚠️ `nullIf(..., toDateTime(0))` en las dos fechas. Un LEFT JOIN sin
    -- coincidencia y un `minIf` sin filas que cumplan devuelven **el valor por
    -- defecto del tipo** —la época cero—, no `NULL`.
    --
    -- Sin esto, una región sin validaciones salía con primera validación en 1970
    -- y una región sin versión de inicio real daba **-20 677 días**. Un número
    -- negativo se ve; el problema es que la misma causa produce también números
    -- positivos plausibles en cuanto las fechas caen del otro lado.
    --
    -- Es la cuarta vez que este relleno muerde en el proyecto.
    nullIf(v.primera_validacion, toDateTime(0))             AS primera_validacion,
    nullIf(r.entro_en_produccion, toDateTime(0))            AS entro_en_produccion,
    -- Ausente si no está en producción **o si no se sabe cuándo entró**. Las dos
    -- son «no se puede medir», y ninguna es un incumplimiento.
    if(
        r.estado_ciclo_vida = 'Producción'
            AND nullIf(v.primera_validacion, toDateTime(0)) IS NOT NULL
            AND nullIf(r.entro_en_produccion, toDateTime(0)) IS NOT NULL,
        dateDiff('day', v.primera_validacion, r.entro_en_produccion),
        NULL
    )                                                       AS dias,
    if(
        r.estado_ciclo_vida = 'Producción'
            AND nullIf(v.primera_validacion, toDateTime(0)) IS NOT NULL
            AND nullIf(r.entro_en_produccion, toDateTime(0)) IS NOT NULL,
        dateDiff('day', v.primera_validacion, r.entro_en_produccion)
            <= {dias_objetivo:UInt32},
        NULL
    )                                                       AS cumple_objetivo
FROM (
    SELECT
        idregionoperativa                       AS idregionoperativa,
        any(nombre_region)                      AS nombre_region,
        any(estado_ciclo_vida)                  AS estado_ciclo_vida,
        -- ⚠️ `inicio_es_real = 1` solo: la versión que abre por la izquierda no
        -- dice cuándo entró en producción, dice que ya lo estaba cuando el
        -- modelo empezó a mirar. Usarla daría una antigüedad de cincuenta y seis
        -- años.
        minIf(valido_desde, inicio_es_real = 1)  AS entro_en_produccion
    FROM dim_region FINAL
    WHERE es_vigente = 1 AND idregionoperativa != -1
    GROUP BY idregionoperativa
) AS r
LEFT JOIN (
    SELECT idregionoperativa, min(fechahora) AS primera_validacion
    FROM hecho_validacion_region
    WHERE fecha <= {hasta:Date}
    GROUP BY idregionoperativa
) AS v ON v.idregionoperativa = r.idregionoperativa
ORDER BY dias DESC NULLS LAST, region
