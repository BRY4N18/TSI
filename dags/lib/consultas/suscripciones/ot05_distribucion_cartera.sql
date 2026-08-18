-- Informe #11 — Distribución de cartera · OT05
--
-- Un plan de precio cero cuenta en `clientes` y aporta **cero** en `mrr_aportado`.

SELECT
    s.plan,
    s.nivel,
    uniqExact(s.idcliente) AS clientes,
    round(uniqExact(s.idcliente) / sum(uniqExact(s.idcliente)) OVER (), 4) AS pct_clientes,
    round(sumIf(s.precio_mensualizado, s.precio_mensualizado IS NOT NULL), 2) AS mrr_aportado,
    if(sum(sumIf(s.precio_mensualizado, s.precio_mensualizado IS NOT NULL)) OVER () = 0,
        NULL,
        round(
            sumIf(s.precio_mensualizado, s.precio_mensualizado IS NOT NULL)
            / sum(sumIf(s.precio_mensualizado, s.precio_mensualizado IS NOT NULL)) OVER (),
            4
        )
    ) AS pct_ingreso,
    'USD'     AS moneda,
    'mensual' AS periodicidad
FROM hecho_suscripcion AS s FINAL
WHERE s.estado_derivado = 'vigente'
  AND toDate(s.fecha_alta) <= {hasta:Date}
  AND {desde:Date} <= {hasta:Date}
GROUP BY s.plan, s.nivel
ORDER BY clientes DESC, s.plan
