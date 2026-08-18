-- Motivo de credencial inactiva · OT08
--
-- ⚠️ Distingue revocada, cascada, expirada y suspensión manual.

SELECT
    p.nombre_partner AS partner,
    c.motivo_inactividad AS motivo_inactividad,
    count() AS credenciales,
    round(count() / nullIf(sum(count()) OVER (PARTITION BY p.nombre_partner), 0), 4) AS pct
FROM dim_credencial_api AS c FINAL
INNER JOIN dim_partner AS p FINAL ON p.idpartner = c.idpartner
WHERE c.esta_activa = 0
  AND c.motivo_inactividad IS NOT NULL
  AND p.idpartner != -1
  AND {desde:Date} <= {hasta:Date}
  AND {dias_aviso_expiracion:Int32} >= 0
GROUP BY partner, motivo_inactividad
ORDER BY partner, motivo_inactividad
