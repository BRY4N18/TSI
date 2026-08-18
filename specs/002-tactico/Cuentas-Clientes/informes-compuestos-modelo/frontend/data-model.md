# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo analítico y los 9 informes viven en el backend. Aquí solo se modela lo que la pantalla compone.

## Entidades de interacción

### Pantalla de historia

Una de tres. Identificador estable: `ciclo` | `incorporacion` | `acceso`.

| Campo | Regla |
|---|---|
| `id` | Coincide con el segmento de ruta |
| `titulo` | Lo que lee el cargo en el H1 |
| `pregunta` | Subtítulo |
| `materia` | `ciclo` / `incorporacion` / `acceso` — el guard se elige por aquí |
| `zonas` | Exactamente las cuatro del patrón Z, más `apoyo` opcional en ciclo y acceso |

### Zona Z

| Zona | Ciclo | Incorporación | Acceso |
|---|---|---|---|
| `heroe` | `churn-por-cohorte` | `tiempo-onboarding` | `concurrencia-sesiones` (máxima + inicios) |
| `periodo` | control | control | control |
| `visual` | `usuarios-vs-tope` | `embudo-abandono` | `concurrencia-sesiones` (franjas) |
| `lectura` | `cuentas-en-riesgo` | `tasa-aprobacion` | `roles-incompatibles` |
| `apoyo` | `antiguedad-media` | — | duración + `sesiones_sin_cierre` (mismo GET de concurrencia) |

Héroe y visual de Acceso **comparten** el GET de `concurrencia-sesiones` (un informe, dos zonas).

### Período de vista

| Campo | Regla |
|---|---|
| `desde`, `hasta` | Inclusive. Defecto: últimos 30 días |
| Única acción global | Cambiarlo refresca **todas** las zonas |

### Envelope de lectura

| Campo | Regla |
|---|---|
| `data.resultados` | Filas. Array vacío → zona **vacio** |
| `data.periodo` | Corte que el backend aplicó |
| `meta.nota_cobertura` | Ocupación y riesgo |
| `meta.nota_catalogo` | Embudo |
| `meta.nota_solape` | Concurrencia si hay cruce de medianoche |

### Lectura derivada

| Concepto | Cómo se obtiene |
|---|---|
| Sin dato de ocupación | `tope_plan` nulo |
| Sin actividad conocida | `sin_actividad_conocida = 1` |
| En proceso | `en_proceso` aparte de `dias_mediana` |
| Etapa fantasma | fila con `clientes_que_llegaron = 0` **visible** |
| Concurrencia vs inicios | `concurrencia_maxima` y `sesiones_iniciadas` en el mismo informe |
| Pares vacíos | `resultados: []` en roles → vacío, no error |

## Validaciones de pantalla

- `resultados: []` → **vacio**, no churn 0 % ni concurrencia 0.
- `tope_plan` nulo → **sin dato**, no 0 %.
- `sin_actividad_conocida` → texto, nunca «0 días».
- `en_proceso` no se pinta como 0 días.
- Prohibido filtrar etapas con cero.
- Prohibido token, nombre, correo, teléfono, mapas.
- Prohibido un enlace que fusione las tres historias.

## Relación con el backend

```text
Pantalla 1—n Zona Z 0—n Informe publicado (CATALOGO)
Listado simple / gestión de cuenta / incorporación operativa  —  no tiene zona en esta capa
```
