# Data Model - Alta y Configuración de Unidades de Emergencia

## Entidades de dominio (lectura Pinot / escritura Kafka)

## 1) Unidad de emergencia (`Dim_UnidadEmergencia`)

- Primary key: `idunidademergencia`
- Campos:
  - `idcliente` (INT, FK a `Dim_Cliente`, **requerido siempre** — inmutable tras alta)
  - `idcondado` (INT, FK a `Dim_Condado`, requerido, editable — reemplaza a `zonacobertura`; determina la cobertura geográfica de la unidad, consumido por `despacho-inteligente` para filtrar candidatas por condado)
  - `tipopropiedad` (STRING: `Propia` | `Externa`, requerido, editable)
  - `placa` (STRING, requerido, único entre unidades activas)
  - `capacidad` (STRING, opcional, editable)
  - `contactoproveedor` (STRING, requerido solo si `tipopropiedad='Externa'`, editable)
  - `unidademergencia` (STRING, requerido, editable — nombre/identificador visible)
  - `tipounidademergencia` (STRING: `Ambulancia`|`Grúa`|`Patrulla`|`Bomberos`|`Defensa Civil`, requerido, editable)
  - `activo` (BOOLEAN, default `true` — `false` tras CU-O58)
  - `latitud`, `longitud` (FLOAT, editables — última posición conocida)
  - `fecha_actualizacion` (LONG epoch ms)
- Inmutables: `idunidademergencia`, `idcliente`.
- Reglas:
  - `placa` única entre unidades con `activo=true` (RN-CAM-003) — validada en alta (CU-O54), lote (CU-O56) y reactivación (CU-O58).
  - `activo=false` excluye la unidad del algoritmo de despacho (RN-CAM-001).
  - Concurrencia: last-write-wins en edición (RF-CAM-003), sin control de versión.

## 2) Baja de unidad (`Fact_BajaUnidad`)

- Primary key: `idbajaunidad`
- Campos:
  - `idunidademergencia` (FK a `Dim_UnidadEmergencia`)
  - `idusuario` (INT — quién ejecuta la baja)
  - `idaccidente` (FK a `Fact_Accidente`, nullable — solo si la baja fue forzada con despacho activo en curso)
  - `motivo` (STRING)
  - `tipobaja` (STRING: `Normal` | `Forzada_con_reasignación`)
  - `fechahora` (LONG epoch ms)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - Nunca se elimina ni modifica tras una reactivación posterior (RN-CAM-004) — historial append-only.

## 3) Historial de estado de disponibilidad (`Fact_HistorialEstadoUnidad`)

- Primary key: `idhistorialestadosunidadesemergencias`
- Campos:
  - `idunidademergencia` (FK)
  - `idestadounidademergencia` (FK a `Dim_EstadoUnidadEmergencia`)
  - `estadoanterior`, `estadonuevo` (STRING)
  - `idusuario` (INT — el Operador que declara, CU-O59; o la unidad-usuario si es autodeclaración, CU-O30 en `evidencia-unidad`)
  - `fechahora` (LONG epoch ms)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - El estado *actual* se obtiene siempre por la fila con `fechahora` más reciente — nunca es un campo directo.
  - "En Misión" es de escritura exclusiva del sistema (`despacho-inteligente`); no declarable vía CU-O59.
  - El Operador puede declarar cualquier otro estado (`Activa`, `Ocupada`, `Fuera de servicio`) vía CU-O59.
  - Alerta (no bloqueo) si se intenta marcar "Activa" con un despacho activo sin retirar en `Fact_Despacho` (RF-CAM-005).

## 4) Catálogo de estados (`Dim_EstadoUnidadEmergencia`) — solo lectura

- Valores: `Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`.

## 5) Despacho activo (`Fact_Despacho`) — solo lectura, módulo Emergencias

- Consultado en tiempo real (sin cache) para:
  - Bloquear/confirmar edición de `tipopropiedad`/`tipounidademergencia` si hay despacho sin `fechahoraretiro` (RF-CAM-003).
  - Determinar `tipobaja` y poblar `idaccidente` en `Fact_BajaUnidad` al forzar una baja (RF-CAM-004).
  - Alertar inconsistencia al declarar "Activa" vía CU-O59 (RF-CAM-005).

## 6) Condado (`Dim_Condado`) — solo lectura, módulo Emergencias/registro-accidente

- Referenciado por `idcondado`. Mismo catálogo que usa `registro-accidente` para resolver la ubicación de un accidente (`Dim_Calle → Dim_Ciudad → Dim_Condado`).

## Relaciones principales

- `Dim_UnidadEmergencia.idcliente → Dim_Cliente.idcliente`
- `Dim_UnidadEmergencia.idcondado → Dim_Condado.idcondado` (reemplaza al antiguo `zonacobertura` textual)
- `Fact_BajaUnidad.idunidademergencia → Dim_UnidadEmergencia.idunidademergencia`
- `Fact_BajaUnidad.idaccidente → Fact_Accidente.idaccidente` (nullable)
- `Fact_HistorialEstadoUnidad.idunidademergencia → Dim_UnidadEmergencia.idunidademergencia`
- `Fact_HistorialEstadoUnidad.idestadounidademergencia → Dim_EstadoUnidadEmergencia.idestadounidademergencia`
- Sin relación directa `Dim_UnidadEmergencia ↔ Dim_RegionOperativa` (RN-CAM-005).

## Impacto en módulos ya implementados (migración obligatoria)

| Módulo | Archivo | Cambio |
|---|---|---|
| `despacho-inteligente` | `specs/.../despacho-inteligente/spec.md` (líneas 43, 74) | `zonacobertura` → `idcondado` en el esquema documentado y en el criterio de filtro por condado |
| `despacho-inteligente` | `specs/.../despacho-inteligente/data-model.md` (línea 50) | Igual |
| `despacho-inteligente` | `backend/core/repositories/despacho/unidad_emergencia_repository.py` (`list_candidatas_por_condado`) | Usa `row.get("idcondado")` directo, elimina el cast de `zonacobertura` a int |
| `despacho-inteligente` | `backend/apps/despacho/services/disponibilidad_unidad_service.py` (`consultar`) | Expone `idcondado` en vez de `zonacobertura` en la respuesta de CU-O30 |
| `evidencia-unidad` | `specs/.../evidencia-unidad/contracts/evidencia-unidad.openapi.yaml:689` | `zonacobertura` → `idcondado` en el schema del contrato |
| `evidencia-unidad` | `frontend/src/app/modules/evidencia-unidad/services/models/evidencia-unidad.types.ts:136` | `zonacobertura: string \| null` → `idcondado: number \| null` |
| `evidencia-unidad` | `frontend/src/app/modules/evidencia-unidad/pages/panel-disponibilidad/panel-disponibilidad.page.html:62` | Binding `disponibilidad()!.zonacobertura` → `disponibilidad()!.idcondado` (ya no renderiza texto libre) |

**Nota de descubrimiento**: `evidencia-unidad` no apareció en la primera pasada de esta migración (research.md Decision 8 original) porque solo se rastreó el consumidor de backend (`despacho-inteligente`). `evidencia-unidad` consume el mismo campo únicamente en su contrato OpenAPI y frontend — sin repositorio propio que lo toque — lo cual lo hizo invisible a una búsqueda centrada en `core/repositories/`. Detectado en `/speckit-analyze` (hallazgo E1) mediante búsqueda de texto en todo el árbol de `frontend/`.
