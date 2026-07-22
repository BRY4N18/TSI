# Quickstart — Validación Despacho Inteligente

Guía de validación end-to-end contract-first para CU-O22–O24, O33–O36, O38, O45 y RF-DES-001–011.

## Prerrequisitos

- Spec: `spec.md` (clarificaciones Session 2026-07-09)
- Plan: `plan.md`, `research.md`, `data-model.md`
- Contrato: `contracts/despacho-inteligente.openapi.yaml`
- Dependencias: `autenticacion-y-rbac`, `registro-accidente` (caso REPORTADO), `evidencia-unidad` (unidades Activa en `Fact_HistorialEstadoUnidad`)
- Infra: Kafka productor/consumidor, Pinot broker lectura, job scheduler, backend Django, frontend Angular

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | CU/RF |
|--------|------|-------|
| `GET` | `/api/v1/accidentes/{idaccidente}/despacho` | RF-DES-011 |
| `GET` | `/api/v1/accidentes/{idaccidente}/despacho/stream` | RF-DES-011 (SSE) |
| `GET` | `/api/v1/accidentes/{idaccidente}/despacho/unidades-candidatas` | O33 (UI) |
| `POST` | `/api/v1/accidentes/{idaccidente}/despacho/asignar-manual` | CU-O33 |
| `POST` | `/api/v1/accidentes/{idaccidente}/despacho/escalar-zona` | CU-O34 |
| `POST` | `/api/v1/accidentes/{idaccidente}/despacho/coordinar` | CU-O38 |
| `GET` | `/api/v1/mi-despacho/pendientes` | O24/O45 (unidad) |
| `GET` | `/api/v1/mi-despacho/{idnotificaciondespacho}` | O23 payload |
| `POST` | `/api/v1/mi-despacho/{idnotificaciondespacho}/confirmar` | CU-O24 |
| `POST` | `/api/v1/mi-despacho/{idnotificaciondespacho}/rechazar` | CU-O45 |
| `GET` | `/api/v1/despacho/parametros` | RF-DES-010 |
| `PATCH` | `/api/v1/despacho/parametros` | RF-DES-010 |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ data, meta }`
- Envelope error: `{ error, detail, code }`
- `Idempotency-Key` en escrituras
- SSE: `Accept: text/event-stream`

**Flujos internos (sin REST):** O22 consumer, O23 notificación, O35 job, O36 consumer — ver `plan.md`.

## 2) Validar flujo backend (Vista → Servicio → Repositorio + Kafka)

### Escenario A — Asignación automática O22 tras REPORTADO

1. Registrar accidente en REPORTADO (`registro-accidente` quickstart).
2. Verificar consumer `AccidenteReportado` ejecuta `AsignacionInteligenteService`.
3. **Esperado:** eventos en `Fact_NotificacionDespacho_topic`, `Fact_Despacho_topic`, `Fact_HistorialDespachoUnidad_topic`; caso → `BUSCANDO_UNIDAD`; candidatas del mismo condado.

### Escenario B — Confirmación unidad O24

1. Login como `Unidad` con unidad vinculada.
2. `GET /mi-despacho/pendientes` → copiar `idnotificaciondespacho`.
3. `POST .../confirmar` con `Idempotency-Key`.
4. **Esperado:** HTTP 200, `estado_caso=ASIGNADO` (primer confirmado), unidad `En Misión`, `Fact_Despacho.activo=true`.

### Escenario C — Rechazo y re-asignación O45 + O36

1. Unidad rechaza con `{ "motivo": "Muy lejos" }`.
2. **Esperado:** `Fact_Despacho.activo=false`, historial Rechazado, nuevo intento O36 síncrono hacia siguiente candidata (excluye unidad que rechazó).

### Escenario D — Timeout O35 + O36 async

1. Simular despacho Pendiente sin respuesta > timeout (90s default).
2. Ejecutar job O35.
3. **Esperado:** Timeout en historial, `activo=false`, evento `DespachoTimeout_topic`; consumer O36 crea nuevo despacho.

### Escenario E — Fallo entrega O23

1. Mock `apps/notificaciones` fallando push y SMS tras reintento.
2. **Esperado:** `No_entregada`, `activo=false`, O36 síncrono inmediato (sin esperar O35).

### Escenario F — Escalamiento condado vecino O34

1. Caso sin candidatas en condado local.
2. `POST .../escalar-zona`.
3. **Esperado:** despacho con `origen=Escalado_zona` o HTTP 202 con alerta `Dim_NotaAccidente`.

### Escenario G — Despacho múltiple O38

1. Caso con grúa confirmada.
2. `POST .../coordinar` con ambulancia disponible.
3. **Esperado:** segundo `Fact_Despacho.activo=true` para misma `idaccidente`.

### Escenario H — Parámetros RF-DES-010

1. Login Director Tecnológico / Administrador.
2. `PATCH /despacho/parametros` timeout 60s, peso distancia 70%.
3. **Esperado:** HTTP 200; despachos subsecuentes usan nuevos valores; cambio en audit log.

### Validaciones transversales

- Sin escritura directa a Pinot (solo Kafka).
- O22 completa en <5s (CA-DES-001).
- Roles incorrectos → HTTP 403.
- Haversine usa posición efectiva (RN-DES-010).

## 3) Validar consumo frontend (Angular)

| Artefacto | Responsabilidad |
|-----------|-----------------|
| `DespachoApiService` | Monitoreo, candidatas, manual, escalar, coordinar |
| `MiDespachoApiService` | Pendientes, confirmar, rechazar |
| `DespachoSseService` | Stream monitoreo operador |
| `DespachoParametrosApiService` | RF-DES-010 |
| `OperadorDespachoGuard` | Rutas monitoreo/asignación |
| `UnidadDespachoGuard` | Rutas mi-despacho |
| `DirectorTecnologicoGuard` | Parámetros algoritmo |

Escenarios UI mínimos:

1. Panel monitoreo con historial intentos y mapa candidatas (RF-DES-011).
2. Unidad recibe pendiente y confirma/rechaza con motivo.
3. Operador asigna manualmente desde lista candidatas puntuadas.
4. SSE actualiza estado sin refresh manual.

## 4) Pruebas sugeridas

**Backend:**

- Contract tests por endpoint (`tests/api/test_despacho_*_contract.py`) contra OpenAPI.
- Unit tests `AsignacionInteligenteService` (scoring, filtro condado, exclusión rechazo).
- Consumer tests O22/O36 con mock Kafka.
- Job test O35 timeout threshold.

**Frontend:**

- Unit tests servicios con `HttpClientTestingModule`.
- Guard tests con JWT roles mock.
- `DespachoSseService` con `EventSource` mock.

## 5) Criterios de salida

- [ ] Todos los endpoints OpenAPI implementados y contract tests verdes
- [ ] O22–O36 flujos internos validados con quickstart escenarios A–E
- [ ] CA-DES-001–013 verificables manualmente o en integración
- [ ] Angular guards bloquean rutas por rol
- [ ] Ningún repositorio escribe directo a Pinot

Siguiente paso: `/speckit-tasks specs/003-operational/Emergencias/despacho-inteligente/spec.md`
