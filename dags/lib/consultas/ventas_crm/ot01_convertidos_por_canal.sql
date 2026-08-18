-- Informe #8 — Clientes convertidos por canal · OT01 · CU-T04
--
-- ⚠️ NO ES EL CAC. NO DEVUELVE NINGUNA COLUMNA DE COSTE, NI VACIA.
-- ---------------------------------------------------------------
-- El catalogo pide un CAC y el sistema no tiene coste por canal. Una columna
-- `coste: null` invitaria a rellenarla desde fuera, y el tablero mostraria un
-- CAC que el sistema no sostiene.
--
-- `nota_indicador` declara que esto es **la parte medible del CAC** y cual falta.

SELECT
    toDate({desde:Date})                         AS periodo,
    p.canal                                      AS canal,
    countIf(p.desenlace = 'convertido')          AS convertidos,
    count()                                      AS prospectos,
    'Parte medible del CAC: clientes convertidos por canal. Falta el coste de adquisicion: el sistema no registra inversion ni gasto por canal.'
                                                 AS nota_indicador
FROM dim_prospecto AS p FINAL
LEFT JOIN (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
) AS v ON v.idprospecto = p.idprospecto
WHERE p.fecha_registro IS NOT NULL
  AND toDate(p.fecha_registro) BETWEEN {desde:Date} AND {hasta:Date}
  AND (
      {idejecutivo:Int32} = -1
      OR v.vigente = {idejecutivo:Int32}
  )
GROUP BY p.canal
ORDER BY convertidos DESC, canal
