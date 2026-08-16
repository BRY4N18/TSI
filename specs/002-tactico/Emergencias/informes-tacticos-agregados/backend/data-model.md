# Phase 1 Data Model: Informes Tácticos Simples de Emergencias (Backend)

Esta feature no crea tablas ni modelos de dominio nuevos — es una capa de lectura agregada sobre tablas Pinot ya existentes. Las "entidades" son las formas de resultado de cada informe (DTOs de agregación), no persistencia.

## Fuente de datos por informe

### Registro de Accidente (7 informes)

| Informe | Tabla(s) fuente | Agregación |
|---|---|---|
| Volumen total de casos por período | `Fact_Accidente` | `COUNT(*) GROUP BY DATETRUNC(periodo, fechahoraaccidente)` |
| Distribución por severidad | `Fact_Accidente` → `Dim_Severidad` | `COUNT(*) GROUP BY idseveridad` |
| Distribución por zona/región | `Fact_Accidente` → `Dim_Calle`/`Dim_Ciudad`/`Dim_Condado`/`Dim_Estado` | `COUNT(*) GROUP BY` nivel geográfico solicitado |
| % de completitud de campos críticos | `Fact_Accidente` | `COUNT(idseveridad IS NOT NULL AND idcalle IS NOT NULL) / COUNT(*)` |
| % de descarte y fusión | `Fact_AccidenteTipoEstadoAccidente`, `Fact_Accidente.idaccidenteorigen` | `COUNT(estado IN (DESCARTADO, FUSIONADO)) / COUNT(*)` |
| Ranking de ubicaciones | `Fact_Accidente` → `Dim_Calle`/`Dim_Ciudad` | `COUNT(*) GROUP BY idcalle ORDER BY COUNT DESC LIMIT N` |
| Impacto humano por región | `Fact_Accidente` (`numvictimas`, `numheridos`, `numfallecidos`) → geografía | `SUM(...) GROUP BY` región y período |

### Despacho Inteligente (6 informes)

| Informe | Tabla(s) fuente | Agregación |
|---|---|---|
| % de asignaciones automáticas vs. manuales | `Fact_Despacho` → `Dim_OrigenDespacho`, `Dim_UnidadEmergencia.idcondado` | `COUNT(*) GROUP BY idorigendespacho` (+ corte opcional por condado) |
| Tiempo promedio reportado→confirmado | `Fact_AccidenteTipoEstadoAccidente` | Diferencia de `fechahoramodificado` entre estados ASIGNADO y REPORTADO, `AVG` |
| Distribución de tiempo de respuesta por severidad | `Fact_Despacho` + `Fact_Accidente.idseveridad` + `Dim_UnidadEmergencia.idcondado` | Diferencia de tiempos, `GROUP BY idseveridad` (+ condado opcional) |
| % de rechazo/timeout por unidad | `Fact_HistorialDespachoUnidad` → `Dim_EstadoDespacho` | `COUNT(estado IN (Rechazado, Timeout)) / COUNT(*) GROUP BY idunidademergencia` |
| Carga de despachos por unidad | `Fact_Despacho` | `COUNT(*) GROUP BY idunidademergencia` |
| Ratio demanda/capacidad por condado | `Fact_Accidente` → geografía, `Dim_UnidadEmergencia` (`activo=true`) | `COUNT(Fact_Accidente) / COUNT(Dim_UnidadEmergencia activas) GROUP BY idcondado` |

### Seguimiento y Cierre de Casos (3 informes)

| Informe | Tabla(s) fuente | Agregación |
|---|---|---|
| Tiempo promedio asignado→cerrado | `Fact_AccidenteTipoEstadoAccidente` | Diferencia de `fechahoramodificado` entre CERRADO y ASIGNADO, `AVG GROUP BY` unidad/zona/período |
| % de cierres forzados | `Fact_HistorialDespachoUnidad` (`idestadodespacho=Retirado`) | `COUNT(Retirado por operador) / COUNT(Retirado total)` |
| % de abortos/pérdidas sobre despachos | `Fact_HistorialDespachoUnidad` (`idestadodespacho=Abortado`) | `COUNT(Abortado) / COUNT(*) GROUP BY idunidademergencia` |

## DTO de respuesta (forma común)

Todos los endpoints devuelven la misma envoltura (`api-standards.md`), con `data` como lista de grupos:

```jsonc
{
  "data": [
    { "grupo": "...", "valor": 0, "...": "..." }
  ],
  "meta": {
    "periodo": { "desde": "2026-07-01", "hasta": "2026-07-31", "granularidad": "dia" },
    "filtros": { "idcondado": null }
  }
}
```

El shape exacto de cada fila de `data` (nombres de campo) se fija en `contracts/informes-tacticos-agregados.openapi.yaml`, uno por informe.

## Fuera de alcance de esta fase

- Ninguna tabla ni modelo Django (`models.py`) — no hay persistencia propia.
- Ningún informe compuesto (ClickHouse/Airflow) — pertenece a `../../informes-tacticos-compuestos/`.
- La disposición visual de las tarjetas por workpanel — se define en `../frontend/`.
