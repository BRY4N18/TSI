# Catálogo estratégico — OE5

Nueve consultas publicadas. **E5-01 y E5-11 no tienen fichero** (NPS y entregas).
**E5-09, E5-10, E5-13 y E5-14 no tienen fichero**: viven en OE1.

Convención: `e5_NN_<informe>.sql`. El HTTP en kebab-case vive en `CATALOGO` del servicio.

- `FINAL` en `dim_cliente`, `dim_plan` y `hecho_ticket` / `hecho_suscripcion`.
- **Nunca** `FINAL` en `hecho_factura`, `hecho_solicitud_cambio_plan`,
  `hecho_accion_ticket`, `hecho_sesion` ni `hecho_llamada_api`.
- `{desde:Date}` `{hasta:Date}` `{granularidad:String}` ligados, nunca interpolados.
- SLA: denominador = cerrados con `tiene_compromiso = 1`.
- NRR: no copiar el stub de expansión=0 de OT07.
- Sin asunto, descripción, mensaje, `idmetodopago`, `calificacion`.
- Sin `e5_01_*.sql`, `e5_09_*.sql`, `e5_10_*.sql`, `e5_11_*.sql`, `e5_13_*.sql`, `e5_14_*.sql`.
