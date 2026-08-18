-- E4-15 cobertura del histórico por condado. El umbral se publica en cada fila.

SELECT
    coalesce(condado, 'Desconocido') AS condado,
    count() AS casos,
    {umbral_casos:UInt32} AS umbral_casos,
    if(count() < {umbral_casos:UInt32}, 1, 0) AS sin_masa_critica
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY condado
ORDER BY casos DESC
