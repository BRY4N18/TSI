# Data Model: Notificación de Prospectos a Ventas

**Feature:** `notificacion-ventas` · **Date:** 2026-07-25  
**Fuente de esquema:** `.specify/docs/architecture/data-model.md` (espejo tablas.json). Este documento fija ownership, validaciones y topics.

## Ownership

| Tabla | Rol de este spec |
|-------|------------------|
| `Fact_Interaccion_Demo` | **Dueño** (escritor original vía Kafka) |
| `Fact_NotificacionVentas` | **Dueño** (escritor original vía Kafka) |
| `Dim_Prospecto` | Co-escritor parcial: solo `demo_expiracion` en primer canje; lectura de `idusuario`, `activo` |
| `Dim_Usuarios` / roles | Lectura (destinatario + RBAC consulta) — `autenticacion-y-rbac` |

**No escribe:** `Fact_Pipeline`, `Fact_Asignacion`, `Dim_Cliente`.

**No modela en Pinot:** `estado_envio`, tabla de grants, cola de pendientes.

## Entities

### Fact_Interaccion_Demo

| Field | Type | Rules |
|-------|------|-------|
| idinteraccion | INT PK | Generado en servicio/repo antes de publicar |
| idprospecto | INT | FK lógico → Dim_Prospecto; debe coincidir con session token |
| tipo_evento | STRING | Enum cerrado: `click` \| `tiempo_seccion` \| `inicio_sesion` \| `fin_sesion` |
| seccion | STRING | ej. `precios`, `pricing`, `mapa_accidentes`, `dashboard` |
| metadata | STRING | JSON; para `tiempo_seccion` MUST incluir `duracion_ms` (int ≥ 0) |
| timestamp_evento | LONG epoch ms | Columna de tiempo Pinot |
| fecha_actualizacion | LONG epoch ms | |

**Kafka:** `Fact_Interaccion_Demo_topic`

### Fact_NotificacionVentas

| Field | Type | Rules |
|-------|------|-------|
| idnotificacion | INT PK | |
| id_prospecto | INT | Nombre con underscore (esquema canónico) |
| idinteraccion | INT | Evento disparador puntual de la sesión |
| idusuariogerentenotificado | INT | Copia de `Dim_Prospecto.idusuario` al disparar; never null en fila insertada |
| regladisparada | STRING | Solo `tiempo_seccion_precios_5min` \| `visito_pricing_3x` (MVP) |
| canal | STRING | `email` \| `slack` \| `push`; MVP dispatch solo email/push |
| fechahoranotificacion | LONG epoch ms | Columna de tiempo Pinot |
| fecha_actualizacion | LONG epoch ms | |

**Kafka:** `Fact_NotificacionVentas_topic`  
**Dedup (RN-NV-001):** unique business check por (`id_prospecto`, `regladisparada`, día UTC de `fechahoranotificacion`) antes de publicar.

### Dim_Prospecto (campos tocados)

| Field | Type | Rules en este feature |
|-------|------|------------------------|
| demo_expiracion | STRING | NULL hasta primer canje; luego ISO-8601 UTC absoluto (`now+30min`); no se prolonga |
| idusuario | INT nullable | Solo lectura para destinatario |
| activo | BOOLEAN | Debe ser `true` para abrir/resume demo |

**Kafka (update parcial):** `Dim_Prospecto_topic` — solo cuando se fija `demo_expiracion` la primera vez.

## Session & grant (fuera de Pinot)

| Concepto | Representación |
|----------|----------------|
| `demo_grant` | HMAC firmado emitido en `POST /ventas-crm/prospectos` (#04); payload incluye `idprospecto` |
| Estado canjeado | Derivado: `demo_expiracion IS NOT NULL` |
| Demo session token | JWT/HS256 claims `{ typ: "demo_session", idprospecto, exp }` con `exp` = epoch de `demo_expiracion` |
| Sesión histórica | Intervalo `[timestamp(inicio_sesion), demo_expiracion)` para un ciclo |

## Rule catalog (RN-NV-003)

| regladisparada | Agregación (por sesión histórica) | canal |
|---------------|-----------------------------------|-------|
| `tiempo_seccion_precios_5min` | Σ `duracion_ms` de `tiempo_seccion` + `seccion='precios'` ≥ 300_000 | `email` |
| `visito_pricing_3x` | COUNT eventos con `seccion ∈ {precios, pricing}` ≥ 3 | `push` |

## Evaluation eligibility (RF-NV-003)

```text
sesión elegible si:
  demo_expiracion >= now - 7 days
  AND exists inicio_sesion en Fact_Interaccion_Demo para idprospecto
  AND (al evaluar) Dim_Prospecto.idusuario IS NOT NULL  → puede notificar
  OR idusuario IS NULL → no inserta; permanece implícitamente elegible
```

## State — demo session

```text
demo_expiracion NULL ──(primer canje grant)──→ ACTIVA (now < demo_expiracion)
ACTIVA ──(now >= demo_expiracion)──→ EXPIRADA (sin renovación en este alcance)
ACTIVA ──(resume grant)──→ ACTIVA (nuevo session token; mismo intervalo)
```

## Kafka topics summary

| Topic | Producer | Trigger |
|-------|----------|---------|
| `Fact_Interaccion_Demo_topic` | `ingesta_interaccion_demo_service` / `demo_sesion_service` | POST interacciones; inicio_sesion en primer canje |
| `Dim_Prospecto_topic` | `demo_sesion_service` | Primer canje (set `demo_expiracion`) |
| `Fact_NotificacionVentas_topic` | `evaluacion_reglas_demo_service` | Job 60s cuando regla cumple + destinatario + no dedup |

## Validation rules (service layer)

1. Reject `canal` ∉ {email, slack, push}.
2. Reject interacción si session token inválido / typ≠demo_session / idprospecto mismatch / exp pasado.
3. Reject sesión si grant firma inválida, prospecto inexistente/inactivo, o demo expirada.
4. Never write Fact_Pipeline / Fact_Asignacion from this feature.
5. Slack dispatch → explicit channel-unavailable (no Pinot row required if rule never selects slack in MVP).
