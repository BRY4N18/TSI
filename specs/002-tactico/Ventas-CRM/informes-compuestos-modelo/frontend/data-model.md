# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 13 informes viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador estable: `embudo` | `captacion` | `nutricion`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el Director / Gerente en el H1 |
| `pregunta` | Subtítulo: la pregunta de la spec |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional |

### Zona Z

| Zona | Qué contiene | Informes (ids de backend) |
|---|---|---|
| `heroe` | Métrica principal, arriba izquierda | ver contrato UI |
| `periodo` | Único filtro, arriba derecha | ninguno — control |
| `alcance` | `todos` / `propios`, junto al período | viene en `meta.acotado_a` de cualquier GET de la pantalla |
| `visual` | Distribución o serie, diagonal | ver contrato UI |
| `lectura` | Implicación, abajo derecha | ver contrato UI |
| `apoyo` | Segundo plano, plegado en `embudo` y `nutricion` | ver contrato UI |

Cada zona que pide datos tiene: `informe` (clave de `PUBLICADOS`), estado
`carga | dato | vacio | error | sin_dato`, y **no** comparte spinner con las otras.

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Fechas inclusive. Defecto: últimos 30 días (backend) |
| Única acción | Cambiarlo refresca **todas** las zonas de la pantalla |

No hay editor de `pesos_etapa` ni de `top` en el MVP. Viajan los defectos del servidor.

### Alcance de vista

| Valor | Quién lo recibe hoy | Qué se lee |
|---|---|---|
| `todos` | Director de Marketing | departamento entero |
| `propios` | Gerente de Ventas, Administrador | cartera del solicitante |

Se pinta **siempre** que el envelope lo traiga. No se infiere del rol.

### Lectura derivada (no llega como columna de negocio)

| Concepto | Cómo se obtiene |
|---|---|
| Convención de pesos | `meta.filtros.nota_pesos` (D7) |
| Mitad medible del CAC | `nota_indicador` de `convertidos-por-canal` (D6) |
| Sin dato | porcentaje o mediana `null` (FR-UI-007) |
| Estancado más lento | `segundos_mediana` de permanencia, con `abiertos` visible; no se recalcula en cliente |
| Vacío de nutrición | `data: []` (D12) |

## Validaciones de pantalla

- `data: []` → estado **vacío**, no héroe en 0 %.
- Una fila con `pct_* = null` → **sin dato**, no 0 %.
- Prohibido pintar columnas que no estén en el contrato UI de esa zona.
- Prohibido nombre, correo, teléfono, cargo, notas, mapas, coste, título «CAC».
- `idejecutivo` solo en la zona de carga; no se resuelve a persona.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—n Informe publicado (CATALOGO)
Listado simple  —  no tiene zona en esta capa
```
