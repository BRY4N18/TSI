-- Informe #4 — Descarte y fusión de reportes · OT21 · origen: OP33
--
-- ⚠️ Descartado, fusionado y cerrado son TRES COSAS DISTINTAS
-- -----------------------------------------------------------
-- El sistema operativo marca los tres igual: `activo = false`. Confundirlos
-- falsea a la vez el volumen y la calidad del registro — un recuento de «casos
-- inactivos» sumaría emergencias atendidas, falsas alarmas y duplicados como si
-- fueran lo mismo, presentando el trabajo hecho y el ruido descartado juntos.
--
-- El modelo los separó al cargar, en dos columnas propias: `fue_descartado` y
-- `es_duplicado`. Por eso aquí distinguirlos es contar, no inferir.
--
-- Los porcentajes van sobre el total de casos del período, que es la pregunta
-- real: qué proporción del registro fue ruido.

SELECT
    toDate({desde:Date})                     AS periodo,
    count()                                  AS casos,
    countIf(fue_descartado = 1)              AS descartados,
    countIf(es_duplicado = 1)                AS fusionados,
    -- Denominador cero es sin dato, no cero.
    if(count() = 0, NULL, round(countIf(fue_descartado = 1) / count(), 4)) AS pct_descarte,
    if(count() = 0, NULL, round(countIf(es_duplicado = 1) / count(), 4))   AS pct_fusion
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo
