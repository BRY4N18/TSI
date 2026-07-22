# Data Model - Onboarding y Validación de Región Operativa

## Entidades de dominio (lectura Pinot / escritura Kafka)

## 1) Región operativa (`Dim_RegionOperativa`)

- Primary key: `idregionoperativa`
- Campos:
  - `idestado` (INT, FK a `Dim_EstadoRegion`, requerido, inmutable tras alta — dimensión geográfica, no confundir con estado de ciclo de vida)
  - `nombreregion` (STRING, requerido, editable)
  - `estadoregion` (STRING: `En_Validación` | `Producción` | `En_Alerta` | `Despublicada`, requerido — campo de estado **directo**, sobrescrito en cada transición, sin tabla de historial)
  - `activo` (BOOLEAN, default `true` — `false` tras rechazo definitivo en CU-O60)
  - `fecha_actualizacion` (LONG epoch ms)
- Inmutables: `idregionoperativa`, `idestado`.
- Reglas:
  - `estadoregion` solo pasa a `Producción` si existe ≥1 fila en `Dim_ValidacionRegion` con `resultado='Aprobada'` para esa región (RN-REGON-003).
  - Transición posible desde cualquier estado no-`[activo=false]` hacia `Producción` vía `CU-O55` (reingreso confirmado en clarificación) — ver Sección 9 del spec.
  - Concurrencia: last-write-wins en `estadoregion` (último `INSERT` en `Dim_ValidacionRegion` procesado gana), sin control de versión — confirmado en clarificación.

## 2) Validación de región (`Dim_ValidacionRegion`)

- Primary key: `idvalidacionregion`
- Campos:
  - `idregionoperativa` (FK a `Dim_RegionOperativa`)
  - `idusuario` (INT — quien ejecuta/aprueba; Administrador o Director Tecnológico)
  - `resultado` (STRING libre: `'Aprobada'` | `'Rechazada'` — **no** FK a catálogo, no existe `Dim_Estado_Implementacion`)
  - `motivo` (STRING, obligatorio solo si `resultado='Rechazada'`)
  - `fechahora` (LONG epoch ms)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - Append-only: nunca se sobrescribe ni elimina una fila previa (RNF-REGON-001) — cada ejecución de `CU-O55` es una fila nueva, incluidas las reactivaciones.
  - Historial completo consultable por `idregionoperativa`, ordenado por `fechahora` (CA-REGON-004).
  - La validación en sí es una revisión manual — el sistema no ejecuta checklist técnico automatizado; solo persiste el resultado declarado (confirmado en clarificación).

## 3) Cobertura geográfica de la región (`Dim_RegionOperativaEstadoRegion`) — solo lectura en este spec

- Primary key: `idregionoperativaestadoregion`
- Campos: `idregionoperativa` (FK), `idestadoregion` (FK a `Dim_EstadoRegion`), `nombreregion`, `activo`, `fecha_actualizacion`.
- Es una tabla puente geográfica (qué estados/provincias cubre la región), **no** un historial de ciclo de vida. No se escribe desde este spec (fuera de alcance de CU-O55/O60/O61/O62); documentada por completitud del esquema.

## 4) Catálogo geográfico (`Dim_EstadoRegion`) — solo lectura

- Dimensión geográfica (estado/provincia). Referenciada por `Dim_RegionOperativa.idestado` y `Dim_RegionOperativaEstadoRegion.idestadoregion`.

## 5) Casos activos (`Fact_Accidente`) — solo lectura, módulo Emergencias

- Consultada en tiempo real (sin cache) por `CU-O61` para la regla de continuidad: al despublicar una región, los casos sin cierre dentro de esa zona no se cancelan, solo se bloquean casos nuevos (RF-REGON-003, RNF-REGON-002).

## 6) Unidades activas (`Dim_UnidadEmergencia`) — solo lectura, módulo Red-Operativa (`alta-unidades`)

- Referenciada conceptualmente por `CU-O62` (conteo de unidades activas dispara la despublicación automática). **Sin FK real a `Dim_RegionOperativa`** (RN-REGON-005) — el servicio `despublicacion_automatica_service.py` queda implementado pero sin disparador automático conectado (ver `research.md` Decision 4).

## Relaciones principales

- `Dim_RegionOperativa.idestado → Dim_EstadoRegion.idestadoregion`
- `Dim_ValidacionRegion.idregionoperativa → Dim_RegionOperativa.idregionoperativa`
- `Dim_RegionOperativaEstadoRegion.idregionoperativa → Dim_RegionOperativa.idregionoperativa` (puente geográfico, solo lectura en este spec)
- `Dim_RegionOperativaEstadoRegion.idestadoregion → Dim_EstadoRegion.idestadoregion`
- Regla de continuidad: `Fact_Accidente` (sin FK física declarada en este spec — validación en tiempo real por zona geográfica al crear un accidente, módulo Emergencias/`registro-accidente`).
- Sin relación directa `Dim_UnidadEmergencia ↔ Dim_RegionOperativa` (RN-REGON-005, igual que documentado en `alta-unidades/data-model.md` RN-CAM-005).

## Estados y transiciones (`Dim_RegionOperativa.estadoregion`)

| Estado | Significado |
|---|---|
| `En_Validación` | Región registrada, protocolo en curso o con rechazos previos. |
| `Producción` | ≥1 validación `Aprobada`; recibe accidentes reales. |
| `En_Alerta` | En producción pero degradada (`CU-O61`). |
| `Despublicada` | Retirada de operación, manual (`CU-O61`) o automática (`CU-O62`). |

```
En_Validación → Producción      (CU-O55, resultado='Aprobada')
En_Validación → [activo=false]  (CU-O60, rechazo definitivo)
Producción → En_Alerta          (CU-O61)
Producción → Despublicada       (CU-O61 o CU-O62)
En_Alerta → Despublicada        (CU-O61 o CU-O62)
En_Alerta → Producción          (CU-O55, resultado='Aprobada' — reactivación)
Despublicada → Producción       (CU-O55, resultado='Aprobada' — reactivación)
```

## Impacto en módulos ya implementados

Ninguno. Este spec es aditivo sobre la app `red_operativa` y no modifica tablas ni contratos de `alta-unidades`. La dependencia hacia `registro-accidente` (validación de `estadoregion='Producción'` antes de crear un `Fact_Accidente`) es de solo lectura desde ese módulo, sin cambio de esquema requerido aquí.
