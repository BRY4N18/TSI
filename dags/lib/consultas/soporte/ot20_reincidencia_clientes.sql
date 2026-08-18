-- C9 · Reincidencia de clientes · OT20
--
-- ⚠️ Clave del cliente, jamás nombre.
-- ⚠️ El eje natural sería el servicio y hoy no existe: se agrupa por tipo
-- de incidencia (o tipo de ticket) y la respuesta lo declara.

SELECT
    t.idcliente AS id_cliente,
    c.tipo AS tipo_cliente,
    count() AS tickets,
    uniqExact(
        multiIf(
            {eje:String} = 'tipo', t.tipo,
            t.tipo_incidencia
        )
    ) AS tipos_distintos,
    countIf(t.fue_reabierto = 1) AS reaperturas
FROM hecho_ticket AS t FINAL
LEFT JOIN (SELECT idcliente, tipo FROM dim_cliente FINAL) AS c
       ON t.idcliente = c.idcliente
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({idagente:Int32} = -1 OR t.idagente = {idagente:Int32})
GROUP BY t.idcliente, c.tipo
HAVING tickets >= {minimo:UInt32}
ORDER BY tickets DESC, id_cliente
