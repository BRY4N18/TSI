# Data Model: Pipeline Comercial y Prospectos

**Feature:** `commercial-pipeline-prospects` · **Date:** 2026-07-25 (rev. 2026-07-26 RF-CPP-000)  
**Fuente de verdad de esquema:** `.specify/docs/architecture/data-model.md` / `tablas.json` / `esquemas.json` del proyecto (espejo). Este documento fija ownership, reglas y transiciones del spec.

## Ownership

| Tabla | Rol de este spec |
|-------|------------------|
| `Dim_Prospecto` | Dueño (CRUD de dominio vía Kafka) |
| `Fact_Asignacion` | Dueño (insert-only) |
| `Fact_Pipeline` | Dueño (insert-only) |
| `Dim_Cliente` | Co-escritor vía `core/repositories/cuentas_clientes/cliente_repository.py` (creación O121 / entrada directa) |
| `Dim_Plan` | **Solo lectura** (RF-CPP-000) — dueño = Suscripciones-Facturación; **no** publicar a `Dim_Plan_topic` desde este módulo |
| `Fact_Interaccion_Demo` | **No** pertenece aquí → `notificacion-ventas` |
| `Dim_Usuarios` / `Dim_Rol` | Lectura (pools, ownership, JWT) — `autenticacion-y-rbac` |

## Entities

### Dim_Prospecto

| Field | Type | Rules |
|-------|------|-------|
| idprospecto | INT PK | Generado en servicio/repo antes de publicar |
| nombres, apellidos | STRING | Required on create |
| gmail | STRING | Required; unique business rule (RN-CPP-001); normalize lower-case before uniqueness check |
| empresa | STRING | Required |
| tipo_organizacion | STRING | Enum: `Público` \| `Privado` |
| cargo, telefono, como_nos_conocio | STRING | Required on create |
| etapa_actual | STRING | See state machine; denormalized |
| idusuario | INT nullable | Owner; NULL = orphan |
| demo_expiracion | STRING | Owned functionally by notificacion-ventas; leave null/unchanged here |
| activo | BOOLEAN | false = terminal |
| motivo_inactividad | STRING nullable | NULL \| `perdido` \| `convertido` |
| valor_estimado | DOUBLE nullable | Optional |
| fecha_registro, fecha_actualizacion | LONG epoch ms | Pinot time column = fecha_actualizacion |

### Fact_Asignacion (append-only)

| Field | Type | Rules |
|-------|------|-------|
| idasignacion | INT PK | |
| idprospecto | INT | FK logical → Dim_Prospecto |
| idusuariogerenteanterior | INT nullable | NULL on first assign |
| idusuariogerenteactual | INT | Required |
| tipoasignacion | STRING | `automatica` \| `manual` |
| motivo | STRING nullable | NULL iff automatica first; required on manual |
| fechahoraasignacion, fecha_actualizacion | LONG | |

### Fact_Pipeline (append-only)

| Field | Type | Rules |
|-------|------|-------|
| id_transicion | INT PK | |
| id_prospecto | INT | Legacy name with underscore |
| etapa_anterior, etapa_nueva | STRING | |
| notas | STRING nullable | |
| motivo_perdida | STRING nullable | Required iff etapa_nueva=`Perdido` |
| gerente_id | INT | Actor human (or admin); Sistema no escribe pipeline en este alcance |
| fecha_transicion, fecha_actualizacion | LONG | |

### Dim_Cliente (create-only from this feature)

| Field | Type | Rules on create here |
|-------|------|----------------------|
| idcliente | INT PK | |
| idprospecto | INT nullable | Set on O121; NULL on entrada directa |
| nombre | STRING | From `nombres + ' ' + apellidos` (conversion) or request (entrada directa) |
| razon_social | STRING | From `empresa` or request |
| tipo | STRING | Enum: `Proveedor` \| `Aseguradora` \| `Municipio` \| `Smart City` |
| nit_identificacion | STRING | Required; unique across all Dim_Cliente (RN-CPP-010) |
| plan_suscripcion, logo_url | STRING nullable | Initial null/empty |
| admin_local_id | INT nullable | Initial null; formalized in Cuentas-Clientes |
| estado_onboarding | STRING | `Pendiente` |
| estado | STRING | `Activo` |
| fecha_inicio_contrato, fecha_actualizacion | LONG | |

### Dim_Plan (read-only projection — RF-CPP-000)

Esquema canónico (architecture data-model): `idplan`, `nombre`, `nivel` (STRING), `limites` (STRING), `activo` (BOOLEAN), `precio` (DOUBLE), `fecha_actualizacion`.

| Field exposed to Visitante | Source | Rules |
|----------------------------|--------|-------|
| idplan | Dim_Plan | PK |
| nombre | Dim_Plan | |
| precio | Dim_Plan | DOUBLE |
| limites | Dim_Plan | STRING en Pinot; API puede devolver string o JSON parseado si el contenido es JSON válido |
| nivel | Dim_Plan | STRING |
| severidades_desbloqueadas | derived | Ver mapa abajo — **no** es columna física |

**Filtro obligatorio:** solo filas con `activo=true`.

**Mapa `nivel` → severidades** (Decision 10 / research.md):

| nivel | severidades_desbloqueadas |
|-------|---------------------------|
| Básico | Baja |
| Profesional | Baja, Media |
| Empresarial | Baja, Media, Alta |

Nivel desconocido → lista vacía de severidades; el plan **sí** se lista.

**Prohibido desde este feature:** INSERT/UPDATE/publish a `Dim_Plan_topic`; desactivar/crear planes.

## State machine — Dim_Prospecto.etapa_actual

```text
Nuevo → Contactado → Calificado → Propuesta → Negociación
  │         │            │            │            │
  └─────────┴────────────┴────────────┴────────────┴──→ Perdido (terminal: activo=false, motivo=perdido)

Negociación ──(RF-CPP-006 only)──→ Ganado (terminal: activo=false, motivo=convertido)
```

- Forward adjacent only; no backward; no skip.
- `Ganado` never via `POST .../pipeline`.

## Funnel entry (informational)

```text
Visitante ──(RF-CPP-000 GET /planes)──→ ve catálogo activo
         └──(opcional CTA)──→ RF-CPP-001 POST /prospectos ──→ … embudo
```

No hay FK Visitante→Plan en este alcance; no se persiste `idplan` en el registro de prospecto.

## Assignment rules

| Event | tipoasignacion | Actor | Notes |
|-------|----------------|-------|-------|
| After O116 | automatica | Sistema | Pool by tipo_organizacion; least load |
| Orphan first assign | manual | Administrador only | idusuario was NULL |
| Reassign | manual | Owner Gerente or Admin | motivo required; optimistic idusuario_esperado |

## Kafka topics

| Topic | Producer service | Trigger |
|-------|------------------|---------|
| `Dim_Prospecto_topic` | registro / asignación / pipeline / conversion | Create + denormalized updates |
| `Fact_Asignacion_topic` | asignacion_automatica / asignacion_manual | Each assign event |
| `Fact_Pipeline_topic` | pipeline / conversion | Each stage event |
| `Dim_Cliente_topic` | conversion / entrada_directa | Client birth |
| `Dim_Plan_topic` | **N/A — no producer in this feature** | Owned by Suscripciones-Facturación |

## Validation summary (service layer)

- Unique gmail (prospect) and unique nit (cliente) before publish.
- Optimistic: `etapa_actual_esperada` / `idusuario_esperado`.
- Terminal prospect: reject assign/pipeline/conversion.
- Conversion precondition: `etapa_actual='Negociación'` AND `activo=true`.
- Public plans: filter `activo=true`; derive severidades; never write `Dim_Plan`.
