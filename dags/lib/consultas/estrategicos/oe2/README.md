# Catálogo estratégico — OE2

Diez consultas publicadas. **E2-06 no tiene fichero**: el log no mide minutos
en silencio; un SQL suelto no debe convertirse en endpoint.

Convención: `e2_NN_<informe>.sql`. HTTP en kebab-case vive en `CATALOGO` del servicio.

- Una sola fuente de consumo: `hecho_llamada_api`. Nunca un agregado.
- `FINAL` en `dim_partner`, `dim_plan`, `dim_version_contrato`.
- **Nunca** `FINAL` en `hecho_llamada_api` ni `hecho_factura`.
- `{desde:Date}` `{hasta:Date}` `{granularidad:String}` ligados, nunca interpolados.
- Sin IP, hash, secreto ni contacto técnico.
