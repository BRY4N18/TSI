-- Informe #14 — Carga por unidad · OT22
-- Solo para contraste: el endpoint que lo sirve hoy es correcto y no se migra.
--
-- Cuánto trabajo asumió cada unidad en el período.
--
-- Se cuentan **intentos** y **casos atendidos** por separado. No son lo mismo:
-- una unidad a la que se le ofrecieron cuarenta despachos y aceptó cinco tiene
-- mucha carga de ofertas y poca de trabajo, y las dos cifras juntas son lo que
-- distingue una unidad saturada de una que rechaza.

SELECT
    toDate({desde:Date})                            AS periodo,
    unidad                                          AS unidad,
    proveedor                                       AS proveedor,
    count()                                         AS intentos_recibidos,
    countIf(resultado = 'confirmado')               AS casos_atendidos,
    countIf(hora_llegada IS NOT NULL)               AS llegadas,
    round(median(segundos_transito))                AS mediana_llegada_seg
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY unidad, proveedor
ORDER BY casos_atendidos DESC, unidad
