# Quickstart — Validación Gestión de Tickets de Soporte

Guía de validación end-to-end contract-first para CU-O83, O84-O87, O97, O89, O88 y RF-TIC-001–007.

## Prerrequisitos

- Spec: `spec.md` (clarificaciones Session 2026-07-21)
- Plan: `plan.md`, `research.md`, `data-model.md`
- Contrato: `contracts/gestion-tickets-soporte.openapi.yaml`
- Dependencias: `autenticacion-y-rbac` (roles Cliente, Soporte al cliente, Desarrollador de APIs, Director Tecnológico, Administrador, Supervisor de Soporte), `incorporacion-clientes` (cliente con cuenta activa), `subscriptions-and-billing` (`Fact_Suscripcion`/`idplan` vigente)
- Infra: Kafka productor/consumidor, Pinot broker lectura, job scheduler (cada 1 min, RNF-TIC-001), backend Django, frontend Angular

## 0) Seed ops (catálogo servicios + rol Supervisor)

```powershell
# Contenedor Django (preferido) o host con Kafka publicado
cd backend
$env:DJANGO_SETTINGS_MODULE = "config.settings"
$env:PYTHONPATH = (Get-Location).Path
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
python scripts/seed_catalogos_soporte.py
```

Publica `Dim_Servicio` (3 servicios) y el rol `SupervisorSoporte` (`idrol=10`). Luego:

1. **Obligatorio:** asignar el rol al usuario supervisor en `Dim_Usuario_Rol` (el job de SLA resuelve por rol, no por un ID fijo).
2. **Opcional:** `SOPORTE_SUPERVISOR_USER_ID=<idusuario>` solo si hay *varios* usuarios con ese rol y quieres forzar uno; si no lo defines, se usa el de menor `idusuario`.
3. Verificar: `GET /api/v1/soporte/servicios`.

Tip seed: `SOPORTE_SUPERVISOR_USER_ID=15 python scripts/seed_catalogos_soporte.py` también publica la fila `Dim_Usuario_Rol` para ese usuario.

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | CU/RF |
|--------|------|-------|
| `GET` | `/api/v1/soporte/servicios` | CU-O83 catálogo |
| `GET` | `/api/v1/soporte/tickets` | RF-TIC-007 (dashboard/listado) |
| `POST` | `/api/v1/soporte/tickets` | CU-O83 |
| `GET` | `/api/v1/soporte/tickets/{id_reclamo}` | O84-O87 (detalle + historial) |
| `POST` | `/api/v1/soporte/tickets/{id}/clasificar` | RF-TIC-001 paso 4 (clasificación manual, RN-TIC-003) |
| `POST` | `/api/v1/soporte/tickets/{id}/tomar` | CU-O84-O87 |
| `POST` | `/api/v1/soporte/tickets/{id}/comentarios` | CU-O84-O87 |
| `POST` | `/api/v1/soporte/tickets/{id}/escalar` | CU-O84-O87 (escalado manual) |
| `POST` | `/api/v1/soporte/tickets/{id}/resolver` | CU-O84-O87 |
| `POST` | `/api/v1/soporte/tickets/{id}/confirmar-cierre` | RF-TIC-006 |
| `POST` | `/api/v1/soporte/tickets/{id}/reabrir` | CU-O88 |
| `GET/POST` | `/api/v1/soporte/sla-config` | CU-O97 |
| `PATCH` | `/api/v1/soporte/sla-config/{id}` | CU-O97 |
| `GET` | `/api/v1/soporte/dashboard` | RF-TIC-007 |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ data, meta }`
- Envelope error: `{ error, detail, code }`
- `Idempotency-Key` en escrituras (registro, tomar, reabrir)

**Flujo interno (sin REST):** CU-O89 — job de monitoreo SLA cada 1 minuto, ver `plan.md`/`research.md` Decision 7.

## 2) Validar flujo backend (Vista → Servicio → Repositorio + Kafka)

### Escenario A — Registro con clasificación automática exitosa (CU-O83, Escenario 1 del spec)

1. Cliente con caso de emergencia activo reporta un ticket técnico.
2. **Esperado:** `prioridad='crítico'` automático; `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion` asignados según `idplan` (vía `Fact_Suscripcion`, Decision 5); `Fact_Historial_Ticket` con `tipo_accion='creacion'`.

### Escenario B — Ticket no clasificable (Escenario 2 del spec)

1. Registrar ticket cuyo `asunto`/`descripcion` no coincide con ninguna regla de clasificación (Decision 4).
2. **Esperado:** `idestadosoporte=Pendiente_de_clasificacion`, `idslaconfig=NULL`, `sla_status=NULL`.
3. `POST .../clasificar` con `tipo_incidencia`/`prioridad` manual.
4. **Esperado:** SLA se asigna recién en este paso (RN-TIC-003); `idestadosoporte=Abierto`.

### Escenario C — Ciclo completo y cierre confirmado (Escenario 3 del spec)

1. Agente `POST .../tomar` → `En_progreso`.
2. Agente `POST .../resolver` dentro del plazo de SLA.
3. Cliente `POST .../confirmar-cierre`.
4. **Esperado:** `sla_status='cumplido'`, `idestadosoporte=Cerrado`, `cierreconfirmadocliente=true`.

### Escenario D — Cierre automático por falta de respuesta (Escenario 4 del spec)

1. Ticket en `Resuelto` sin `POST .../confirmar-cierre` durante 5 días (RN-TIC-004).
2. **Esperado:** cierre automático, `cierreconfirmadocliente=false`, `Fact_Historial_Ticket` con `tipo_accion='cierre_automatico_por_vencimiento'`.

### Escenario E — Modificación de SLA sin afectar tickets existentes (Escenario 5 del spec)

1. `PATCH /soporte/sla-config/{id}` sobre una regla vigente del plan "Premium".
2. **Esperado:** fila anterior `activo=false`/`fechavigenciahasta=now`; fila nueva `activo=true`; tickets ya creados conservan su `idslaconfig` original (RN-TIC-006).

### Escenario F — Escalado automático por incumplimiento de SLA (Escenario 6 del spec)

1. Ticket "En_progreso" supera `sla_resolucion` (o `sla_primera_respuesta`, clarificación) sin resolverse.
2. Job de monitoreo ejecuta su ciclo (cada 1 min).
3. **Esperado:** `sla_status='incumplido'`, `idestadosoporte=Escalado`, `id_agente_asignado`=usuario con rol Supervisor de Soporte (Decision 6).

### Escenario G — Reapertura con renovación de SLA (Escenario 7 del spec + clarificación)

1. Ticket `Cerrado`; cliente `POST .../reabrir` con nueva evidencia adjunta.
2. **Esperado:** `idestadosoporte=Reabierto`; `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion` **renovados** contra la configuración vigente actual (Decision 8); historial previo conservado íntegro; `Fact_ArchivosAdjuntosReclamos` con el nuevo adjunto.

### Validaciones transversales

- Ningún repositorio escribe directo a Pinot (solo Kafka).
- Registro de ticket completo en <3s (RNF-TIC-003). Validar con:
  `python -m pytest apps/soporte_cliente/tests/performance/test_registrar_ticket_p95.py -m slow -v`
- Rol `Cliente` nunca recibe `Fact_Historial_Ticket` con `es_nota_interna=true` (RN-TIC-002).
- `Fact_Historial_Ticket` es append-only: ningún UPDATE/DELETE contra esa tabla en ningún flujo.

## 3) Validar consumo frontend (Angular)

| Artefacto | Responsabilidad |
|-----------|-----------------|
| `TicketApiService` | Registro, transiciones, detalle, dashboard |
| `SlaConfigApiService` | CU-O97 |
| `ClienteSoporteGuard` | Rutas de cliente (mis tickets, reabrir) |
| `AgenteSoporteGuard` | Rutas de agente (tomar, comentar, escalar, resolver) |
| `AdministradorSlaGuard` | Configuración de SLA |

Escenarios UI mínimos:

1. Cliente registra ticket con adjuntos y ve estado/SLA en tiempo real de la respuesta.
2. Agente abre **Cola de soporte** (master-detail): filtra por prioridad/estado, selecciona un ticket en la lista, toma/comenta (nota interna oculta al cliente) y resuelve desde el panel de detalle; empty state muestra "No hay tickets pendientes." sin CTA de reembolso ni alta.
3. Cliente confirma cierre o ve reapertura disponible sobre un ticket Cerrado (ruta detalle / mis tickets).
4. Administrador crea/modifica reglas de `Dim_SLAConfig` desde un panel.
5. Dashboard muestra métricas de RF-TIC-007 (tickets por estado; SLA `en riesgo` / `incumplido`; tasa de reapertura).

## 4) Pruebas sugeridas

**Backend:**

- Contract tests por endpoint (`tests/api/test_*_contract.py`) contra OpenAPI.
- Unit tests `ClasificacionAutomaticaService` (reglas por keyword, caso crítico por emergencia activa).
- Unit tests `AsignacionSLAService` (resolución de `idplan` vía `Fact_Suscripcion`, no `Dim_Cliente.plan_suscripcion`).
- Job test O89 (umbral 80%, independencia de `sla_primera_respuesta`/`sla_resolucion`, ejecución cada 1 min).
- Test de reapertura verificando renovación de SLA (Decision 8) y conservación de historial previo.

**Frontend:**

- Unit tests servicios con `HttpClientTestingModule`.
- Guard tests con JWT roles mock.
- Test de ocultamiento de notas internas para rol Cliente en el componente de detalle.

## 5) Criterios de salida

- [ ] Todos los endpoints OpenAPI implementados y contract tests verdes
- [ ] CA-TIC-001–013 verificables manualmente o en integración
- [ ] Job de monitoreo SLA corriendo cada 1 minuto y marcando `en riesgo`/`incumplido` correctamente
- [ ] Angular guards bloquean rutas por rol
- [ ] Ningún repositorio escribe directo a Pinot
- [ ] Notas internas nunca visibles para el rol Cliente (verificado en API, no solo en UI)

Siguiente paso: `/speckit-tasks specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/backend/spec.md`
