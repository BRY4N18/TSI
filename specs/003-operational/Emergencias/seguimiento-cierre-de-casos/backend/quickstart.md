# Quickstart — Validación Seguimiento y Cierre de Casos

Guía de validación end-to-end contract-first para CU-O25–O29, O37, O39, O42, O44 y RF-SEG-001–011.

## Prerrequisitos

- Spec: `spec.md` (clarificaciones Session 2026-07-09)
- Plan: `plan.md`, `research.md`, `data-model.md`
- Contrato: `contracts/seguimiento-cierre-de-casos.openapi.yaml`
- Dependencias: `despacho-inteligente` (despacho Confirmado), `autenticacion-y-rbac`, `incorporacion-clientes` (`zonas_geograficas` por condado), `evidencia-unidad`
- Infra: Kafka, Pinot broker, job scheduler, backend Django, frontend Angular

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | CU/RF |
|--------|------|-------|
| `GET` | `/api/v1/seguimiento/mapa` | RF-SEG-007 |
| `GET` | `/api/v1/seguimiento/stream` | RF-SEG-007 (SSE) |
| `GET` | `/api/v1/accidentes/{idaccidente}/seguimiento` | O25/O26 |
| `POST` | `/api/v1/mi-seguimiento/posicion` | CU-O25 |
| `POST` | `/api/v1/mi-seguimiento/despachos/{iddespacho}/llegada` | CU-O26 |
| `POST` | `/api/v1/mi-seguimiento/despachos/{iddespacho}/abortar` | CU-O39 |
| `POST` | `/api/v1/accidentes/{idaccidente}/cerrar` | CU-O28 |
| `POST` | `/api/v1/accidentes/{idaccidente}/cancelar` | CU-O42 |
| `POST` | `/api/v1/despachos/{iddespacho}/forzar-retiro` | CU-O44 |
| `GET` | `/api/v1/emergencias/historial` | RF-SEG-005 |
| `GET` | `/api/v1/emergencias/historial/{idaccidente}/expediente` | CU-O29 |
| `GET` | `/api/v1/cliente/expedientes` | RF-SEG-006 |
| `GET` | `/api/v1/cliente/expedientes/{idaccidente}` | RF-SEG-006 |
| `GET` | `/api/v1/cliente/expedientes/{idaccidente}/pdf` | RF-SEG-006 |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ data, meta }`
- Envelope error: `{ error, detail, code }`
- `Idempotency-Key` en escrituras
- SSE: `Accept: text/event-stream`

**Flujos internos (sin REST):** geofencing O26, job O37, job depuración GPS, consumer `DespachoAbortado` — ver `plan.md`.

## 2) Validar flujo backend (Vista → Servicio → Repositorio + Kafka)

### Escenario A — Rastreo GPS O25

1. Despacho Confirmado (`despacho-inteligente` quickstart escenario B).
2. Login como `Unidad`; `POST /mi-seguimiento/posicion` cada 10s con `Idempotency-Key` único.
3. **Esperado:** eventos en `Dim_HistorialUbicacionUnidadEmergencia_topic` y `Dim_UnidadEmergencia_topic`; operador ve posición en SSE `seguimiento.posicion`.

### Escenario B — Llegada manual O26

1. Unidad en camino cerca del sitio.
2. `POST .../llegada`.
3. **Esperado:** historial `En_sitio`, `fechahorallegada` en `Fact_Despacho`, caso `EN_ATENCION`.

### Escenario C — Llegada geofencing O26

1. Enviar posiciones GPS dentro de 100m del accidente por >30s.
2. **Esperado:** llegada automática en respuesta GPS (`llegada_automatica: true`); notificación a app unidad.

### Escenario D — Cierre multi-despacho O28

1. Caso con grúa + ambulancia; ambulancia ya Retirado.
2. Operador `POST .../cerrar` con `resultado_atencion`.
3. **Esperado:** grúa auto-retirada con `idusuario` = operador; `horafin`/`duracionminutos`; caso `CERRADO`; unidades `Activa`.

### Escenario E — Cancelación O42

1. Caso falsa alarma con unidad despachada.
2. `POST .../cancelar` con `{ "motivo": "Falsa alarma" }`.
3. **Esperado:** CERRADO + `horafin`; motivo en `Dim_NotaAccidente`; **sin** campos RF-SEG-004 ni `Dim_EvidenciaFoto`.

### Escenario F — Forzar retiro O44

1. Técnico olvida retiro; operador `POST /despachos/{id}/forzar-retiro`.
2. **Esperado:** Retirado con `idusuario` operador; si todos retirados → CERRADO; si no → `EN_ATENCION`.

### Escenario G — Abortar misión O39

1. Unidad `POST .../abortar`.
2. **Esperado:** historial `Abortado`, unidad `Activa`, evento `DespachoAbortado_topic`, consumer despacho dispara O36.

### Escenario H — Pérdida señal GPS O37

1. Detener POST posición >60s con unidad en camino.
2. Ejecutar job O37.
3. **Esperado:** alerta `Dim_NotaAccidente` tipo `alerta`; `Fact_Despacho` sin cambios; SSE `seguimiento.alerta_gps`.

### Escenario I — Historial operador y expediente cliente

1. Operador `GET /emergencias/historial` con filtros fecha/estado.
2. Cliente `GET /cliente/expedientes` — solo CERRADOS en condados de `Dim_Preferencias_Cliente`.
3. **Esperado:** cliente HTTP 403 en `/seguimiento/mapa`; PDF descargable en `/pdf`.

### Validaciones transversales

- Sin escritura directa a Pinot (solo Kafka).
- Latencia mapa ≤5s desde GPS (RNF-SEG-001).
- Roles incorrectos → HTTP 403.
- Idempotencia: re-POST con misma key no duplica efectos.

## 3) Validar consumo frontend (Angular)

| Artefacto | Responsabilidad |
|-----------|-----------------|
| `SeguimientoApiService` | Mapa, historial, cerrar, cancelar, forzar retiro |
| `MiSeguimientoApiService` | GPS, llegada, abortar |
| `SeguimientoSseService` | Stream mapa operador |
| `ExpedienteClienteApiService` | Lista expedientes + PDF |
| `OperadorSeguimientoGuard` | Rutas operador |
| `UnidadSeguimientoGuard` | Rutas app unidad |
| `ClienteExpedienteGuard` | Portal cliente |

Escenarios UI mínimos:

1. Mapa con marcadores severidad + unidades en camino + ETA via SSE.
2. Unidad envía GPS en background; operador ve ruta recorrida.
3. Cierre caso con validación multi-despacho.
4. Cliente consulta expediente cerrado y descarga PDF.

## 4) Pruebas sugeridas

**Backend:**

- Contract tests por endpoint (`tests/api/test_seguimiento_*_contract.py`) contra OpenAPI.
- Unit tests `CerrarCasoService` (auto-retiro, idusuario), `GeofencingEvaluator`, `ExpedienteService` (filtro condado).
- Job tests O37 y depuración GPS (3 puntos conservados).

**Frontend:**

- `SeguimientoApiService` / `SeguimientoSseService` specs con `HttpClientTestingModule`.
- Guards con mock `AuthService` roles.

## 5) Orden de implementación recomendado

1. Validar OpenAPI como gate (`contracts/seguimiento-cierre-de-casos.openapi.yaml`).
2. Repositorios Kafka + topics en `settings.py`.
3. Servicios dominio (GPS → geofencing → cierre).
4. Jobs O37 + depuración.
5. Views DRF + permisos JWT.
6. Contract tests.
7. Módulo Angular `seguimiento/` (servicios → guards → páginas).
