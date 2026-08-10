# Especificación: Alta, Configuración y Onboarding Digital de Clientes

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../incorporacion-clientes.md`](../incorporacion-clientes.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B; no duplicar OpenAPI/data-model en FE.


## 1. Objetivo

Permitir que un solicitante (Proveedor, Aseguradora, Municipio o Smart City) se convierta en cliente activo de la plataforma TSI mediante **autorregistro (CU-O09)** → **aprobación Admin (CU-O10)** → **onboarding digital (CU-O11, guardar progreso incluido como RF-O11.2)** con reenvío de invitación (CU-O12) cuando sea necesario.

## 2. Contexto

Tráfico Seguro Integral opera bajo un modelo B2B/B2G. El camino único de alta es el **autorregistro** seguido de **aprobación por el Administrador**. El logo lo carga el propio cliente; la asignación de plan queda fuera de esta oleada (Suscripciones-Facturación).

**Fuente de alineación:** `especificacion-cambios-cuentas-clientes.md` / `especificacion-cambios-implementacion.md` (decisiones 2026-07-24 y **2026-07-25**).

**Casos de uso incluidos (numeración `TSI-Catalogo-CU-RF-RNF.md`, corregida 2026-08-08 — ver Clarifications):**
- **CU-O09: Autorregistro** — Crea `Dim_Cliente` con `estado='Pendiente_Aprobación'`, usuario admin local y credenciales temporales. Cualquier `tipo` válido del modelo.
- **CU-O10: Aprobar, rechazar o anular rechazo** — Admin cambia estado a `Activo` / `Rechazado` / `Rechazado_Anulado`. Tras aprobar, `estado_onboarding='Pendiente'`. Envía email SMTP. **No** carga logo ni plan.
- **CU-O11: Ejecutar onboarding digital** — Etapas en `Fact_Onboarding` (logo en `perfil_corporativo`), **incluye guardar progreso** (RF-O11.2 — no es CU independiente en el catálogo: es un paso sin actor propio, absorbido en CU-O11). Solo si `estado='Activo'`.
- **CU-O12: Reenviar invitación** — Admin o Cliente; UI en solicitudes Admin y wizard onboarding.

**Capacidades retiradas (HTTP 410 / sin ruta FE) — ninguna tiene CU vigente en el catálogo:**
- **Registro directo por el Administrador** (antes rotulado "CU-O01" en este spec) — **retirado**. El equivalente institucional vivo hoy es Ventas y CRM **CU-O96** (entrada directa), que cubre específicamente la venta institucional ya cerrada comercialmente; no es lo mismo que este flujo retirado ni requiere revivirlo.
- **Configuración de plan + logo por el Administrador** (antes rotulado "CU-O12" en este spec, **sin relación** con el CU-O12 vigente de arriba) — **retirado**. Plan → Suscripciones-Facturación; logo → CU-O11 (este spec) / CU-O13 (spec `gestion-cuentas`).

## Clarifications

### Session 2026-08-08 (renumeración a catálogo vigente + decisión SRS)

- Q: ¿Los CU-Oxx de este spec (O14, O16, O02, O09, O08, O01, O12) eran los del catálogo limpio? → A: **No.** Numeración propia previa a la limpieza, sin alias declarado. Renumerado: O14→**O09** (Autorregistro), O16→**O10** (Aprobar/rechazar/anular), O02→**O11** (Onboarding guiado), O08→**O12** (Reenviar invitación). El antiguo O09 (guardar progreso) se absorbió como RF-O11.2, sin CU propio. Los antiguos O01 y O12 (registro directo / config. plan+logo) quedan **sin CU vigente**: eran capacidades retiradas del catálogo viejo, no casos de uso activos.
- Q: ¿El SRS §3.2.2 ("alta directa del Administrador") sigue vigente? → A: **No** — corregido en el SRS (2026-08-08). Esa puerta se trasladó a Ventas y CRM (CU-O96, venta institucional ya cerrada comercialmente, sin aprobación posterior porque el área comercial ya decidió) y es un mecanismo **distinto e independiente** del autorregistro+aprobación de este spec (CU-O09/CU-O10). No se retira CU-O96 ni se fusiona con este flujo.

### Session 2026-07-09

- Q: ¿Cómo se modela la membresía usuario↔cuenta al registrar un cliente (O01)? → A: No existe `Dim_Usuario_Cliente`; la membresía se infiere solo de `Dim_Cliente.admin_local_id`.
- Q: ¿Cuándo debe establecerse `Dim_Cliente.estado='Activo'`? → A: *(Superada)* Solo tras CU-O10 aprobación.
- Q: ¿Cuál es el catálogo canónico de valores `etapa` en `Fact_Onboarding` (CU-O11)? → A: `cambio_password`, `perfil_corporativo`, `preferencias` (+ opcionales por plan).
- Q: ¿Cuándo debe crearse el registro inicial en `Dim_Preferencias_Cliente`? → A: Al completar la etapa `preferencias`.
- Q: ¿Qué política concreta aplican los recordatorios si el onboarding no se completa en 30 días (RN-ONB-004)? → A: Correo semanal al admin local desde el día 30 hasta completar onboarding.

### Session 2026-07-24 (modelo Proveedor)

- Q: ¿Campos extra en autorregistro (capacidad/certificación)? → A: No por ahora.
- Q: ¿Quién carga el logo? → A: El cliente (CU-O11 aquí / CU-O13 en `gestion-cuentas`), nunca el Administrador en O10.
- Q: ¿La aprobación incluye plan/logo? → A: No. Plan → Suscripciones.

### Session 2026-07-25 (cierre gaps)

- Q: ¿Bloquear login hasta `Activo`? → A: **No.** Login permitido; bloquear onboarding / alta unidades / gestión.
- Q: ¿Reintento NIT tras `Rechazado`? → A: **No self-service.** Admin anula a `Rechazado_Anulado` (soft); nuevo O09 = fila nueva; `find_by_nit` ignora `Rechazado_Anulado`.
- Q: ¿Email al aprobar/rechazar? → A: **Sí**, SMTP existente.
- Q: ¿Destino del registro directo (antes "CU-O01")? → A: **Retirado** (410); todos los tipos → O09→O10.
- Q: ¿Pantalla de configuración de plan+logo (antes "CU-O12")? → A: **Retirada** (410 + sin ruta FE); plan en Suscripciones.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Proveedor (solicitante)** | Autorregistrado | Ejecuta O09; tras aprobación ejecuta onboarding (O11). |
| **Administrador** | Aprobador | Aprueba, rechaza o anula (O10); reenvía invitación (O12). **No** gestiona logo ni plan. |
| **Cliente (admin local)** | Ejecutor del onboarding | Completa etapas (O11), incluyendo logo en perfil corporativo. |
| **Sistema** | Facilitador | Guarda progreso (O09), envía credenciales (O12/O09), setea `estado_onboarding` tras aprobación. |

## 4. Requisitos funcionales

### RF-ONB-001: Autorregistro (CU-O09)

El sistema debe permitir al solicitante autorregistrar una cuenta (tipo **Proveedor**, Aseguradora, Municipio o Smart City) en `Dim_Cliente` con los campos existentes del modelo:
- `razon_social`, `nombre`, `tipo`, `nit_identificacion` (único salvo filas `Rechazado_Anulado`), `fecha_inicio_contrato` (opcional).
- Crear admin local, rol Cliente, credenciales temporales, email de invitación.
- `estado = 'Pendiente_Aprobación'`. **No** `Activo`. **No** exigir plan ni logo.
- Membresía = `admin_local_id` (sin tabla intermedia).

### RF-ONB-002: Aprobar, rechazar o anular (CU-O10)

El Administrador debe poder:
1. Listar `Pendiente_Aprobación` y `Rechazado`.
2. **Aprobar:** `estado='Activo'`, `estado_onboarding='Pendiente'`; notificar por email. **No** logo ni plan.
3. **Rechazar:** `estado='Rechazado'`; motivo en auditoría; notificar por email.
4. **Anular rechazo:** `Rechazado` → `Rechazado_Anulado` (soft, sin borrado físico); libera NIT para un nuevo O09 (fila nueva).

### RF-ONB-002b: Configuración de plan+logo por el Administrador — retirado (sin CU vigente)

Endpoints y pantallas responden **410 Gone** / sin ruta. Logo en CU-O11 (este spec) / CU-O13 (spec `gestion-cuentas`). Plan → Suscripciones-Facturación.

### RF-ONB-002c: Registro directo por el Administrador — retirado (sin CU vigente)

`POST /cuentas-clientes` responde **410 Gone**. Alta únicamente vía O09→O10. Equivalente institucional vivo: Ventas y CRM CU-O96.

### RF-ONB-003: Onboarding digital guiado (CU-O11)

**Precondición:** `Dim_Cliente.estado = 'Activo'`. Si está `Pendiente_Aprobación` o `Rechazado`, el sistema rechaza el onboarding (HTTP 403).

El sistema debe guiar al administrador local a través de etapas canónicas en `Fact_Onboarding.etapa`:
1. **`cambio_password`** — cambio de contraseña obligatorio (si aplica).
2. **`perfil_corporativo`** — configuración de perfil corporativo, **incluyendo `logo_url`** (el cliente sube/ubica su logo aquí).
3. **`preferencias`** — umbrales, canales, zonas, destinatarios. Al guardar, el sistema **crea** `Dim_Preferencias_Cliente`.
4. Etapas **opcionales** según plan (cuando exista catálogo de planes).

Las etapas 1–3 son **obligatorias**. `estado_onboarding='Completado'` solo cuando las tres tienen `completado=true`.

### RF-ONB-004: Guardar progreso de onboarding (RF-O11.2, parte de CU-O11)

Sin cambio de mecánica:
- Cada fila de `Fact_Onboarding` con `completado=true` ES el progreso.
- Al reanudar, el sistema consulta etapas completadas y continúa en la siguiente pendiente.

### RF-ONB-005: Reenviar invitación (CU-O12)

Sin cambio de mecánica (temp password → hash en `Dim_Credencial` → `estadocredencial='Cambio contraseña'` → email). Disponible para cuentas en proceso de onboarding post-aprobación.

## 5. Requisitos no funcionales

### RNF-ONB-001: Tiempo de autorregistro
El autorregistro (O09) debe completarse en menos de 3 minutos (interacción de usuario).

### RNF-ONB-002: Disponibilidad del onboarding
El flujo de onboarding debe estar disponible 24/7 y reanudable sin pérdida de datos, **solo** para cuentas `Activo`.

### RNF-ONB-003: Trazabilidad
Toda creación de solicitud (O09), aprobación/rechazo (O10) y reenvío de invitación debe registrarse en logs (`idusuario`, timestamp, estado anterior/nuevo, motivo de rechazo si aplica).

### RNF-ONB-004: Recordatorios de onboarding
Un correo por semana al gmail del `admin_local_id`, a partir del día 30 desde la **aprobación** (O10), mientras `estado='Activo'` y `estado_onboarding` ≠ `Completado`.

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
CU-O12 no requiere tabla de tokens separada.

### RN-ONB-007
No existe tabla intermedia de membresía usuario↔cuenta. Vínculo = `admin_local_id`.

### RN-ONB-008
`Dim_Cliente.estado` y `Dim_Cliente.estado_onboarding` son independientes. Para Proveedor, `estado='Activo'` solo tras O10; el onboarding no arranca antes.

### RN-ONB-009
Valores canónicos de `Fact_Onboarding.etapa`: `cambio_password`, `perfil_corporativo`, `preferencias` (+ opcionales por plan).

### RN-ONB-010
`Dim_Preferencias_Cliente` se crea al completar la etapa `preferencias` en O11 (no en O09 ni O10).

### RN-ONB-011
Cuentas en `Pendiente_Aprobación` o `Rechazado` no pueden completar onboarding ni operar módulos que exijan cliente activo (p. ej. alta de unidades). El **login** sí está permitido.

### RN-ONB-012
El Administrador **no** asigna `logo_url` en O10. El logo lo gestiona el cliente.

### RN-ONB-013
Tras `Rechazado`, solo el Administrador puede anular (`Rechazado_Anulado`). No hay reintento self-service del mismo NIT sin anulación.

## 7. Entradas

### Para autorregistro (CU-O09)
`razon_social`, `nombre`, `tipo`, `nit_identificacion`, `fecha_inicio_contrato` (si aplica), `admin_local_nombres`, `admin_local_apellidos`, `admin_local_gmail`.

### Para aprobación/rechazo/anular (CU-O10)
`idcliente`, decisión (`aprobar`|`rechazar`), `motivo` (requerido si rechazar); o `POST .../anular-rechazo` sin body.

### Para onboarding (CU-O11)
`idcliente`, `etapa`, datos de la etapa (en `perfil_corporativo` incluye logo).

### Para reenviar invitación (CU-O12)
`id_usuario` (o gmail).

## 8. Salidas

- **201 Created — Solicitud creada (O09):** `idcliente`, `estado='Pendiente_Aprobación'`.
- **200 OK — Aprobada (O10):** `idcliente`, `estado='Activo'`, `estado_onboarding='Pendiente'`.
- **200 OK — Rechazada (O10):** `idcliente`, `estado='Rechazado'`.
- **200 OK — Rechazo anulado (O10):** `idcliente`, `estado='Rechazado_Anulado'`.
- **410 Gone — registro directo / configuración de plan+logo (sin CU vigente, ver §1).**
- **200 OK — Etapa completada:** `{ etapa, progreso }`.
- **200 OK — Progreso actual:** `{ etapas_completadas, etapa_actual }`.
- **200 OK — Invitación reenviada:** mensaje de confirmación.
- **400/401/403/409** según validaciones.

## 9. Estados posibles

### Estados de cuenta (`Dim_Cliente.estado`)
- **Pendiente_Aprobación**: creado por O09; espera O10.
- **Activo**: aprobado en O10.
- **Rechazado**: rechazado en O10.
- **Rechazado_Anulado**: soft-anulado por Admin; NIT libre para nuevo O09.
- **Dado de baja**: módulo `gestion-cuentas` (`CU-O16`).

### Estados de onboarding (`Dim_Cliente.estado_onboarding`)
- **Pendiente**: setado al aprobar (O10); onboarding no iniciado.
- **En progreso**: al menos una `Fact_Onboarding` registrada, no todas completas.
- **Completado**: etapas obligatorias con `completado=true`.

### Fact_Onboarding / admin_local_id / Dim_Preferencias_Cliente
Sin cambio estructural respecto a la versión previa del spec (ver Session 2026-07-09).

## 10. Escenarios

### Escenario 1: Autorregistro + aprobación (O09 + O10)
Proveedor se autorregistra → `Pendiente_Aprobación` → Administrador aprueba → `Activo` + `estado_onboarding='Pendiente'` → cliente inicia O11 (incluye logo en `perfil_corporativo`).

### Escenario 2: Rechazo + anulación + reintento (O10)
Solicitud → Admin rechaza con motivo → `Rechazado` → email → Admin anula → `Rechazado_Anulado` → nuevo O09 con mismo NIT → fila nueva `Pendiente_Aprobación`.

### Escenario 3: Onboarding con progreso (CU-O11, incluye RF-O11.2)
Cliente `Activo` completa `cambio_password` → cierra sesión → al reanudar continúa en `perfil_corporativo` (sube logo) → luego `preferencias`.

### Escenario 4: Reenviar invitación (O12)
Admin desde solicitudes (pendiente) o Cliente desde wizard → temp password → email.

## 11. Criterios de aceptación

### CA-ONB-001
Un solicitante puede autorregistrar (cualquier tipo válido) con `estado='Pendiente_Aprobación'` (O09).

### CA-ONB-002
El Administrador puede aprobar (`Activo` + `estado_onboarding='Pendiente'`) o rechazar (`Rechazado`) con email, sin setear logo ni plan (O10).

### CA-ONB-003
El cliente puede completar onboarding solo si `estado='Activo'`; en `perfil_corporativo` puede establecer `logo_url` (O11).

### CA-ONB-004
El sistema guarda progreso automáticamente vía `Fact_Onboarding` (RF-O11.2, parte de CU-O11).

### CA-ONB-005
Al reanudar, el sistema retoma desde la última etapa incompleta.

### CA-ONB-006
Administrador/Cliente puede reenviar invitación (O12) desde UI operativa (solicitudes / wizard).

### CA-ONB-007
Si `estado_onboarding` ≠ `Completado` tras 30 días desde la aprobación, correo semanal de recordatorio al admin local.

### CA-ONB-008
Cuentas `Pendiente_Aprobación` o `Rechazado` no pueden ejecutar onboarding ni alta de unidades; el login sí está permitido.

### CA-ONB-009
Admin puede anular `Rechazado` → `Rechazado_Anulado`; un nuevo O09 con el mismo NIT crea una fila nueva.

### CA-ONB-010
`POST /cuentas-clientes` (registro directo) y `PATCH .../configuracion` (plan+logo) responden **410 Gone** — ninguno de los dos tiene CU vigente en el catálogo.

### CA-ONB-011
Las pantallas canónicas (autorregistro, solicitudes Admin, onboarding) usan `templateUrl` HTML separado y tokens del design system TSI (`bg-bg-page` / `bg-bg-surface` / `text-text-*` / `accent-primary` / alertas semánticas). Feedback vía `NotificationService` (Toast host), íconos Tabler, acciones primarias con área mínima ~44px (`min-h-11`), y rechazo con modal de confirmación (motivo obligatorio; sin `window.prompt`). Tras O09 exitoso se muestra estado **Solicitud en revisión**.

## 12. Dependencias

- **autenticacion-y-rbac**: `Dim_Usuarios`, `Dim_Credencial`, `Dim_Rol`, `Dim_Usuario_Rol`, JWT.
- **Requerido por:** `alta-unidades` (solo Proveedor con cuenta `Activo` gestiona unidades), `gestion-cuentas` (perfil/logo posterior).

## 13. Fuera de alcance

- Asignación de plan de suscripción / catálogo de severidad (Suscripciones-Facturación).
- Portal público de planes (Ventas-CRM).
- Facturación y cobros.
- Campos extendidos de capacidad/certificación del proveedor (futuro).
- Personalización avanzada del portal del cliente.
