# Quickstart - Validación de Onboarding y Validación de Región Operativa

Guía de validación end-to-end contract-first para CU-O55, CU-O60, CU-O61 y CU-O62.

## Prerequisitos

- Contrato: `contracts/incorporacion-regional.openapi.yaml`
- Spec y plan en `specs/003-operational/Red-Operativa/incorporacion-regional/`
- Módulo **autenticacion-y-rbac** operativo (login JWT, roles Administrador y Director Tecnológico)
- Un `Dim_EstadoRegion` existente para poblar `idestado` (alta de región nueva)
- App `red_operativa` desplegada (compartida con `alta-unidades`, ya implementada)

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | UC | Rol |
|--------|------|-----|-----|
| GET | `/api/v1/red-operativa/regiones` | — | Administrador / Director Tecnológico |
| GET | `/api/v1/red-operativa/regiones/{id}` | — | Administrador / Director Tecnológico |
| POST | `/api/v1/red-operativa/regiones/validaciones` | O55 | Administrador (ejecuta) / Director Tecnológico (`idusuario` de aprobación) |
| GET | `/api/v1/red-operativa/regiones/{id}/validaciones` | O60 | Administrador / Director Tecnológico |
| POST | `/api/v1/red-operativa/regiones/{id}/rechazo-definitivo` | O60 | Administrador |
| POST | `/api/v1/red-operativa/regiones/{id}/reevaluacion` | O61 | Director Tecnológico |
| POST | `/api/v1/red-operativa/regiones/{id}/despublicacion-automatica` | O62 | Sistema (sin `idusuario`; invocable manual/cron) |

Convenciones (`api-standards.md`): envelope `{data, meta}` / `{error, detail, code}`; `Idempotency-Key` en todo POST de escritura.

**Resultado esperado**: contrato alineado con spec y `data-model.md`.

## 2) Validar flujo backend (Vista → Servicio → Repositorio)

### Escenario A — Validación aprobada en primer intento (O55, CA-REGON-001/002)

1. Login como Director Tecnológico → JWT.
2. `POST /red-operativa/regiones/validaciones` sin `idregionoperativa`, con `idestado`, `nombreregion`, `resultado="Aprobada"` → `200`, región creada con `estadoregion="En_Validación"` y luego actualizada a `"Producción"`.
3. Confirmar fila nueva en `Dim_ValidacionRegion` vía `GET .../validaciones`.

**Resultado esperado**: región visible vía Pinot con `estadoregion="Producción"` tras el evento Kafka.

### Escenario B — Rechazo y reintento (O55 + O60, CA-REGON-003/004)

1. `POST .../validaciones` con `resultado="Rechazada"`, `motivo="Latencia fuera de rango"` → `200`, `estadoregion` permanece `"En_Validación"`.
2. `GET .../{id}/validaciones` → 1 fila con `resultado="Rechazada"`.
3. Reintentar `POST .../validaciones` con el mismo `idregionoperativa` y `resultado="Aprobada"` → `200`, `estadoregion="Producción"`; historial ahora con 2 filas, ninguna sobrescrita.

### Escenario C — Rechazo definitivo (O60, CA-REGON-005)

1. Región con ≥1 rechazo, `estadoregion="En_Validación"`.
2. `POST .../{id}/rechazo-definitivo` → `200`, `activo=false`; `estadoregion` sin cambio (permanece `"En_Validación"`).

### Escenario D — Despublicación manual con casos activos (O61, CA-REGON-006/007)

1. Región en `estadoregion="Producción"` con casos activos en `Fact_Accidente` (módulo Emergencias) sin cierre.
2. Login como Director Tecnológico → JWT.
3. `POST .../{id}/reevaluacion` con `estadoregion="Despublicada"`, `motivo` → `200`.
4. Confirmar que los casos activos siguen consultables/sin cancelar (regla de continuidad, RF-REGON-003) y que un nuevo `Fact_Accidente` en esa región es rechazado por `registro-accidente` (validación cruzada, fuera de este servicio).

### Escenario E — Reactivación desde estado degradado (O55, reingreso — Clarifications)

1. Región en `estadoregion="Despublicada"` (o `"En_Alerta"`).
2. `POST /red-operativa/regiones/validaciones` con el mismo `idregionoperativa` y `resultado="Aprobada"` → `200`, `estadoregion="Producción"`.

### Escenario F — Despublicación automática invocada manualmente (O62, CA-REGON-008)

1. `POST .../{id}/despublicacion-automatica` sobre una región en `"Producción"` o `"En_Alerta"` → `200`, `estadoregion="Despublicada"`, sin `idusuario` asociado.
2. **Nota**: este endpoint no tiene disparador automático conectado a un evento de cero-unidades-activas (RN-REGON-005, sin FK `Dim_UnidadEmergencia ↔ Dim_RegionOperativa`); se valida invocándolo directamente.

### Escenario G — Conflicto: activar sin validación aprobada (409)

1. Intentar transicionar `estadoregion` a `"Producción"` sin ninguna fila `resultado="Aprobada"` en `Dim_ValidacionRegion` para esa región → `409 Conflict`.

## 3) Validar frontend (Angular)

1. Login como Administrador → navegar a `red-operativa/incorporacion-regional/validacion`.
2. Ejecutar protocolo con `resultado="Rechazada"` → confirmar que la UI muestra el historial actualizado sin recargar manualmente.
3. Login como Director Tecnológico → navegar a `red-operativa/incorporacion-regional/reevaluacion`.
4. Despublicar una región en producción → confirmar guard `director-tecnologico.guard.ts` bloquea el acceso a un usuario Administrador sin ese rol.

## Referencias

- Contrato completo: `contracts/incorporacion-regional.openapi.yaml`
- Modelo de datos: `data-model.md`
- Decisiones de diseño: `research.md`
