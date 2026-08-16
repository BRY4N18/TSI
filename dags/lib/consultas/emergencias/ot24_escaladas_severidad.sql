-- Informe #21 — Escaladas de severidad originadas en sitio · OT24
--
-- Cuántos casos cambiaron de gravedad después de reportarse, y en qué dirección.
--
-- Es la medida de cuánto se equivoca la clasificación inicial, que es la que
-- decide con qué prioridad se despacha. Una escalada al alza significa que se
-- envió menos de lo necesario, y esa es la que cuesta vidas.
--
-- ⚠️ CERO ESCALADAS ES UNA MEDICIÓN
-- ---------------------------------
-- Un caso que no cambió de gravedad tiene `num_escaladas_severidad = 0` y
-- `severidad_inicial` igual a la final. Eso **no** es un dato ausente: es un
-- caso bien clasificado desde el principio, que es lo normal y lo deseable.
--
-- Los casos con la métrica sin medir —cargados antes de que existiera— se
-- cuentan aparte. Meterlos entre los «sin escalada» afirmaría que se
-- clasificaron bien casos de los que no se sabe nada, y este informe se lee
-- justamente para decidir si la clasificación inicial es de fiar.
--
-- Se agrupa por el par inicial → final, y no solo por el número de escaladas,
-- porque «Leve que acabó en Fatal» y «Grave que acabó en Moderado» son la misma
-- cifra de escaladas y problemas opuestos.

SELECT
    toDate({desde:Date})                                        AS periodo,
    coalesce(severidad_inicial, 'Desconocido')                  AS severidad_inicial,
    coalesce(severidad, 'Desconocido')                          AS severidad_final,
    count()                                                     AS casos,
    countIf(num_escaladas_severidad > 0)                        AS con_escalada,
    countIf(num_escaladas_severidad IS NULL)                    AS sin_medir,
    sum(num_escaladas_severidad)                                AS escaladas_totales
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY severidad_inicial, severidad_final
ORDER BY con_escalada DESC, casos DESC, severidad_inicial, severidad_final
