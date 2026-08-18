-- Clientes con integración API activa · OT10
--
-- ⚠️ Denominador: todos los clientes. Si fueran solo los que tienen partner,
-- el indicador daría siempre 100 %.

SELECT
    toStartOfMonth({desde:Date}) AS periodo,
    count() AS clientes_totales,
    countIf(p.idp > 0) AS con_integracion,
    round(countIf(p.idp > 0) / nullIf(count(), 0), 4) AS pct,
    0.70 AS meta
FROM dim_cliente AS c FINAL
LEFT JOIN (
    SELECT idcliente, min(idpartner) AS idp
    FROM dim_partner FINAL
    WHERE idpartner != -1 AND idcliente IS NOT NULL
    GROUP BY idcliente
) AS p ON p.idcliente = c.idcliente
WHERE c.idcliente != -1
  AND {desde:Date} <= {hasta:Date}
GROUP BY periodo
ORDER BY periodo
