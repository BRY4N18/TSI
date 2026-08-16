-- Informe #5 — Ranking de ubicaciones con más casos · OT21 · origen: ±
--
-- ⛔ SIN COORDENADAS, por diseño
-- ------------------------------
-- La ubicación se expresa por nombre: condado, ciudad y calle. La constitución
-- trata la geolocalización de accidentes como dato sensible con su propio
-- control de acceso y auditoría, y **la exención de la autoridad departamental
-- no la levanta**. Un ranking de coordenadas con recuento de casos es un mapa de
-- siniestralidad exportable.
--
-- El modelo ni siquiera las trajo: el origen las tiene y la carga las dejó
-- fuera, así que aquí no hay nada que excluir — no están.
--
-- Las ubicaciones sin resolver se agrupan bajo 'Desconocido' en vez de omitirse:
-- un montón de casos sin calle es en sí mismo un hallazgo del ranking.

SELECT
    coalesce(condado, 'Desconocido')   AS condado,
    coalesce(ciudad, 'Desconocido')    AS ciudad,
    -- ⚠️ `nullIf(calle, '')` y no `coalesce(calle, …)` a secas: en ClickHouse un
    -- LEFT JOIN sin coincidencia rellena con el **valor por defecto del tipo**,
    -- no con NULL. Una calle que no está en la dimensión vuelve como cadena
    -- vacía, y `coalesce` no dispara porque `''` no es nulo. El resultado sería
    -- una fila con la calle en blanco: parece un fallo de maquetación y
    -- significa que la ubicación no se pudo resolver.
    coalesce(nullIf(calle, ''), 'Desconocido')  AS calle,
    casos
FROM (
    SELECT
        h.condado                       AS condado,
        h.ciudad                        AS ciudad,
        g.calle                         AS calle,
        count()                         AS casos
    FROM hecho_accidente AS h FINAL
    LEFT JOIN (
        SELECT idcalle, calle FROM dim_geografia FINAL
    ) AS g ON g.idcalle = h.idcalle
    WHERE h.fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY condado, ciudad, calle
)
ORDER BY casos DESC, condado, ciudad, calle
LIMIT {top:UInt32}
