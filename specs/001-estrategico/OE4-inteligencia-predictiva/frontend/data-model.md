# Data model — pantalla OE4 (no el almacén)

Esta capa **no crea tablas**.

## Pantalla de historia

`calidad` | `concentracion` | `impacto` | `cobertura`.

| Zona | Informes |
|---|---|
| `heroe` (calidad) | `indice-calidad-historico` |
| `visual` (calidad) | `completitud-campos-criticos` |
| `lectura` (calidad) | `campos-mas-ausentes` |
| `apoyo` (calidad) | `calidad-por-origen` |
| `heroe` (concentracion) | `concentracion-siniestralidad` |
| `visual` (concentracion) | `patron-horario-climatico` |
| `lectura` (concentracion) | alcance: no mapa; clima parcial |
| `heroe` (impacto) | `impacto-humano-por-zona` |
| `visual` (impacto) | `impacto-vial-por-zona` |
| `lectura` (impacto) | denominadores |
| `heroe` (cobertura) | `cobertura-del-historico` |
| `visual` (cobertura) | mismos datos: sin masa crítica |
| `lectura` (cobertura) | umbral publicado |

Estados de zona: `carga | dato | vacio | error | sin_dato`.

## Controles

`desde`, `hasta` obligatorios. `granularidad`: mes \| trimestre \| anio. `comparacion`: ninguna \| mom \| yoy.

## Envelope

`data` array. `meta.cobertura`, `meta.falta`, `meta.alcance`, `meta.objetivo` (sin `cumple`
booleano útil), `meta.comparacion`.

## Validaciones

- `data: []` → vacío, no 0 % de calidad.
- Índice sin componentes → no se pinta como KPI cerrado.
- `sin_masa_critica = 1` → etiqueta, no «listo».
- Prohibido lat/lon, región, slugs bloqueados.
