# Quickstart — Validación Registro de Accidentes

Guía de validación end-to-end contract-first para CU-O21, O32, O40, O41 y RF-REG-010.

## Prerrequisitos

- Spec: `spec.md` (con clarificaciones Session 2026-07-09)
- Contrato: `contracts/registro-accidente.openapi.yaml`
- Dependencias operativas: `autenticacion-y-rbac` (JWT + roles), `incorporacion-regional` (regiones en Producción)
- Infra: Kafka productor, Pinot broker lectura, backend Django, frontend Angular

## 1) Validar contrato REST (backend contract-first)

Revisar endpoints en OpenAPI:

| Método | Ruta | UC/RF |
|--------|------|-------|
| `GET` | `/api/v1/accidentes/geocodificacion-inversa` | RF-REG-006 |
| `GET` | `/api/v1/accidentes` | RF-REG-005 |
| `POST` | `/api/v1/accidentes` | CU-O21 |
| `GET` | `/api/v1/accidentes/{idaccidente}` | RF-REG-005 |
| `PATCH` | `/api/v1/accidentes/{idaccidente}` | RF-REG-005 |
| `POST` | `/api/v1/accidentes/{idaccidente}/confirmar-reporte` | RF-REG-010 |
| `POST` | `/api/v1/accidentes/{idaccidente}/descartar` | CU-O32 |
| `POST` | `/api/v1/accidentes/{idaccidente}/escalar-severidad` | CU-O40 |
| `POST` | `/api/v1/accidentes/{idaccidente}/fusionar` | CU-O41 |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ data, meta }`
- Envelope error: `{ error, detail, code }`
- Paginación cursor en listado
- `Idempotency-Key` en escrituras

## 2) Validar flujo backend (Vista → Servicio → Repositorio + Kafka)

### Escenario A — Registro exitoso → REPORTADO

1. Login como `Operador de emergencias` (ver quickstart auth-rbac).
2. `POST /api/v1/accidentes` con coordenadas en cobertura, campos obligatorios, sin advertencias.
3. **Esperado:** HTTP 201, `data.estado = "REPORTADO"`, eventos en `Fact_Accidente_topic` y `Fact_AccidenteTipoEstadoAccidente_topic`.

### Escenario B — Fuera de cobertura forzado → BORRADOR

1. Coordenadas fuera de región Producción.
2. `POST` con `?forzarAdvertencias=true`.
3. **Esperado:** HTTP 201, `data.estado = "BORRADOR"`, `advertencias` incluye `fuera_cobertura`.

### Escenario C — Confirmar reporte (RF-REG-010)

1. Caso en BORRADOR del escenario B.
2. `POST .../confirmar-reporte` con `{ "confirmacion": true }`.
3. **Esperado:** HTTP 200, `estado = "REPORTADO"`.

### Escenario D — Duplicado con sugerencia de padre (RN-REG-010b)

1. Registrar accidente base.
2. `POST` segundo accidente en radio 50m/5min sin forzar.
3. **Esperado:** HTTP 409 con `idaccidente_principal_sugerido` = registro más antiguo.
4. `POST .../fusionar` con `idaccidenteprincipal` confirmado.
5. **Esperado:** HTTP 200, duplicado `FUSIONADO`.

### Escenario E — Descarte BORRADOR (O32)

1. Caso en BORRADOR.
2. `POST .../descartar` opcional `{ "motivo": "falsa alarma" }`.
3. **Esperado:** HTTP 200, `activo=false`, estado DESCARTADO.

### Escenario F — Escalamiento ASIGNADO/EN_ATENCIÓN (O40)

1. Caso con `Fact_Despacho` activo confirmado (datos semilla o integración despacho).
2. Login como `Unidad de emergencia`.
3. `POST .../escalar-severidad` con `idseveridad` mayor y `nota`.
4. **Esperado:** HTTP 200, nota en `Dim_NotaAccidente_topic`, estado sin cambio.

### Escenario G — Registro retrospectivo

1. `fechahoraaccidente` >24h con `registroRetrospectivo=true` y `justificacionRetrospectiva`.
2. **Esperado:** HTTP 201; sin justificación → HTTP 422.

### Validaciones transversales

- Sin escritura directa a Pinot (solo publicación Kafka).
- Validaciones RF-REG-003 completan en <2s (RNF-REG-005).
- Roles incorrectos → HTTP 403.

#### Evidencia RNF-REG-005 (T086)

Ejecutar en `backend/`:

```bash
python -m pytest apps/accidentes/tests/performance/test_registro_accidente_p95.py -m slow -v
```

Resultado esperado (entorno local con mocks): p95 ≤ 500ms en 20 iteraciones de `RegistroAccidenteService.registrar()`.

Cobertura servicios:

```bash
python -m pytest apps/accidentes/tests/ --cov=apps/accidentes/services --cov-report=term-missing -q
```

Umbral T089: ≥80% (actual ~93% en servicios de dominio accidentes).

## 3) Validar consumo frontend (Angular)

Componentes objetivo (`frontend/src/app/modules/accidentes/`):

| Artefacto | Responsabilidad |
|-----------|-----------------|
| `AccidenteApiService` | CRUD + acciones sub-recurso según OpenAPI |
| `GeocodificacionApiService` | `GET geocodificacion-inversa` |
| `OperadorEmergenciasGuard` | Rutas registro/lista/edición/fusión/descarte |
| `UnidadEmergenciaGuard` | Ruta escalamiento O40 |
| `accidentes.routes.ts` | Lazy loading módulo |

Escenarios UI mínimos:

1. Formulario registro con sugerencia geocodificación y manejo de advertencias.
2. Modal duplicado con padre preseleccionado (más antiguo).
3. Botón "Confirmar reporte" visible solo en BORRADOR.
4. Unidad sin despacho activo no accede a escalamiento.

## 4) Pruebas sugeridas

**Backend:**

- Contract tests por endpoint (`tests/api/test_*_contract.py`) contra OpenAPI.
- Unit tests servicios: validación, promoción BORRADOR→REPORTADO, RN-REG-007 incremento.
- Repository tests con mock Pinot/Kafka.

**Frontend:**

- Unit tests `AccidenteApiService` con HttpClientTestingModule.
- Guard tests con roles mock del JWT.

## 5) Criterios de salida

- [ ] Contrato OpenAPI alineado con spec y clarificaciones
- [ ] CU-O21/O32/O40/O41 + RF-REG-010 funcionales vía API
- [ ] Patrón Vista→Servicio→Repositorio respetado
- [ ] Kafka como único canal de escritura verificado
- [ ] Guards Angular operativos por rol
- [ ] CA-REG-001 a CA-REG-014 verificables manualmente o en tests

## 6) Evidencia de performance (RNF-REG-001 / RNF-REG-005)

- Medir p95 de `POST /accidentes` (validaciones incluidas) < 2s en entorno de prueba.
- Registrar tiempo de captura UI objetivo < 5 min (meta operativa OP-3.2.1) en prueba guiada con operador.
