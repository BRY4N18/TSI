-- Informe #9 — Intensidad de uso de la demo · OT03
--
-- Grano: prospecto × periodo. Sin eventos en el periodo, cero filas — no una
-- fila de ceros. Cero filas es «no hubo demos»; filas con secciones en cero
-- es «hubo demo y no se uso». Son conclusiones opuestas sobre el producto.
--
-- `idprospecto` es la clave del grano, no identidad de persona: no viaja
-- nombre, correo ni telefono. `empresa` es unidad de negocio.

SELECT
    toDate({desde:Date})                         AS periodo,
    d.idprospecto                                AS idprospecto,
    d.empresa                                    AS empresa,
    count()                                      AS eventos,
    uniqExact(d.seccion)                         AS secciones_distintas
FROM hecho_interaccion_demo AS d
WHERE d.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND (
      {idejecutivo:Int32} = -1
      OR d.idprospecto IN (
          SELECT idprospecto
          FROM (
              SELECT
                  idprospecto,
                  argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
              FROM hecho_asignacion_prospecto
              WHERE fecha <= {hasta:Date}
              GROUP BY idprospecto
          )
          WHERE vigente = {idejecutivo:Int32}
      )
  )
GROUP BY d.idprospecto, d.empresa
ORDER BY eventos DESC, idprospecto
