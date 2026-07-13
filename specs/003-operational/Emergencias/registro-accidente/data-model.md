# Data Model — Registro de Accidentes

## Entidades principales

### 1) `Fact_Accidente` (hecho central)

- **PK:** `idaccidente` (STRING, formato `ACC-{epoch_ms}-{4digitos}`)
- **FKs:** `idseveridad` → `Dim_Severidad`, `idcalle` → `Dim_Calle`, `idusuario` → `Dim_Usuarios`, `idtiporeportado` → `Dim_TipoReportado` (opcional), `idreferenciaestacion` → `Dim_ReferenciaEstacion` (opcional)
- **Campos métricos:** `latitudinicio`, `longitudinicio`, `numvehiculos`, `numvictimas`, `numheridos`, `numfallecidos`, `distanciamillas`, `duracionminutos`
- **Campos descriptivos:** `descripcion`, `codigopostal`, `horainicio`, `horafin`
- **Trazabilidad fusión:** `idaccidenteorigen` (STRING, nullable → caso padre)
- **Control:** `activo` (BOOLEAN)
- **Timestamps:** `fechahoraaccidente`, `fecha_actualizacion` (epoch ms)
- **Reglas:**
  - `idaccidente` único generado en creación.
  - `numheridos`, `numfallecidos`, `numvehiculos`, `numvictimas` solo incrementan (RN-REG-007).
  - `activo=false` en DESCARTADO; duplicado fusionado conserva trazabilidad vía `idaccidenteorigen`.

### 2) `Fact_AccidenteTipoEstadoAccidente` (historial de estados)

- **PK:** `idaccidentetipoestadoaccidente` (INT)
- **FKs:** `idaccidente`, `idtipoestadoincidente` → `Dim_TipoEstadoAccidente`, `idusuario`
- **Timestamps:** `fechahoramodificado`, `fecha_actualizacion`
- **Reglas:**
  - Cada transición inserta nuevo registro (append-only).
  - Estado actual = último por `fechahoramodificado`.
  - Estados: BORRADOR, REPORTADO, BUSCANDO_UNIDAD, ASIGNADO, EN_ATENCIÓN, CERRADO, DESCARTADO, FUSIONADO.

### 3) `Dim_ElementoClimaticosAccidente` (puente clima/período)

- **PK:** `idelementoclimaticoaccidente`
- **Campos:** `idaccidente`, `idperiododia`, `idestadoclima`, `idusuario`, `fecha_actualizacion`
- **Regla:** No son columnas directas de `Fact_Accidente`.

### 4) `Dim_ElementoFisicoAccidente` (puente elementos físicos)

- **PK:** `idelementosfisicosaccidente`
- **Campos:** `idaccidente`, `idelementofisico`, `idusuario`, `fecha_actualizacion`

### 5) `Dim_NotaAccidente` (notas de escalamiento O40)

- **PK:** `idnotaaccidentes`
- **Campos:** `idaccidente`, `idusuario`, `nota`, `tipo` (`escalamiento`), `sincronizado`, `activo`, `fechahora`, `fecha_actualizacion`

## Dimensiones de lectura (join, no persistidas en hecho)

| Dimensión | Uso en módulo |
|-----------|---------------|
| `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado` → `Dim_EstadoRegion` → `Dim_Pais` | Geocodificación, filtros lista, validación cobertura |
| `Dim_Severidad` | Valores 1–4 (Leve…Fatal) |
| `Dim_RegionOperativa` + `Dim_RegionOperativaEstadoRegion` | Cobertura operativa (`estadoregion='Producción'`) |
| `Dim_TipoReportado`, `Dim_PeriodosDias`, `Dim_EstadosClimas`, `Dim_Elementos_Fisicos` | Datos complementarios |
| `Fact_Despacho` | Precondición O40 (despacho activo confirmado) |

## Transiciones de estado (módulo registro-accidente)

```text
BORRADOR → REPORTADO     (auto sin advertencias | RF-REG-010 manual)
BORRADOR → DESCARTADO    (CU-O32)
BORRADOR → FUSIONADO     (CU-O41)
REPORTADO → FUSIONADO    (CU-O41)
REPORTADO → BUSCANDO_UNIDAD  (despacho-inteligente, fuera de alcance)
```

O40 **no** cambia estado; solo muta campos en `Fact_Accidente` + nota.

## Validaciones de dominio (RF-REG-003)

| Validación | Bloqueante | Efecto si advertencia + `forzarAdvertencias` |
|------------|------------|-----------------------------------------------|
| GPS rango global | Sí (400) | — |
| Fuera cobertura operativa | No | BORRADOR |
| Duplicado 50m/5min | No (409 sugerencia) | BORRADOR o fusión |
| Discrepancia geo GPS vs idcalle | No | BORRADOR |
| Fecha >24h sin retrospectivo | Sí (422) | — |
| Fecha futura | Sí (422) | — |
| Campos obligatorios vacíos | Sí (400) | — |

## Eventos Kafka (escritura)

| Topic | Disparadores |
|-------|--------------|
| `Fact_Accidente_topic` | Crear, editar, descartar (`activo`), fusionar (`idaccidenteorigen`), escalar severidad |
| `Fact_AccidenteTipoEstadoAccidente_topic` | Toda transición de estado |
| `Dim_ElementoClimaticosAccidente_topic` | Alta/edición datos climáticos |
| `Dim_ElementoFisicoAccidente_topic` | Alta elemento físico |
| `Dim_NotaAccidente_topic` | Escalamiento O40 |

Lecturas: queries Pinot vía repositorios (`core/repositories/accidentes/`).

## Auditoría (RNF-REG-004)

Log estructurado por acción: `crear`, `editar`, `descartar`, `confirmar_reporte`, `escalar`, `fusionar` con `idusuario`, `idaccidente`, timestamp, campos modificados, valores anterior/nuevo. Registro retrospectivo audita `justificacionRetrospectiva`.

## Mapeo API ↔ persistencia

| Endpoint | Tablas afectadas |
|----------|------------------|
| `POST /accidentes` | `Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente`, puentes opcionales |
| `PATCH /accidentes/{id}` | `Fact_Accidente`, puentes, audit log |
| `POST .../confirmar-reporte` | `Fact_AccidenteTipoEstadoAccidente` |
| `POST .../descartar` | `Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente` |
| `POST .../escalar-severidad` | `Fact_Accidente`, `Dim_NotaAccidente` |
| `POST .../fusionar` | `Fact_Accidente`, `Fact_AccidenteTipoEstadoAccidente` (duplicado) |
