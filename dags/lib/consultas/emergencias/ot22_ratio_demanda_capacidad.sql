-- Informe #7 — Ratio demanda / capacidad por condado · OT22 · origen: CU-T08
--
-- Cuántos casos hubo por unidad disponible, por condado y mes.
--
-- ⚠️ CORRIGE EL DEFECTO DE CU-T08: LA CAPACIDAD ES LA DEL PERÍODO, NO LA DE HOY
-- ----------------------------------------------------------------------------
-- El endpoint anterior cuenta la flota con `activo = true`, es decir **la flota
-- de hoy**. Aplicada a un período pasado, esa cifra responde a una pregunta que
-- nadie hizo: «¿cuántos casos hubo entonces por cada unidad que tenemos ahora?».
--
-- El error no se ve. Da un número plausible, y solo cambia cuando la flota
-- cambia — de modo que un informe de marzo consultado en marzo y el **mismo**
-- informe de marzo consultado en agosto dan cifras distintas sin que nada haya
-- pasado en marzo. Es la peor forma del fallo: el histórico se reescribe solo.
--
-- Aquí la capacidad sale de `dim_unidad`, que guarda **una versión por cada
-- cambio** de la unidad con su intervalo de vigencia. Se cuentan las versiones
-- cuya vigencia **solapa** el mes medido:
--
--     empieza antes de que el mes acabe   AND   acaba después de que el mes empiece
--
-- `valido_hasta IS NULL` significa «sigue vigente», no «caducó»: la condición lo
-- trata como un final infinito, que es lo que es. Confundirlo dejaría fuera
-- justamente a las unidades activas.
--
-- Se cuenta `uniqExact(idunidademergencia)` y no versiones: una unidad que
-- cambió de nombre a mitad de mes tiene dos versiones y sigue siendo una unidad.
-- Contar versiones inflaría la capacidad de los meses movidos, que son
-- precisamente aquellos en los que el ratio importa.

WITH
meses AS (
    SELECT DISTINCT toStartOfMonth(fecha) AS mes
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
),
demanda AS (
    SELECT
        toStartOfMonth(fecha)        AS mes,
        coalesce(condado, 'Desconocido') AS condado,
        uniqExact(idaccidente)       AS casos
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY mes, condado
),
capacidad AS (
    SELECT
        m.mes                            AS mes,
        coalesce(u.condado, 'Desconocido') AS condado,
        uniqExact(u.idunidademergencia)  AS unidades_vigentes
    FROM meses AS m
    CROSS JOIN (
        SELECT idunidademergencia, condado, valido_desde, valido_hasta
        FROM dim_unidad FINAL
    ) AS u
    WHERE u.valido_desde < addMonths(m.mes, 1)
      AND (u.valido_hasta IS NULL OR u.valido_hasta >= m.mes)
    GROUP BY mes, condado
)
SELECT
    formatDateTime(d.mes, '%Y-%m')       AS periodo,
    d.condado                            AS condado,
    d.casos                              AS casos,
    c.unidades_vigentes                  AS unidades_vigentes,
    -- ⚠️ Sin unidades no hay ratio: **ausente**, no cero ni infinito. Un `0`
    -- diría «hubo capacidad de sobra» y es lo contrario de lo que pasó.
    if(
        c.unidades_vigentes = 0,
        NULL,
        round(d.casos / c.unidades_vigentes, 2)
    )                                    AS ratio
FROM demanda AS d
LEFT JOIN capacidad AS c ON c.mes = d.mes AND c.condado = d.condado
ORDER BY periodo, condado
