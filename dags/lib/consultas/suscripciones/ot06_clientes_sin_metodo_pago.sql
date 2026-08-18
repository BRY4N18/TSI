-- Informe #6 — Clientes sin método de pago · OT06
--
-- ⚠️ Diferencia de conjuntos: interesa quien **no tiene** ninguna fila de
-- método. Una unión interna lo perdería — al revés del propósito.
-- ⚠️ El informe pregunta por la ausencia, nunca por el medio.

SELECT
    c.idcliente,
    c.nombre_comercial,
    c.tipo,
    c.estado_comercial,
    if(
        c.metodo_pago_caduca IS NULL,
        NULL,
        dateDiff('day', {hasta:Date}, c.metodo_pago_caduca)
    ) AS caduca_en_dias
FROM dim_cliente AS c FINAL
WHERE c.idcliente != -1
  AND {desde:Date} <= {hasta:Date}
  AND (
        (c.fecha_alta IS NOT NULL AND toDate(c.fecha_alta) <= {hasta:Date})
        OR c.idcliente IN (
            SELECT idcliente
            FROM hecho_suscripcion FINAL
            WHERE toDate(fecha_alta) <= {hasta:Date}
        )
      )
  AND (
        c.idcliente NOT IN (
            SELECT idcliente
            FROM dim_cliente FINAL
            WHERE tiene_metodo_pago = 1
              AND idcliente != -1
        )
        OR (
            c.metodo_pago_caduca IS NOT NULL
            AND dateDiff('day', {hasta:Date}, c.metodo_pago_caduca)
                BETWEEN 0 AND {dias_aviso_caducidad:Int32}
        )
      )
ORDER BY c.idcliente
