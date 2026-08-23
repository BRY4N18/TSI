# Contrato UI — cuatro pantallas Z de OE4

Prefijo: `GET /api/v1/informes-estrategicos/oe4/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Slug | Pantalla |
|---|---|
| `indice-calidad-historico` | calidad (héroe) |
| `completitud-campos-criticos` | calidad (visual) |
| `campos-mas-ausentes` | calidad (lectura) |
| `calidad-por-origen` | calidad (apoyo) |
| `concentracion-siniestralidad` | concentracion |
| `patron-horario-climatico` | concentracion (visual) |
| `impacto-humano-por-zona` | impacto |
| `impacto-vial-por-zona` | impacto (visual) |
| `cobertura-del-historico` | cobertura |

`data-testid`: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`,
`zona-parcial`, `zona-comparacion`.

**Prohibido:** mapa; lat/lon; slugs bloqueados; semáforo; ítem gris; botón de venta.

| Ruta | Guard |
|---|---|
| `/estrategico/oe4/calidad` | Datos · Operaciones · Gerente |
| `/estrategico/oe4/concentracion` | Datos · Gerente |
| `/estrategico/oe4/impacto` | Datos · Operaciones · Gerente |
| `/estrategico/oe4/cobertura` | Datos · Gerente |
