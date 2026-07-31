# Data Model (UI): Prospectos — Frontend

**Capa**: frontend | **Depends-on**: [`../backend/data-model.md`](../backend/data-model.md)  
Este archivo describe **view-models / estado UI**, no redefine entidades Pinot/Kafka.

## ListadoProspectosQueryState

| Campo | Tipo UI | Maps to API |
|-------|---------|-------------|
| filtroActivo | `'todas' \| 'activo' \| 'inactivo'` | `activo` omit / true / false |
| filtroEtapa | `EtapaPipeline \| ''` | `etapa_actual` o omit |
| cursor | `number \| string \| null` | `cursor` |
| cursorStack | array | pager Anterior |
| limit | `20` | `limit` |

**Reglas**: cambiar filtro → reset cursor/stack; no cachear catálogo completo.

## ListadoProspectosRow (proyección)

Campos visibles: `idprospecto`, `nombres`, `apellidos`, `empresa`, `etapa_actual`, `activo`, (+ opcionales teléfono/gmail si caben).  
**Acción**: solo `eye` → ruta workpanel. Nombre/empresa **texto plano**.

## WorkpanelProspectoView (modo Ver)

Fuente: `GET …/prospectos/{id}` (+ historiales si el envelope los trae).  
Campos: todos RO/disabled.  
Acciones de dominio (visibilidad por reglas BE/rol):

- Avanzar etapa adyacente → `POST …/pipeline`
- Marcar Perdido (+ motivo modal) → pipeline `Perdido`
- Convertir (si Negociación) → `POST …/conversion`
- Asignar/reasignar (Admin / dueño según RF) → `PATCH …/asignacion`

**Prohibido**: Guardar ficha; modo Editar/Crear de contacto.

## PipelineBoardColumn

Clave = etapa no terminal activa (`Nuevo`…`Negociación`); cards con empresa + etapa + botones + ojo.  
`Ganado`/`Perdido` no reciben avance; pueden listarse aparte o filtrarse por `activo`.

## Auth UI flags

| Flag | Fuente | Uso |
|------|--------|-----|
| `esAdmin` | `hasRole('Administrador')` | CTA Entrada directa; asignación huérfano |
| `esGerenteCrm` | GerenteVentas \| GerenteCuentasPublicas | sin CTA alta |

## Relaciones

```text
Listado --(ojo)--> Workpanel Ver --(acciones)--> Pipeline / Asignacion / Conversion APIs
Board   --(ojo)--> Workpanel Ver
Board   --(botones)--> Pipeline API
Admin CTA --> EntradaDirecta page --> Conversion/entrada-directa API
```
