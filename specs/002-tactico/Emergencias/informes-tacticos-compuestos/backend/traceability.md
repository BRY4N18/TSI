# Trazabilidad: Informes Tácticos Compuestos de Emergencias (Backend)

## Success Criteria

| SC | Descripción | Tareas | Verificación real | Estado |
|----|-------------|--------|--------------------|--------|
| SC-001 | Lectura de informe compuesto ya materializado < 2s | T017-T021, T027, T037 | `curl` real, `perdida-senal`/`indice-calidad`/`rendimiento-proveedor` responden en < 1s | ✓ |
| SC-002 | Detección de huecos de señal GPS sin falsos negativos | T011, T015 | `docker exec ... airflow dags trigger perdida_senal_gps` sobre pings reales con hueco de 200s (umbral 60s) — 1/1 hueco detectado | ✓ |
| SC-003 | Idempotencia por período (re-ejecutar no duplica filas) | T012, T021 | Segunda corrida de `perdida_senal_gps` sobre el mismo período — conteo de filas sin cambio (1→1) | ✓ |
| SC-004 | Distinguir rendimiento entre proveedores | T032, T041 | `rendimiento_por_proveedor` materializó filas diferenciadas por `idcliente` con datos reales | ✓ |

## Bugs reales encontrados y corregidos (revisión 2026-08-02, fuera del ciclo normal `/tasks`)

| # | Descripción | Archivos | Detectado por |
|---|---|---|---|
| B1 | `IN (%(ids)s)` con paréntesis duplicados → `SQLParsingError` en Pinot real con 2+ elementos | `despacho_repository.py`, `seguimiento_repository.py` (6 sitios) | `curl` contra Pinot real — no reproducible con `mock_pinot` |
| B2 | `DATETRUNC` de Pinot real devuelve epoch ms, no string — `periodo` salía como número crudo | `registro_repository.py`, `seguimiento_repository.py`, `_periodo_utils.py` (nuevo), `conftest.py` (mock corregido) | `curl` contra Pinot real |
| B3 | `IS NOT NULL` de Pinot no filtra el sentinel de "sin valor" (`enableColumnBasedNullHandling=false`) → `TypeError` | `despacho_repository.py::tiempo_respuesta_por_severidad` | `curl` contra Pinot real |
| B4 | `HistorialUbicacionRepository` usaba columna `idhistorialubicacion`, inexistente en el esquema real (`idhistorialunidademergencia`) — bug preexistente ajeno a esta feature, autoconsistente con su propio mock | `core/repositories/seguimiento/historial_ubicacion_repository.py`, `apps/seguimiento/services/gps_depuracion_service.py`, sus tests, `conftest.py` | Publicación real vía Kafka durante la verificación de US1 |

## Cambio de esquema (2026-08-02)

`Fact_HistorialDespachoUnidad.idusuario` (INT, nullable) añadido vía `PUT /schemas/Fact_HistorialDespachoUnidad` al Pinot Controller ya corriendo — resuelve la limitación L3 documentada en `.specify/docs/changelog.md`. El código de aplicación (`HistorialDespachoRepository.publish`, `RetiroDespachoService`, `ForzarRetiroService`) ya enviaba el campo en el payload Kafka; Pinot lo descartaba en silencio por no estar declarado en el schema. `seguimiento_repository.cierres_forzados()` actualizado para calcular "forzado" como `estadonuevo='Retirado' AND idusuario IS NOT NULL` (antes: aproximaba con solo `estadonuevo='Retirado'`). Verificado con escritura real: fila con `idusuario=999` publicada, indexada y consultable en Pinot tras `POST /segments/.../reload`.

## Limitaciones conocidas (documentadas, no bloqueantes)

Ver `.specify/docs/changelog.md`, entrada "2026-08-02 — Limitaciones conocidas de los informes tácticos compuestos":
- **L1**: `materializado` es `true` para cualquier período una vez que un DAG corrió al menos una vez (reprocesamiento completo, no ventana incremental).
- **L2**: `rendimiento_por_proveedor` usa el proveedor actual de la unidad, no el vigente históricamente (sin tabla de tipo SCD para `idcliente`).
