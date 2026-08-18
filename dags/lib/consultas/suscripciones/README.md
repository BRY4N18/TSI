# Catálogo de consultas — Suscripciones y Facturación

La definición canónica de cada informe está en
`specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md`.
Aquí solo viven las consultas.

## Cuatro reglas propias

1. **Ninguna consulta lee `activo`** para saber si una suscripción está vigente. Se lee
   `estado_derivado`.
2. **Los ingresos se suman con `monto_con_signo`**, nunca con `monto_total`: las notas de crédito
   restan solas.
3. **`En disputa` no entra en ningún cálculo de impago ni de mora.**
4. **Ninguna consulta devuelve medio de cobro, identificador fiscal ni desglose por persona.**

## Versión final

`FINAL` es **obligatorio** en `dim_plan`, `dim_cliente` y `hecho_suscripcion`.
Es **prohibido** en `hecho_factura` y `hecho_solicitud_cambio_plan`.
