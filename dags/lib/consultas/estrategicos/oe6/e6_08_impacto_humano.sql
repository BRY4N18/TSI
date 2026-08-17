-- Informe E6-08 — Impacto humano agregado
-- Parte de ot21_impacto_humano. Añade granularidad y severidad.
--
-- ⛔ Recuentos, nunca identidad. El modelo guarda los números, no las personas.
--
-- ⚠️ DISTINGUE «CERO» DE «NO REGISTRADO»
-- Un accidente con cero heridos es una buena noticia; uno cuyos heridos nadie
-- contó es un expediente incompleto. Sumar los segundos como ceros haría BAJAR
-- el impacto humano total cada vez que empeora la calidad del registro.
-- `casos_con_dato` publica el denominador real. Las sumas no usan coalesce a 0:
-- un NULL no aporta, y eso es correcto; lo que no se hace es contarlo como caso
-- con dato.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    coalesce(severidad, 'Desconocido')                          AS severidad,
    if({por_condado:UInt8} = 1, coalesce(condado, 'Desconocido'), '') AS condado,
    count()                                                     AS casos,
    countIf(
        num_heridos IS NOT NULL
        OR num_victimas IS NOT NULL
        OR num_fallecidos IS NOT NULL
    )                                                           AS casos_con_dato,
    sum(num_victimas)                                           AS victimas,
    sum(num_heridos)                                            AS heridos,
    sum(num_fallecidos)                                         AS fallecidos
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0
  AND es_duplicado = 0
GROUP BY periodo, severidad, condado
ORDER BY periodo, fallecidos DESC, victimas DESC, heridos DESC, severidad, condado
