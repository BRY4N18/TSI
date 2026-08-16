-- Informe #9 — Asignación automática frente a manual · OT22
-- Solo para contraste: el endpoint que lo sirve hoy es correcto y no se migra.
--
-- Qué proporción de los despachos salió del asignador automático y cuánta hizo
-- falta decidir a mano.
--
-- `Escalado_zona` es un origen propio y **no** se suma a ninguno de los otros
-- dos: un escalado es el sistema pidiendo ayuda fuera de la zona, que no es lo
-- mismo que una asignación automática que funcionó ni que una decisión humana.
-- Repartirlo entre los dos borraría la única señal de que la cobertura local no
-- daba abasto.

SELECT
    toDate({desde:Date})                        AS periodo,
    origen_despacho                             AS origen,
    count()                                     AS despachos,
    round(count() / sum(count()) OVER (), 4)    AS pct
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY origen_despacho
ORDER BY despachos DESC, origen
