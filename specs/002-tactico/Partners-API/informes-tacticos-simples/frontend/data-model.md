# Data model — pantalla (no el almacén)

Esta capa **no crea tablas**. El modelo y las cinco lecturas viven en
[`../backend/data-model.md`](../backend/data-model.md). Aquí solo se modela lo que la pantalla
compone.

## Entidades de interacción

### Audiencia

Decide **qué enlaces ve** y **qué guard abre la ruta**. No decide qué filas hay: eso es
`meta.acotado_a` del backend.

| Audiencia | Roles | Listados | `acotado_a` esperado |
|---|---|---|---|
| Acceso | `PartnerIntegracion`, más los de gestión | partners, credenciales, cambios-acceso | `propios` (Partner) / `todos` (gestión) |
| Contrato | `DesarrolladorAPIs`, `Administrador`, `DirectorTecnologico` | versiones-contrato, alcance-datos | `todos` |

`DirectorTecnologico` es gestión de **informes**, no `es_gestor()` operativo (research D0).

### Listado declarado

Una de cinco. Identificador estable = segmento de ruta.

| Campo | Regla |
|---|---|
| `id` | `partners` \| `credenciales` \| `cambios-acceso` \| `versiones-contrato` \| `alcance-datos` |
| `ruta` | Relativa a `/api/v1/informes/`, p. ej. `partners-api/credenciales` |
| `titulo` | Lo que lee el H1 |
| `columnas` | Exactamente las del OpenAPI de ese listado. **Cero** de secreto o de motivo en credenciales |
| `filtros` | Los del contrato. `partner` se declara en los tres de acceso y la página lo **omite** si el actor es Partner |
| `admiteRango` | `true` **solo** en `cambios-acceso` |
| `mensajeVacio` | Habla del dominio; no dice «sin datos» |

### Filtro condicional `partner`

No es una entidad de backend nueva. Es un recorte de la declaración **en la página**:

| Actor | ¿Se pinta `partner`? |
|---|---|
| Partner | No |
| Gestión de informes | Sí, en los tres de acceso. En contrato no aplica (el OpenAPI no lo declara en versiones/alcance) |

### Envelope que la pantalla está obligada a conservar

| Campo | Cuándo importa |
|---|---|
| `meta.acotado_a` | aviso si ≠ `todos`, **también con `data: []`** |
| `meta.pagination.has_next` / `cursor` | siguiente/anterior; el cursor es opaco |
| `detail` de error | `400` y `403` se muestran tal cual; no se pintan como tabla vacía |

`meta.alcance` no lo emite este departamento (es de composición de flota). No se inventa.

## Lectura que no se inventa en cliente

| Concepto | Cómo se obtiene |
|---|---|
| Credencial inactiva | `activa === false`. **No** hay motivo en la fila |
| Revocación vs cascada | `tipo_cambio` distinto en cambios de acceso; **no** agrupar |
| Partner no suspendido | `fecha_suspension` / `motivo_suspension` nulos → ausente |
| Reactivación sin motivo | `motivo` nulo → ausente, no «sin motivo» inventado |
| Alcance no configurado | `zonas_geograficas` (y condiciones) nulos → ausente, **nunca** «todas las zonas» |
| Versión aún publicada | `fecha_retiro` nulo → ausente; la fila retirada **no se omite** |
| Cupo cero | `0` se pinta `0`; no se confunde con `null` |

## Validaciones de pantalla

- `data: []` → vacío de dominio, con aviso de acotamiento si `propios`.
- Prohibido pintar columnas que no estén en el contrato UI de ese listado.
- Prohibido `client_secret`, `secret_hash`, `telefono_sms`, hash o pista del secreto.
- Prohibido recuento total y números de página.
- Prohibido selector de fechas en los cuatro de estado actual.
- Prohibido CTA operativo (suspender, reactivar, rotar secreto, aprobar producción).

## Relación con el backend

```text
Índice 1—n Listado declarado
Listado 1—1 Audiencia mínima (acceso | contrato)
Listado 1—1 GET partners-api/{id}
Audiencia acceso 1—n Rol (4)
Audiencia contrato 1—n Rol (3; subconjunto)
```
