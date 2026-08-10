# Quickstart — Validación Evidencia en Sitio y Disponibilidad de Unidad

Guía de validación end-to-end contract-first para CU-O74, CU-O78 y CU-O77.

## Prerrequisitos

- Spec: `spec.md` (clarificaciones Session 2026-07-09)
- Contrato: `contracts/evidencia-unidad.openapi.yaml`
- Data model: `data-model.md`
- Dependencias: `autenticacion-y-rbac` (JWT + roles), `registro-accidente` (caso activo), `despacho-inteligente` (lectura flota)
- Infra: Kafka productor, Pinot broker lectura, Azure Blob Storage, backend Django, app móvil/Angular

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | UC/RF |
|--------|------|-------|
| `GET` | `/api/v1/accidentes/{idaccidente}/evidencias` | RF-EVI-005 |
| `POST` | `/api/v1/accidentes/{idaccidente}/evidencias/fotos` | RF-EVI-002 |
| `POST` | `/api/v1/accidentes/{idaccidente}/evidencias/notas` | RF-EVI-003 |
| `POST` | `/api/v1/accidentes/{idaccidente}/evidencias/sincronizar` | CU-O77 / RF-EVI-006 |
| `GET` | `/api/v1/unidades-emergencia` | RF-EVI-004 |
| `GET` | `/api/v1/unidades-emergencia/{id}/disponibilidad` | RF-EVI-004 / CA-EVI-002 |
| `GET` | `/api/v1/unidades-emergencia/{id}/historial-estado` | CA-EVI-009 |
| `POST` | `/api/v1/unidades-emergencia/{id}/historial-estado` | CU-O78 / RF-EVI-001 |
| `GET` | `/api/v1/mi-unidad-emergencia/disponibilidad` | RF-EVI-004 |
| `POST` | `/api/v1/mi-unidad-emergencia/disponibilidad` | CU-O78 |
| `GET` | `/api/v1/accidentes/{id}/enriquecimiento` | CU-O75/CU-O76 |
| `PUT` | `/api/v1/accidentes/{id}/enriquecimiento/clima` | RF-EVI-007 |
| `GET/POST` | `/api/v1/accidentes/{id}/enriquecimiento/elementos-fisicos` | RF-EVI-008 |
| `GET/POST` | `/api/v1/accidentes/{id}/enriquecimiento/conductores` | RF-EVI-009 |
| `GET/POST` | `/api/v1/accidentes/{id}/enriquecimiento/implicados` | RF-EVI-010 |
| `PATCH` | `/api/v1/accidentes/{id}/enriquecimiento/implicados/{idimplicado}` | RF-EVI-010 |
| `GET` | `/api/v1/catalogos/periodos-dias` (y climas / físicos / estados-conductor) | CU-O75/CU-O76 |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ data, meta }`
- Envelope error: `{ error, detail, code }`
- Paginación cursor en listados
- `Idempotency-Key` en escrituras
- `Authorization: Bearer <JWT>`

## 2) Validar flujo backend (Vista → Servicio → Repositorio + Kafka + Blob)

### Escenario A — Subida foto en línea (CA-EVI-003)

1. Login como `Técnico de campo`.
2. `POST /api/v1/accidentes/{idaccidente}/evidencias/fotos` multipart con JPEG <10 MB.
3. **Esperado:** HTTP 201, `sincronizado=true`, URL Blob válida, evento en `Dim_EvidenciaFoto_topic`.

### Escenario B — Nota de campo (CA-EVI-005)

1. `POST .../evidencias/notas` con `tipo=Declaración de testigo`.
2. **Esperado:** HTTP 201, evento en `Dim_NotaAccidente_topic`.

### Escenario C — Galería con RBAC (CA-EVI-007)

1. `GET .../evidencias` como Técnico → HTTP 200 con items ordenados por `fechahora` desc.
2. Login como rol sin permiso → HTTP 403.

### Escenario D — Cambio disponibilidad unidad (CA-EVI-001)

1. Login como `Unidad de emergencia`.
2. `POST /api/v1/mi-unidad-emergencia/disponibilidad` con `estadonuevo=Ocupada`.
3. **Esperado:** HTTP 201, `estadoanterior=Activa`, evento `Fact_HistorialEstadoUnidad_topic`.
4. `GET /api/v1/mi-unidad-emergencia/disponibilidad` → `estado_actual=Ocupada`, `incluido_en_despacho=false`.

### Escenario E — Estado por defecto sin historial (CA-EVI-002)

1. Unidad nueva sin filas en historial.
2. `GET .../disponibilidad` como Administrador.
3. **Esperado:** `estado_actual=Fuera de servicio`, `incluido_en_despacho=false`, `fechahora_ultimo_cambio=null`.

### Escenario F — RBAC disponibilidad (RN-EVI-015)

1. Unidad intenta `GET /unidades-emergencia/{otra_id}/disponibilidad` → HTTP 403.
2. Técnico intenta `GET /unidades-emergencia` → HTTP 403.
3. Administrador `GET /unidades-emergencia` → HTTP 200.

### Escenario G — Sync diferida parcial (Escenario 4b)

1. Cliente con 3 ítems locales pendientes.
2. `POST .../evidencias/sincronizar` simulando fallo en 1 foto (timeout Blob).
3. **Esperado:** HTTP 200, `sincronizados=2`, `pendientes=1`; reintento automático en siguiente ciclo completa el tercero.

### Escenario H — Caso inactivo (RN-EVI-006)

1. Caso en estado Cerrado.
2. `POST .../evidencias/notas` → HTTP 422.

### Escenario I — Multi-unidad (CA-EVI-008)

1. Grúa y ambulancia suben evidencia al mismo `idaccidente`.
2. `GET .../evidencias` → ambas visibles sin referencia a `Fact_Despacho`.

## 3) Validar frontend (Angular)

### Servicios

| Servicio | Contrato |
|----------|----------|
| `EvidenciaApiService` | Paths `/accidentes/*/evidencias/*` |
| `DisponibilidadUnidadApiService` | Paths `/unidades-emergencia/*`, `/mi-unidad-emergencia/*` |
| `EvidenciaOfflineStoreService` | IndexedDB local; merge en galería |

### Guards

| Guard | Rutas |
|-------|-------|
| `EvidenciaGalleryGuard` | Técnico, Unidad, Administrador |
| `UnidadEmergenciaDisponibilidadGuard` | Panel disponibilidad unidad |
| `AdministradorFlotaGuard` | Vista flota admin |

### Escenario móvil offline

1. Sin red: capturar 2 fotos → visibles solo en galería local del dispositivo.
2. Otro usuario consulta mismo caso → solo evidencia previamente sincronizada.
3. Reconectar: sync automático → terceros ven nuevas fotos tras HTTP 200 sync.

### Escenario J — Clima/período en sitio (CA-EVI-010)

1. Técnico abre `/evidencia-unidad/accidentes/{id}/enriquecimiento`.
2. Selecciona período y clima → `PUT .../enriquecimiento/clima` → HTTP 200.
3. `GET .../enriquecimiento` refleja el puente activo único (RN-EVI-017).

### Escenario K — Elementos físicos (CA-EVI-011)

1. Agregar elemento desde catálogo → `POST .../elementos-fisicos`.
2. Soft-delete con `PATCH .../{id}` `{ activo: false }` → deja de listarse.

### Escenario L — Conductores/vehículos (CA-EVI-012)

1. Registrar conductor + vehículo; reutilizar misma identificación (RN-EVI-019).
2. Consulta lista enriquecida incluye `conductor` y `vehiculo`.

### Escenario N — Implicados no conductores (RF-EVI-010)

1. Técnico registra peatón/pasajero/testigo → `POST .../enriquecimiento/implicados` con `tipoimplicado` + `estadoimplicado` (opc. `genero`/`edad`).
2. `GET .../enriquecimiento` incluye `implicados[]` (solo campos de ontología; sin PII de identidad).
3. Soft-delete `PATCH .../implicados/{id}` `{ activo: false }`.
4. Offline: borrador `LocalImplicado` sin cifrado PII hasta sync CU-O77.

### Escenario M — PII offline cifrado (CA-EVI-013)

1. Sin red: registrar conductor → IndexedDB guarda `ciphertext`/`iv`, no PII en claro.
2. Tras sync OK se borran borradores PII (RN-EVI-021).

## Security — checklist cifrado at-rest (RNF-EVI-009 servidor)

- [ ] TLS en tránsito (API + Kafka SASL/SSL según entorno)
- [ ] Pinot: cifrado at-rest de tablas con PII (`Dim_Conductor`) habilitado en cluster/backups
- [ ] Backups de Pinot/Blob con cifrado y rotación de claves documentada
- [ ] Acceso a PII auditado (`consultar_conductores_accidente`, escrituras)
- [ ] Offline: Web Crypto AES-GCM + clave de sesión; no persistir PII en claro (tests unitarios)

## 4) Criterios de salida

- [ ] Contract tests OpenAPI pasan (evidencia + disponibilidad + **implicados ontología**)
- [ ] CA-EVI-001 a CA-EVI-009 verificados; **CA-EVI-015** (implicado sin PII) verificado
- [ ] Payload Kafka `Dim_Implicado_topic` solo campos de `database/esquemas.json`
- [ ] Offline implicados: sin AES-GCM / sin cédula-nombres en IndexedDB
- [ ] RNF-EVI-003: cambio estado visible en consulta despacho ≤5s
- [ ] RNF-EVI-004: batch sync ≤30s tras reconectar (hasta N ítems razonable en prueba)
- [ ] RNF-EVI-006: consulta estado ≤2s
- [ ] Sin escritura directa a Pinot (solo Kafka + Blob)
- [ ] **No** se modificó `database/esquemas.json` / `tablas.json` por remediación implicado

## 5) Comandos útiles (post-implementación)

```bash
pytest backend/apps/accidentes/tests/api/test_evidencia_contract.py -v
pytest backend/apps/accidentes/tests/api/test_enriquecimiento_implicados_contract.py -v
pytest backend/apps/accidentes/tests/services/test_enriquecimiento_implicado_service.py -v
pytest backend/apps/accidentes/tests/repositories/test_implicado_repository.py -v
pytest backend/apps/despacho/tests/api/test_disponibilidad_contract.py -v
```
