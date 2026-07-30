# Research: Notificación de Prospectos a Ventas

**Feature:** `notificacion-ventas` · **Date:** 2026-07-25  
**Inputs:** spec.md (clarify 2026-07-25), constitution.md, architectural-patterns.md, api-standards.md, project-structure.md, testing.md, `commercial-pipeline-prospects`

---

## Decision 1 — Extender app `ventas_crm` (no crear app nueva)

**Decision:** Implementar O118/O122 en `backend/apps/ventas_crm/` (ya existente por `#04`) y el módulo Angular `ventas-crm`, con vistas/servicios/repositorios adicionales bajo el mismo módulo de negocio.

**Rationale:** `project-structure.md` y `module-map.md` #5 — 1 app Django = 1 módulo Ventas-CRM. Crear `notificacion_ventas` como app separada violaría esa regla.

**Alternatives considered:**
- App Django nueva `notificacion_ventas` — rechazada (rompe 1 app = 1 módulo).
- Meter endpoints en `cuentas_clientes` — rechazada (módulo equivocado).

---

## Decision 2 — Contract-first REST (`api-standards.md`)

**Decision:** OpenAPI primero en `contracts/notificacion-ventas.openapi.yaml`; base `/api/v1/ventas-crm/`; envelopes éxito/error; cursor pagination en listado; Idempotency-Key opcional en `POST .../interacciones` (ráfagas UI).

**Rationale:** Constitution Compatibility (API-First); consistencia con `#04`.

**Alternatives considered:**
- GraphQL / SSE para interacciones — fuera de alcance y de api-standards para este flujo.

---

## Decision 3 — Kafka-only-write; Pinot read-only

**Decision:** Escrituras de dominio solo vía Kafka:
- `Fact_Interaccion_Demo_topic`
- `Fact_NotificacionVentas_topic`
- `Dim_Prospecto_topic` (solo UPDATE de `demo_expiracion` en primer canje)

Lecturas vía `core/repositories/ventas_crm/*` (Pinot Broker).

**Rationale:** `architectural-patterns.md` vinculante.

**Alternatives considered:**
- INSERT/UPDATE directo a Pinot — prohibido.
- Tabla SQL de staging para interacciones — rechazada (duplica canal).

---

## Decision 4 — Grant de demo sin tabla Pinot nueva (HMAC firmado)

**Decision:** En el registro de prospecto (`commercial-pipeline-prospects`), emitir `demo_grant` = token firmado HMAC (p. ej. `base64url(idprospecto).base64url(nonce).sig`) con secreto `DEMO_GRANT_SECRET`.  
Validación en este feature:
- Firma válida + `idprospecto` coincide + prospecto `activo=true`.
- **Primer canje:** `demo_expiracion IS NULL` → fijar `now+30min` ISO-8601 UTC, publicar update `Dim_Prospecto`, emitir session token, INSERT `inicio_sesion`.
- **Resume:** `demo_expiracion` presente y `now < demo_expiracion` → reemitir session token; sin nuevo `inicio_sesion`.
- **Expirada:** rechazo.

No se añade columna ni tabla Pinot; el estado “canjeado” se deriva de `demo_expiracion != NULL`.

**Rationale:** Cumple RN-NV-006 y assumption §16.9 sin expandir las 71 tablas; Maintainability.

**Alternatives considered:**
- Tabla `Fact_DemoGrant` — rechazada (gobernanza de modelo).
- Guardar grant en Redis únicamente — viable como cache, pero la fuente de verdad del ciclo sigue siendo `demo_expiracion` + firma HMAC.

**Handoff `#04`:** extender respuesta de `POST /ventas-crm/prospectos` con `data.demo_grant` (cambio aditivo no breaking del contrato de pipeline; documentado en tasks de este feature como dependencia de coordinación).

---

## Decision 5 — Token de sesión de demo (no JWT RBAC)

**Decision:** Session token = JWT HS256 (o equivalente firmado) con claims `{ typ: "demo_session", idprospecto, exp }` donde `exp` = epoch de `demo_expiracion`. Header: `Authorization: Bearer <demo_session_token>` o `X-Demo-Session: <token>` — **elegido: Bearer con typ distinto** validado por autenticador DRF dedicado `DemoSessionAuthentication` (no SimpleJWT RS256 de usuarios).

**Rationale:** api-authentication — separación clara demo vs usuario; CA-NV-007.

**Alternatives considered:**
- Reusar RS256 de usuarios con rol ficticio — rechazado (mezcla identidades).
- Solo cookie HttpOnly — viable en SPA same-site; Bearer facilita contract tests y mobile web.

---

## Decision 6 — Job Celery beat 60s (evaluación + re-evaluación)

**Decision:** `EvaluacionReglasDemoService` invocado por Celery beat cada 60s:
1. Listar sesiones históricas candidatas (`demo_expiracion ≥ now-7d` con al menos un `inicio_sesion`).
2. Por sesión, agregar eventos en `[inicio_sesion, demo_expiracion)` según RN-NV-003.
3. Si regla cumple y `idusuario` no null y no hay dedup del día UTC → publicar `Fact_NotificacionVentas` + despachar canal.
4. Si `idusuario` null → no insertar (elegible implícito).

**Rationale:** Spec Decisión 1–2; Maintainability vs streaming.

**Alternatives considered:**
- Kafka consumer streaming — rechazado en spec (windowing).
- Evaluar síncrono en cada `POST interacciones` — rechazado (acopla latency UI; agregados temporales incompletos mid-request).

---

## Decision 7 — Canales: email/push vía `core/notificaciones`; slack enum-only

**Decision:** Tras INSERT de notificación, llamar `EmailNotifier` o `PushNotifier`. Si `canal='slack'` → no llamar adaptador; registrar error de canal no disponible en logs (sin fallback silencioso a email). MVP rules solo usan email/push.

**Rationale:** Spec Decisión 4; SOLID I en `core/notificaciones`.

**Alternatives considered:**
- Implementar SlackNotifier ahora — fuera de alcance MVP.
- Mapear slack→SMS — inventaría canal no presente en enum de negocio.

---

## Decision 8 — AuthZ consulta notificaciones

**Decision:** `GET /ventas-crm/notificaciones` con Bearer JWT RS256.  
- `GerenteVentas` / `GerenteCuentasPublicas`: filtro obligatorio `idusuariogerentenotificado = request.user.idusuario`.  
- `Administrador`: sin filtro de dueño; query opcional `idusuario` para filtrar.  
Cursor pagination (`cursor`, `limit`).

**Rationale:** Matriz RBAC spec; api-authentication + patrón `#04`.

---

## Decision 9 — Throttling

**Decision:**
- `POST /demo/sesiones`: throttle IP moderado (p. ej. 20/min) anti-enumeración de grants.
- `POST /demo/interacciones`: **60/min por token de sesión** (scope throttle key = hash del token), RNF-NV-004.

**Rationale:** Spec CA-NV-007; Security.

---

## Decision 10 — Frontend (angular-architect + typescript-expert)

**Decision:** Extender módulo `ventas-crm`:
- Rutas públicas/lazy `demo/` (sin guard JWT; usa DemoSessionTokenInterceptor).
- Ruta autenticada `notificaciones/` con `admin-o-gerente-crm.guard.ts` (reutilizar/extender).
- Servicios tipados `demo-api.service.ts`, `notificacion-api.service.ts` alineados al OpenAPI.
- UI listado: skeleton / empty / error+retry (RNF-NV-005). Sin NgRx obligatorio.

**Rationale:** Consistencia con `#04`; Maintainability.

---

## Tie-Breaker closure

Conflicto latencia (Performance) vs complejidad (Maintainability) en motor de reglas: **Maintainability** gana (job 60s, SLA ≤2 min). Safety N/A. Documentado; Constitution Check → PASS.
