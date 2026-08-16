-- Informe #8 — Despachos resueltos al primer intento · OT22 · indicador BSC
--
-- Qué proporción de los casos se resolvió con el **primer** intento de despacho.
-- Meta del cuadro de mando: ≥ 90 %.
--
-- ⚠️ SOLO ES CALCULABLE CON GRANO DE INTENTO
-- ------------------------------------------
-- Con grano de caso este indicador no existe. Un caso que se despachó tres veces
-- —dos rechazos y una confirmación— aparece en las tablas por caso como **un
-- despacho confirmado**: los intentos fallidos no dejan rastro, y el indicador
-- daría 100 % justo cuando el problema es más grave.
--
-- `hecho_despacho` guarda **una fila por intento**, con su ordinal
-- (`numero_intento`) y su desenlace (`resultado`). Eso es lo que hace calculable
-- la pregunta.
--
-- El denominador
-- --------------
-- Son los casos cuyo **primer intento** cae en el período, no todos los intentos.
-- Contar intentos en el denominador castigaría dos veces al mismo caso: un caso
-- con tres intentos aportaría tres fallos y un acierto, cuando lo que se mide es
-- si el caso se resolvió a la primera.
--
-- Un caso cuyo primer intento fue `en_curso` al cerrar el período cuenta en el
-- denominador y no en el numerador. Es correcto: todavía no se ha resuelto al
-- primer intento, y excluirlo mejoraría el indicador por el simple hecho de
-- tener casos sin terminar.

SELECT
    formatDateTime(toStartOfMonth(fecha), '%Y-%m')      AS periodo,
    count()                                             AS casos,
    countIf(resultado = 'confirmado')                   AS resueltos_primer_intento,
    -- ⚠️ Denominador cero es **sin dato**: un mes sin despachos no tiene un 0 %
    -- de resolución al primer intento, no tiene indicador. Un `0` en un cuadro
    -- de mando con meta del 90 % es una alarma roja donde no pasó nada.
    if(
        count() = 0,
        NULL,
        round(countIf(resultado = 'confirmado') / count(), 4)
    )                                                   AS pct_primer_intento,
    0.9                                                 AS meta
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND numero_intento = 1
GROUP BY periodo
ORDER BY periodo
