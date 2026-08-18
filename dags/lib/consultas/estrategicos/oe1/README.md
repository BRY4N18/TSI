# Catálogo estratégico — OE1

Diez consultas publicadas. **E1-05, E1-07 y E1-08 no tienen fichero**: no hay
costos de marketing ni geografía comercial en `dim_cliente`. Un SQL suelto no
debe convertirse en endpoint.

Convención: `e1_NN_<informe>.sql`. El HTTP en kebab-case vive en `CATALOGO` del servicio.

- `FINAL` en `dim_cliente`, `dim_plan`, `dim_etapa_onboarding` y `hecho_suscripcion`.
- **Nunca** `FINAL` en `hecho_factura`, `hecho_transicion_embudo` ni `hecho_onboarding`.
- `{desde:Date}` `{hasta:Date}` `{granularidad:String}` ligados, nunca interpolados.
- MRR suma `precio_mensualizado`; no divide `precio`.
- Sin `idpais`, `idestado`, `tiene_metodo_pago`, `metodo_pago_caduca`.
- Sin `e1_05_*.sql`, `e1_07_*.sql`, `e1_08_*.sql`.
