-- Sesiones concurrentes por día y franja · OT18
--
-- ⚠️ Solape de intervalos, no conteo de inicios.
-- ⚠️ Duración mediana solo donde hay cierre; sesiones_sin_cierre lo declara.
-- Una sesión que cruza medianoche cuenta en ambas franjas.

WITH
    sesiones AS (
        SELECT
            idsesion,
            fechahora_inicio AS ini,
            if(fechahora_cierre IS NULL, now(), fechahora_cierre) AS fin,
            duracion_segundos,
            if(fechahora_cierre IS NULL, 1, 0) AS sin_cierre
        FROM hecho_sesion
        WHERE toDate(fechahora_inicio) <= {hasta:Date}
          AND toDate(if(fechahora_cierre IS NULL, now(), fechahora_cierre)) >= {desde:Date}
    ),
    dias AS (
        SELECT addDays({desde:Date}, number) AS fecha
        FROM numbers(dateDiff('day', {desde:Date}, {hasta:Date}) + 1)
    ),
    franjas AS (
        SELECT arrayJoin(['madrugada', 'manana', 'tarde', 'noche']) AS franja
    ),
    ventanas AS (
        SELECT
            d.fecha,
            f.franja,
            toDateTime(d.fecha) + toIntervalHour(
                multiIf(f.franja = 'madrugada', 0, f.franja = 'manana', 6, f.franja = 'tarde', 12, 18)
            ) AS ini_f,
            toDateTime(d.fecha) + toIntervalHour(
                multiIf(f.franja = 'madrugada', 6, f.franja = 'manana', 12, f.franja = 'tarde', 18, 24)
            ) AS fin_f
        FROM dias AS d
        CROSS JOIN franjas AS f
    ),
    recortes AS (
        SELECT
            s.idsesion,
            v.fecha,
            v.franja,
            greatest(s.ini, v.ini_f) AS ini_r,
            least(s.fin, v.fin_f) AS fin_r,
            s.duracion_segundos,
            s.sin_cierre,
            s.ini
        FROM sesiones AS s
        CROSS JOIN ventanas AS v
        WHERE s.ini < v.fin_f AND s.fin > v.ini_f
    ),
    recortes_ok AS (
        SELECT
            idsesion,
            fecha,
            franja,
            ini_r,
            fin_r,
            duracion_segundos,
            sin_cierre,
            ini
        FROM recortes WHERE ini_r < fin_r
    ),
    eventos AS (
        SELECT fecha, franja, ini_r AS t, 1 AS delta FROM recortes_ok
        UNION ALL
        SELECT fecha, franja, fin_r AS t, -1 AS delta FROM recortes_ok
    ),
    barrido AS (
        SELECT
            fecha,
            franja,
            sum(delta) OVER (
                PARTITION BY fecha, franja
                ORDER BY t, delta DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS carga
        FROM eventos
    ),
    por_franja AS (
        SELECT
            fecha,
            franja,
            max(carga) AS concurrencia_maxima
        FROM barrido
        GROUP BY fecha, franja
    ),
    iniciadas AS (
        SELECT
            toDate(ini) AS fecha,
            multiIf(
                toHour(ini) < 6, 'madrugada',
                toHour(ini) < 12, 'manana',
                toHour(ini) < 18, 'tarde',
                'noche'
            ) AS franja,
            countDistinct(idsesion) AS sesiones_iniciadas,
            medianIf(duracion_segundos, duracion_segundos IS NOT NULL) AS duracion_mediana,
            countIf(sin_cierre = 1) AS sesiones_sin_cierre,
            max(if(toDate(ini) != toDate(fin_r), 1, 0)) AS cruza_medianoche
        FROM recortes_ok
        GROUP BY fecha, franja
    )
SELECT
    p.fecha,
    p.franja,
    p.concurrencia_maxima,
    ifNull(i.sesiones_iniciadas, 0) AS sesiones_iniciadas,
    i.duracion_mediana,
    ifNull(i.sesiones_sin_cierre, 0) AS sesiones_sin_cierre,
    ifNull(i.cruza_medianoche, 0) AS cruza_medianoche
FROM por_franja AS p
LEFT JOIN iniciadas AS i ON i.fecha = p.fecha AND i.franja = p.franja
ORDER BY p.fecha, multiIf(
    p.franja = 'madrugada', 1,
    p.franja = 'manana', 2,
    p.franja = 'tarde', 3,
    4
)
