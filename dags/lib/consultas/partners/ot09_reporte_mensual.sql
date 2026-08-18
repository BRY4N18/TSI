-- Reporte mensual de consumo · OT09

SELECT
    toStartOfMonth(fecha) AS mes,
    partner,
    count() AS llamadas,
    countIf(clase_resultado != 'exito') AS errores,
    countIf(clase_resultado = 'limite_cupo') AS excedente,
    count() AS muestras
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({mes:String} = '' OR formatDateTime(toStartOfMonth(fecha), '%Y-%m') = {mes:String})
GROUP BY mes, partner
ORDER BY mes, partner
