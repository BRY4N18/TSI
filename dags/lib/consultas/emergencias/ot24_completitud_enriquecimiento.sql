-- Informe #19 — Completitud del enriquecimiento · OT24 · indicador BSC
--
-- Qué proporción de los casos llegó con su contexto documentado: quiénes
-- estaban implicados, en qué condiciones y con qué notas.
--
-- ⚠️ CERO ES UNA MEDICIÓN; AUSENTE NO
-- -----------------------------------
-- `num_notas = 0` significa que el caso existe y **no tiene ninguna nota**: es
-- justo lo que este informe busca contar. `num_notas IS NULL` significa otra
-- cosa distinta —la fila se cargó antes de que la métrica existiera— y esos
-- casos no se pueden juzgar.
--
-- Se cuentan aparte en `sin_medir` y **salen del denominador**. Meterlos como
-- incompletos hundiría un indicador con meta usando casos que nadie midió;
-- meterlos como completos lo inflaría igual de mal. La única lectura honesta es
-- decir cuántos hay y no juzgarlos.
--
-- Un caso está enriquecido si tiene **al menos una** de las tres cosas
-- ---------------------------------------------------------------------
-- No se exigen las tres porque no todas aplican siempre: un choque sin heridos
-- no tiene implicados que registrar, y exigírselo penalizaría a quien documentó
-- bien lo que había. Las tres se publican por separado además del agregado, para
-- que se vea cuál falta.

SELECT
    toDate({desde:Date})                                            AS periodo,
    count()                                                         AS casos,
    countIf(num_notas IS NULL)                                      AS sin_medir,
    countIf(num_notas IS NOT NULL)                                  AS medidos,
    countIf(num_notas > 0)                                          AS con_notas,
    countIf(num_implicados > 0)                                     AS con_implicados,
    countIf(num_elementos_clima > 0)                                AS con_clima,
    countIf(
        num_notas > 0 OR num_implicados > 0 OR num_elementos_clima > 0
    )                                                               AS enriquecidos,
    if(
        countIf(num_notas IS NOT NULL) = 0,
        NULL,
        round(
            countIf(num_notas > 0 OR num_implicados > 0 OR num_elementos_clima > 0)
            / countIf(num_notas IS NOT NULL),
            4
        )
    )                                                               AS pct_enriquecidos
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo
