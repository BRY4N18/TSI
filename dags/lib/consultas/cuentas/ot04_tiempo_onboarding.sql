-- Tiempo de onboarding (BSC) · OT04
--
-- Clientes aún en proceso van en en_proceso, fuera de la mediana.

WITH
    por_cliente AS (
        SELECT
            idcliente,
            min(fecha) AS primera,
            max(fecha) AS ultima,
            max(dias_desde_alta) AS dias
        FROM hecho_onboarding
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idcliente
    ),
    estado AS (
        SELECT
            p.idcliente,
            p.dias,
            c.onboarding_completo
        FROM por_cliente AS p
        INNER JOIN dim_cliente AS c FINAL ON c.idcliente = p.idcliente
    )
SELECT
    toStartOfMonth({desde:Date}) AS periodo,
    countIf(onboarding_completo = 1) AS clientes_completados,
    round(medianIf(dias, onboarding_completo = 1), 1) AS dias_mediana,
    countIf(onboarding_completo = 0) AS en_proceso
FROM estado
WHERE {desde:Date} <= {hasta:Date}
GROUP BY periodo
ORDER BY periodo
