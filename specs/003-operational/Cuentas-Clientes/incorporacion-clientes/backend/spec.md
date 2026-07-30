# Especificación: Alta, Configuración y Onboarding Digital de Clientes

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../incorporacion-clientes.md`](../incorporacion-clientes.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B; no duplicar OpenAPI/data-model en FE.


## 1. Objetivo

Permitir que un solicitante (Proveedor, Aseguradora, Municipio o Smart City) se convierta en cliente activo de la plataforma TSI mediante **autorregistro (CU-O14)** → **aprobación Admin (CU-O16)** → **onboarding digital (CU-O02/O09)** con reenvío de invitación (CU-O08) cuando sea necesario.

## 2. Contexto

Tráfico Seguro Integral opera bajo un modelo B2B/B2G. El camino único de alta es el **autorregistro** seguido de **aprobación por el Administrador**. El logo lo carga el propio cliente; la asignación de plan queda fuera de esta oleada (Suscripciones-Facturación).

**Fuente de alineación:** `especificacion-cambios-cuentas-clientes.md` / `especificacion-cambios-implementacion.md` (decisiones 2026-07-24 y **2026-07-25**).

**Casos de uso incluidos:**
- **CU-O14: Autorregistro** — Crea `Dim_Cliente` con `estado='Pendiente_Aprobación'`, usuario admin local y credenciales temporales. Cualquier `tipo` válido del modelo.
- **CU-O16: Aprobar, rechazar o anular rechazo** — Admin cambia estado a `Activo` / `Rechazado` / `Rechazado_Anulado`. Tras aprobar, `estado_onboarding='Pendiente'`. Envía email SMTP. **No** carga logo ni plan.
- **CU-O02: Ejecutar onboarding digital** — Etapas en `Fact_Onboarding` (logo en `perfil_corporativo`). Solo si `estado='Activo'`.
- **CU-O09: Guardar progreso de onboarding** — Filas de `Fact_Onboarding`.
- **CU-O08: Reenviar invitación** — Admin o Cliente; UI en solicitudes Admin y wizard onboarding.

**Casos de uso retirados (HTTP 410 / sin ruta FE):**
- **CU-O01:** registro Admin con `Activo` inmediato — **retirado**.
- **CU-O12:** Admin configuraba plan + logo — **retirado**. Plan → Suscripciones; logo → O02/O03.

## Clarifications

### Session 2026-07-09

- Q: ¿Cómo se modela la membresía usuario↔cuenta al registrar un cliente (O01)? → A: No existe `Dim_Usuario_Cliente`; la membresía se infiere solo de `Dim_Cliente.admin_local_id`.
- Q: ¿Cuándo debe establecerse `Dim_Cliente.estado='Activo'`? → A: *(Superada)* Solo tras CU-O16 aprobación.
- Q: ¿Cuál es el catálogo canónico de valores `etapa` en `Fact_Onboarding` (CU-O02)? → A: `cambio_password`, `perfil_corporativo`, `preferencias` (+ opcionales por plan).
- Q: ¿Cuándo debe crearse el registro inicial en `Dim_Preferencias_Cliente`? → A: Al completar la etapa `preferencias`.
- Q: ¿Qué política concreta aplican los recordatorios si el onboarding no se completa en 30 días (RN-ONB-004)? → A: Correo semanal al admin local desde el día 30 hasta completar onboarding.

### Session 2026-07-24 (modelo Proveedor)

- Q: ¿Campos extra en autorregistro (capacidad/certificación)? → A: No por ahora.
- Q: ¿Quién carga el logo? → A: El cliente (O02 / O03), nunca el Administrador en O16.
- Q: ¿La aprobación incluye plan/logo? → A: No. Plan → Suscripciones.

### Session 2026-07-25 (cierre gaps)

- Q: ¿Bloquear login hasta `Activo`? → A: **No.** Login permitido; bloquear onboarding / alta unidades / gestión.
- Q: ¿Reintento NIT tras `Rechazado`? → A: **No self-service.** Admin anula a `Rechazado_Anulado` (soft); nuevo O14 = fila nueva; `find_by_nit` ignora `Rechazado_Anulado`.
- Q: ¿Email al aprobar/rechazar? → A: **Sí**, SMTP existente.
- Q: ¿Destino CU-O01? → A: **Retirado** (410); todos los tipos → O14→O16.
- Q: ¿Pantalla O12? → A: **Retirada** (410 + sin ruta FE); plan en Suscripciones.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Proveedor (solicitante)** | Autorregistrado | Ejecuta O14; tras aprobación ejecuta onboarding (O02). |
| **Administrador** | Aprobador | Aprueba, rechaza o anula (O16); reenvía invitación (O08). **No** gestiona logo ni plan. |
| **Cliente (admin local)** | Ejecutor del onboarding | Completa etapas (O02), incluyendo logo en perfil corporativo. |
| **Sistema** | Facilitador | Guarda progreso (O09), envía credenciales (O08/O14), setea `estado_onboarding` tras aprobación. |

## 4. Requisitos funcionales

### RF-ONB-001: Autorregistro (CU-O14)

El sistema debe permitir al solicitante autorregistrar una cuenta (tipo **Proveedor**, Aseguradora, Municipio o Smart City) en `Dim_Cliente` con los campos existentes del modelo:
- `razon_social`, `nombre`, `tipo`, `nit_identificacion` (único salvo filas `Rechazado_Anulado`), `fecha_inicio_contrato` (opcional).
- Crear admin local, rol Cliente, credenciales temporales, email de invitación.
- `estado = 'Pendiente_Aprobación'`. **No** `Activo`. **No** exigir plan ni logo.
- Membresía = `admin_local_id` (sin tabla intermedia).

### RF-ONB-002: Aprobar, rechazar o anular (CU-O16)

El Administrador debe poder:
1. Listar `Pendiente_Aprobación` y `Rechazado`.
2. **Aprobar:** `estado='Activo'`, `estado_onboarding='Pendiente'`; notificar por email. **No** logo ni plan.
3. **Rechazar:** `estado='Rechazado'`; motivo en auditoría; notificar por email.
4. **Anular rechazo:** `Rechazado` → `Rechazado_Anulado` (soft, sin borrado físico); libera NIT para un nuevo O14 (fila nueva).

### RF-ONB-002b: CU-O12 retirado

Endpoints y pantallas O12 responden **410 Gone** / sin ruta. Logo en O02/O03. Plan → Suscripciones-Facturación.

### RF-ONB-002c: CU-O01 retirado

`POST /cuentas-clientes` responde **410 Gone**. Alta únicamente vía O14→O16.

### RF-ONB-003: Onboarding digital guiado (CU-O02)

**Precondición:** `Dim_Cliente.estado = 'Activo'`. Si está `Pendiente_Aprobación` o `Rechazado`, el sistema rechaza el onboarding (HTTP 403).

El sistema debe guiar al administrador local a través de etapas canónicas en `Fact_Onboarding.etapa`:
1. **`cambio_password`** — cambio de contraseña obligatorio (si aplica).
2. **`perfil_corporativo`** — configuración de perfil corporativo, **incluyendo `logo_url`** (el cliente sube/ubica su logo aquí).
3. **`preferencias`** — umbrales, canales, zonas, destinatarios. Al guardar, el sistema **crea** `Dim_Preferencias_Cliente`.
4. Etapas **opcionales** según plan (cuando exista catálogo de planes).

Las etapas 1–3 son **obligatorias**. `estado_onboarding='Completado'` solo cuando las tres tienen `completado=true`.

### RF-ONB-004: Guardar progreso de onboarding (CU-O09)

Sin cambio de mecánica:
- Cada fila de `Fact_Onboarding` con `completado=true` ES el progreso.
- Al reanudar, el sistema consulta etapas completadas y continúa en la siguiente pendiente.

### RF-ONB-005: Reenviar invitación (CU-O08)

Sin cambio de mecánica (temp password → hash en `Dim_Credencial` → `estadocredencial='Cambio contraseña'` → email). Disponible para cuentas en proceso de onboarding post-aprobación.

## 5. Requisitos no funcionales

### RNF-ONB-001: Tiempo de autorregistro
El autorregistro (O14) debe completarse en menos de 3 minutos (interacción de usuario).

### RNF-ONB-002: Disponibilidad del onboarding
El flujo de onboarding debe estar disponible 24/7 y reanudable sin pérdida de datos, **solo** para cuentas `Activo`.

### RNF-ONB-003: Trazabilidad
Toda creación de solicitud (O14), aprobación/rechazo (O16) y reenvío de invitación debe registrarse en logs (`idusuario`, timestamp, estado anterior/nuevo, motivo de rechazo si aplica).

### RNF-ONB-004: Recordatorios de onboarding
Un correo por semana al gmail del `admin_local_id`, a partir del día 30 desde la **aprobación** (O16), mientras `estado='Activo'` y `estado_onboarding` ≠ `Completado`.

## 6. Reglas de negocio

### RN-ONB-001
El NIT debe ser único en `Dim_Cliente` entre filas **no** `Rechazado_Anulado`.

### RN-ONB-002
El gmail del administrador local debe ser único en `Dim_Usuarios`.

### RN-ONB-003
Una cuenta de cliente debe tener al menos un administrador local asignado (`admin_local_id`).

### RN-ONB-004
Recordatorios SMTP semanales post-aprobación según RNF-ONB-004. Fallo de envío → log, sin detener el job.

### RN-ONB-005
La cuenta permanece en el estado de onboarding donde quedó. No se reinicia el progreso.

### RN-ONB-006
CU-O08 no requiere tabla de tokens separada.

### RN-ONB-007
No existe tabla intermedia de membresía usuario↔cuenta. Vínculo = `admin_local_id`.

### RN-ONB-008
`Dim_Cliente.estado` y `Dim_Cliente.estado_onboarding` son independientes. Para Proveedor, `estado='Activo'` solo tras O16; el onboarding no arranca antes.

### RN-ONB-009
Valores canónicos de `Fact_Onboarding.etapa`: `cambio_password`, `perfil_corporativo`, `preferencias` (+ opcionales por plan).

### RN-ONB-010
`Dim_Preferencias_Cliente` se crea al completar la etapa `preferencias` en O02 (no en O14 ni O16).

### RN-ONB-011
Cuentas en `Pendiente_Aprobación` o `Rechazado` no pueden completar onboarding ni operar módulos que exijan cliente activo (p. ej. alta de unidades). El **login** sí está permitido.

### RN-ONB-012
El Administrador **no** asigna `logo_url` en O16. El logo lo gestiona el cliente.

### RN-ONB-013
Tras `Rechazado`, solo el Administrador puede anular (`Rechazado_Anulado`). No hay reintento self-service del mismo NIT sin anulación.

## 7. Entradas

### Para autorregistro (CU-O14)
`razon_social`, `nombre`, `tipo`, `nit_identificacion`, `fecha_inicio_contrato` (si aplica), `admin_local_nombres`, `admin_local_apellidos`, `admin_local_gmail`.

### Para aprobación/rechazo/anular (CU-O16)
`idcliente`, decisión (`aprobar`|`rechazar`), `motivo` (requerido si rechazar); o `POST .../anular-rechazo` sin body.

### Para onboarding (CU-O02)
`idcliente`, `etapa`, datos de la etapa (en `perfil_corporativo` incluye logo).

### Para reenviar invitación (CU-O08)
`id_usuario` (o gmail).

## 8. Salidas

- **201 Created — Solicitud creada (O14):** `idcliente`, `estado='Pendiente_Aprobación'`.
- **200 OK — Aprobada (O16):** `idcliente`, `estado='Activo'`, `estado_onboarding='Pendiente'`.
- **200 OK — Rechazada (O16):** `idcliente`, `estado='Rechazado'`.
- **200 OK — Rechazo anulado (O16):** `idcliente`, `estado='Rechazado_Anulado'`.
- **410 Gone — O01/O12 retirados.**
- **200 OK — Etapa completada:** `{ etapa, progreso }`.
- **200 OK — Progreso actual:** `{ etapas_completadas, etapa_actual }`.
- **200 OK — Invitación reenviada:** mensaje de confirmación.
- **400/401/403/409** según validaciones.

## 9. Estados posibles

### Estados de cuenta (`Dim_Cliente.estado`)
- **Pendiente_Aprobación**: creado por O14; espera O16.
- **Activo**: aprobado en O16.
- **Rechazado**: rechazado en O16.
- **Rechazado_Anulado**: soft-anulado por Admin; NIT libre para nuevo O14.
- **Dado de baja**: módulo gestion-cuentas (`CU-O11`).

### Estados de onboarding (`Dim_Cliente.estado_onboarding`)
- **Pendiente**: setado al aprobar (O16); onboarding no iniciado.
- **En progreso**: al menos una `Fact_Onboarding` registrada, no todas completas.
- **Completado**: etapas obligatorias con `completado=true`.

### Fact_Onboarding / admin_local_id / Dim_Preferencias_Cliente
Sin cambio estructural respecto a la versión previa del spec (ver Session 2026-07-09).

## 10. Escenarios

### Escenario 1: Autorregistro + aprobación (O14 + O16)
Proveedor se autorregistra → `Pendiente_Aprobación` → Administrador aprueba → `Activo` + `estado_onboarding='Pendiente'` → cliente inicia O02 (incluye logo en `perfil_corporativo`).

### Escenario 2: Rechazo + anulación + reintento (O16)
Solicitud → Admin rechaza con motivo → `Rechazado` → email → Admin anula → `Rechazado_Anulado` → nuevo O14 con mismo NIT → fila nueva `Pendiente_Aprobación`.

### Escenario 3: Onboarding con progreso (O02 + O09)
Cliente `Activo` completa `cambio_password` → cierra sesión → al reanudar continúa en `perfil_corporativo` (sube logo) → luego `preferencias`.

### Escenario 4: Reenviar invitación (O08)
Admin desde solicitudes (pendiente) o Cliente desde wizard → temp password → email.

## 11. Criterios de aceptación

### CA-ONB-001
Un solicitante puede autorregistrar (cualquier tipo válido) con `estado='Pendiente_Aprobación'` (O14).

### CA-ONB-002
El Administrador puede aprobar (`Activo` + `estado_onboarding='Pendiente'`) o rechazar (`Rechazado`) con email, sin setear logo ni plan (O16).

### CA-ONB-003
El cliente puede completar onboarding solo si `estado='Activo'`; en `perfil_corporativo` puede establecer `logo_url` (O02).

### CA-ONB-004
El sistema guarda progreso automáticamente vía `Fact_Onboarding` (O09).

### CA-ONB-005
Al reanudar, el sistema retoma desde la última etapa incompleta.

### CA-ONB-006
Administrador/Cliente puede reenviar invitación (O08) desde UI operativa (solicitudes / wizard).

### CA-ONB-007
Si `estado_onboarding` ≠ `Completado` tras 30 días desde la aprobación, correo semanal de recordatorio al admin local.

### CA-ONB-008
Cuentas `Pendiente_Aprobación` o `Rechazado` no pueden ejecutar onboarding ni alta de unidades; el login sí está permitido.

### CA-ONB-009
Admin puede anular `Rechazado` → `Rechazado_Anulado`; un nuevo O14 con el mismo NIT crea una fila nueva.

### CA-ONB-010
`POST /cuentas-clientes` (O01) y `PATCH .../configuracion` (O12) responden **410 Gone**.

### CA-ONB-011
Las pantallas canónicas (autorregistro, solicitudes Admin, onboarding) usan `templateUrl` HTML separado y tokens del design system TSI (`bg-bg-page` / `bg-bg-surface` / `text-text-*` / `accent-primary` / alertas semánticas). Feedback vía `NotificationService` (Toast host), íconos Tabler, acciones primarias con área mínima ~44px (`min-h-11`), y rechazo con modal de confirmación (motivo obligatorio; sin `window.prompt`). Tras O14 exitoso se muestra estado **Solicitud en revisión**.

## 12. Dependencias

- **autenticacion-y-rbac**: `Dim_Usuarios`, `Dim_Credencial`, `Dim_Rol`, `Dim_Usuario_Rol`, JWT.
- **Requerido por:** `alta-unidades` (solo Proveedor con cuenta `Activo` gestiona unidades), `gestion-cuentas` (perfil/logo posterior).

## 13. Fuera de alcance

- Asignación de plan de suscripción / catálogo de severidad (Suscripciones-Facturación).
- Portal público de planes (Ventas-CRM).
- Facturación y cobros.
- Campos extendidos de capacidad/certificación del proveedor (futuro).
- Personalización avanzada del portal del cliente.
