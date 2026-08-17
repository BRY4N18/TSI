-- Informe — Tasa de aprobación al primer intento · OT11 · indicador BSC
--
-- Qué proporción de las regiones se aprobó sin tener que volver a intentarlo.
--
-- ⚠️ SE CUENTAN INTENTOS, NO REGIONES (FR-017)
-- --------------------------------------------
-- Una región rechazada dos veces y aprobada a la tercera **no se aprobó al
-- primer intento**. Con grano de región solo queda la aprobación final, los dos
-- rechazos no dejan rastro, y el indicador daría 100 % justo en el caso que peor
-- fue.
--
-- Es exactamente el caso que hay en los datos hoy: «Region Prueba Norte» tiene
-- rechazo, rechazo y aprobación. El indicador correcto es 0 %, no 100 %.
--
-- `numero_intento` viene calculado en la carga, ordenando las validaciones de
-- cada región por su instante. Sin esa columna esta pregunta no es formulable.
--
-- ⚠️ POR REGIÓN, NO POR VALIDADOR
-- -------------------------------
-- El hecho **no guarda quién validó**, y es deliberado: un desglose por persona
-- juzgaría a alguien por resultados que dependen de las regiones que le tocaron.
-- La pregunta útil —qué proporción sale bien a la primera— no necesita saberlo.
--
-- El denominador son las regiones con **primer intento en el período**, no todos
-- los intentos: contar intentos en el denominador castigaría dos veces a la
-- misma región, que aportaría un fallo por cada reintento.
--
-- Una región **sin validaciones no aparece** y no cuenta como 0 %: no ha
-- intentado nada, así que no ha fallado.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m')          AS periodo,
    count()                                                 AS regiones_validadas,
    countIf(resultado = 'Aprobada')                         AS aprobadas_al_primero,
    -- ⚠️ Denominador cero es **sin dato**: un mes sin validaciones no tiene una
    -- tasa del 0 %, no tiene tasa. Un `0` en un tablero con meta es una alarma
    -- roja donde no pasó nada.
    if(
        count() = 0,
        NULL,
        round(countIf(resultado = 'Aprobada') / count(), 4)
    )                                                       AS pct_aprobacion_primer_intento
FROM hecho_validacion_region
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND numero_intento = 1
GROUP BY periodo
ORDER BY periodo
