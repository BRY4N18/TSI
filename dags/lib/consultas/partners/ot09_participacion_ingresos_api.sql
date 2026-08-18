-- Participación de ingresos por API · OT09
--
-- Reutiliza hecho_factura de Suscripciones. Separa excedente de ingreso base.

SELECT
    toStartOfMonth(f.fecha) AS mes,
    p.nombre_partner AS partner,
    round(sumIf(f.monto_con_signo, f.tipo != 'excedente_api' OR f.tipo IS NULL), 2) AS ingreso_base,
    round(sumIf(f.monto_con_signo, f.tipo = 'excedente_api'), 2) AS excedente,
    round(
        sumIf(f.monto_con_signo, f.tipo = 'excedente_api')
        / nullIf(sum(f.monto_con_signo), 0),
        4
    ) AS pct_excedente
FROM hecho_factura AS f
INNER JOIN dim_partner AS p FINAL ON p.idcliente = f.idcliente
WHERE f.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND p.idpartner != -1
GROUP BY mes, partner
ORDER BY mes, partner
