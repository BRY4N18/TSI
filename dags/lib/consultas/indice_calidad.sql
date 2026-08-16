-- Índice de calidad del dato, calculado **desde el modelo** (T045).
--
-- Sustituye a la tabla `indice_calidad_historico` y a su flujo propio.
--
-- ⚠️ CORRIGE UN DEFECTO, y por eso sus cifras **deben** diferir
-- --------------------------------------------------------------
-- El flujo anterior medía la completitud así:
--
--     SUM(CASE WHEN idseveridad IS NOT NULL AND idcalle IS NOT NULL THEN 1 ELSE 0 END)
--
-- contra el origen. Pero **el origen no tiene nulos**: usa valores centinela.
-- La condición era por tanto siempre cierta y `pct_completitud` salía
-- exactamente `1.0000` los 182 días medidos — no porque el dato estuviera
-- completo, sino porque la pregunta no podía dar otra respuesta.
--
-- En el modelo la ausencia **sí es ausencia**: la conversión desde el origen
-- traduce los centinelas a nulo al cargar. La misma condición, escrita aquí,
-- mide lo que decía medir.
--
-- **Que la cifra baje es el arreglo, no un error de migración.**
--
-- Otra diferencia esperada: el reparto por día
-- --------------------------------------------
-- El flujo viejo contaba descartes y fusiones por la **fecha del cambio de
-- estado**, y los dividía entre el total de casos por **fecha del accidente**:
-- dos ejes distintos en la misma fracción, de modo que un caso descartado en
-- otro día contaminaba el porcentaje de ese día. Aquí ambos van por la fecha del
-- caso, que es el eje del hecho.

SELECT
    fecha                                                        AS periodo,
    round(countIf(idseveridad IS NOT NULL AND idcalle IS NOT NULL) / count(), 4)
                                                                 AS pct_completitud,
    round(countIf(fue_descartado = 1) / count(), 4)               AS pct_descarte,
    round(countIf(es_duplicado = 1) / count(), 4)                 AS pct_fusion,
    round(
        if(
            countIf(hora_cierre IS NOT NULL) = 0,
            1,
            countIf(hora_cierre IS NOT NULL AND num_evidencias > 0)
                / countIf(hora_cierre IS NOT NULL)
        ),
        4
    )                                                            AS pct_cobertura_evidencia,
    round(
        (
            countIf(idseveridad IS NOT NULL AND idcalle IS NOT NULL) / count()
            + (1 - countIf(fue_descartado = 1) / count())
            + (1 - countIf(es_duplicado = 1) / count())
            + if(
                countIf(hora_cierre IS NOT NULL) = 0,
                1,
                countIf(hora_cierre IS NOT NULL AND num_evidencias > 0)
                    / countIf(hora_cierre IS NOT NULL)
              )
        ) / 4,
        4
    )                                                            AS indice_consolidado
FROM hecho_accidente FINAL
GROUP BY fecha
ORDER BY periodo
