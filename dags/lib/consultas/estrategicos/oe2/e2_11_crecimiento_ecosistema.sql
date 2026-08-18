-- E2-11 Crecimiento: primera llamada 2xx, no alta de credencial.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(primera_exito),
            {granularidad:String} = 'trimestre', toStartOfQuarter(primera_exito),
            toStartOfYear(primera_exito)
        ),
        '%Y-%m'
    ) AS periodo,
    count() AS partners_nuevos
FROM (
    SELECT
        idpartner,
        min(fecha) AS primera_exito
    FROM hecho_llamada_api
    WHERE codigo_http >= 200
      AND codigo_http < 300
      AND idpartner != -1
    GROUP BY idpartner
) AS primeras
WHERE primera_exito BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo
ORDER BY periodo
