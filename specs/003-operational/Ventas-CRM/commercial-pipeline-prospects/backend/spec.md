# Especificación Funcional: Pipeline Comercial y Prospectos

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../commercial-pipeline-prospects.md`](../commercial-pipeline-prospects.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B; no duplicar OpenAPI/data-model en FE.


**Spec:** `commercial-pipeline-prospects` · **Módulo:** Ventas-CRM · **Índice module-map.md:** #4  
**Carpeta:** `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/backend/`  
**Fuente:** `VentasCRM_Pre-venta.md` (Parte 1–3) + `data-model.md` + `actors.md` + `constitution.md` + docs de arquitectura  
**Estado:** Draft clarificado (sesión 2026-07-25) + RF portal planes (2026-07-26)  
**Última actualización:** 2026-07-26

## Clarifications

### Session 2026-07-25

- Q: ¿Qué prospectos puede listar y mutar un Gerente (Ventas / Cuentas Públicas)? → A: Solo los asignados a él (`idusuario` propio); el Administrador ve y opera todos.
- Q: ¿Quién hace la primera asignación manual si el pool automático está vacío (`idusuario=NULL`)? → A: Solo el Administrador; después aplica la regla de dueño.
- Q: ¿Qué hacer si `nit_identificacion` ya existe en `Dim_Cliente` al convertir o en entrada directa? → A: Rechazar si el NIT ya existe en cualquier fila de `Dim_Cliente`.
- Q: ¿Se permiten retrocesos de etapa en el pipeline? → A: No; solo avance adyacente + `Perdido`.
- Q: ¿Cómo resolver escrituras concurrentes sobre el mismo prospecto? → A: Optimistic check — rechazar si etapa/`idusuario` de partida ya no coincide (conflicto; reintentar tras refrescar).

### Session 2026-07-26

- Q: ¿El portal público de planes (antes §15) entra en este embudo? → A: Sí, como **RF-CPP-000**: consulta de solo lectura del catálogo activo (`Dim_Plan`, propiedad de Suscripciones-Facturación), precondición/entrada previa a RF-CPP-001; sin JWT y sin escrituras. Alias documental `CU-O123` **no** es ID canónico en `module-map.md` (pendiente de asignación oficial, igual que los demás alias de fuente).

### Trazabilidad (constitution — Mandatory traceability)

| Tipo | Referencia | Notas |
|---|---|---|
| Módulo / mapa | `module-map.md` #4 Ventas-CRM | Spec canónico del embudo comercial |
| CU canónicos | **O116, O117, O119, O121** | IDs oficiales del mapa; **no** reutilizar O05/O06/O61/O62 de otros módulos |
| Alias de fuente | CU-O05→O116, CU-O62→O117, CU-O06→O119, CU-O64→O121, **CU-O123→(ID canónico a definir)** | Solo trazabilidad al documento `VentasCRM_Pre-venta.md`; CU-O123 **no** figura aún en `module-map.md` |
| Objetivo de negocio | Adquisición comercial operativa (embudo pre-venta → cuenta cliente) | Se introduce formalmente este conjunto de CU operativos bajo Ventas-CRM; no colisiona con la ruta crítica de despacho de emergencias |

### Mapeo CU canónico ↔ requisito

| CU canónico | Alias fuente | Requisitos |
|---|---|---|
| *(ID canónico a definir)* | CU-O123 | **RF-CPP-000** — Portal público / catálogo de planes (solo lectura) |
| **O116** | CU-O05 | RF-CPP-001 — Registro de prospecto |
| **O117** | CU-O62 | RF-CPP-002, RF-CPP-003 — Asignación / reasignación |
| **O119** | CU-O06 | RF-CPP-004, RF-CPP-005 — Transiciones de pipeline / pérdida |
| **O121** | CU-O64 | RF-CPP-006 — Conversión a cliente |
| *(sin CU dedicado en mapa)* | Parte 3 fuente | RF-CPP-007 — Entrada directa sin prospecto |
| *(consulta operativa)* | — | RF-CPP-008 — Consulta de prospectos y pipeline |

---

## 1. Objetivo

Permitir el ciclo de vida comercial completo de un **Prospecto** — desde la **consulta pública del catálogo de planes** (entrada informativa del embudo), pasando por su registro inbound, hasta su conversión en **Cliente** o su pérdida — incluyendo la asignación y reasignación del ejecutivo comercial responsable, el avance auditable por las etapas del pipeline (`Nuevo → Contactado → Calificado → Propuesta → Negociación → Ganado/Perdido`), y la creación de la cuenta de cliente resultante, con historial de solo-inserción que permita reconstruir en cualquier momento quién tuvo el prospecto, cuándo, y por qué etapa pasó.

Incluye la vía de entrada alterna de clientes que nunca pasaron por el embudo (venta institucional / licitación pública).

## 2. Contexto

Un **Cliente** (`Dim_Cliente`) puede originarse de dos formas mutuamente excluyentes:

1. **Vía embudo comercial**: el Visitante consulta el catálogo de planes activos (**RF-CPP-000**), luego puede autorregistrarse como `Dim_Prospecto` (**RF-CPP-001**), se asigna, avanza por el pipeline y se convierte en `Dim_Cliente` con `idprospecto` apuntando a su origen.
2. **Entrada directa**: licitación o venta institucional sin `Dim_Prospecto`. Se crea `Dim_Cliente` con `idprospecto = NULL`.

El **estado del pipeline** vive en `Fact_Pipeline` (historial, nunca se sobrescribe). El **dueño comercial** vive en `Fact_Asignacion` (historial), reflejado en `Dim_Prospecto.idusuario` como valor desnormalizado. Un Prospecto llega a estado terminal (`activo=false`) solo con `motivo_inactividad` explícito: `'perdido'` o `'convertido'`.

El catálogo comercial expuesto en el portal público se lee de `Dim_Plan` (propiedad del módulo **Suscripciones-Facturación**); este spec **no** escribe ni administra planes.

**Fuera de este spec:** eventos de demo (`Fact_Interaccion_Demo`) y notificaciones a ventas (`notificacion-ventas`).

## 3. Actores

| Actor | Tipo | Rol en este spec |
|---|---|---|
| **Visitante** | Externo, sin sesión, sin JWT | Consulta de solo lectura el catálogo de planes activos (**RF-CPP-000**). No escribe datos. Puede continuar al registro (**RF-CPP-001**) y entonces actúa como Prospecto. |
| **Prospecto** | Externo, no autenticado | Se autorregistra vía formulario web público (**O116** / **RF-CPP-001**). Sin sesión RBAC. |
| **Gerente de Ventas** | Interno (`actors.md`) | Reasigna, avanza pipeline y convierte **solo** prospectos con `idusuario` = su id. |
| **Gerente de Cuentas Públicas** | Interno (`actors.md`) | Igual: **solo** prospectos asignados a él. |
| **Administrador** | Interno (`actors.md`) | Entrada directa (`RF-CPP-007`); consulta y opera **todos** los prospectos (sin filtro por dueño). |
| **Sistema** | Interno (`actors.md`) | Ejecuta **solo** la primera asignación automática (**O117** / `RF-CPP-002`) tras el registro. |

**No es actor de este spec:** “supervisor” genérico (no existe en `actors.md`).

### Matriz RBAC (única)

| Requisito | Quién puede ejecutarlo |
|---|---|
| RF-CPP-000 | Visitante / público (sin JWT); solo lectura |
| RF-CPP-001 | Público (sin JWT) + rate limit |
| RF-CPP-002 | Solo Sistema |
| RF-CPP-003 | Primera asignación de huérfano: solo Administrador. Reasignación: Gerente dueño o Administrador |
| RF-CPP-004 / RF-CPP-005 | Gerente dueño del prospecto **o** Administrador |
| RF-CPP-006 | Gerente dueño del prospecto **o** Administrador |
| RF-CPP-007 | Solo Administrador |
| RF-CPP-008 | Gerente: solo los suyos; Administrador: todos |

## 4. Modelo de datos

Tablas propiedad de este spec (espejo de `data-model.md` / `tablas.json`):

### `Dim_Prospecto` — PK `idprospecto`

| Columna | Tipo | Notas |
|---|---|---|
| idprospecto (PK) | INT | |
| nombres, apellidos | STRING | |
| gmail | STRING | Único a nivel de regla de negocio (RN-CPP-001) |
| empresa | STRING | |
| tipo_organizacion | STRING | Vocabulario cerrado: `'Público'` \| `'Privado'` |
| cargo, telefono, como_nos_conocio | STRING | |
| etapa_actual | STRING | Desnormalizado — última fila de `Fact_Pipeline` |
| idusuario | INT | Desnormalizado — última asignación; NULL hasta la primera |
| demo_expiracion | STRING | Propiedad funcional de `notificacion-ventas`; solo referencial aquí |
| activo | BOOLEAN | `false` = terminal |
| motivo_inactividad | STRING | `NULL` \| `'perdido'` \| `'convertido'` |
| valor_estimado | DOUBLE | Opcional |
| fecha_registro, fecha_actualizacion | LONG (EPOCH ms) | |

### `Fact_Asignacion` — PK `idasignacion` · insert-only

| Columna | Tipo | Notas |
|---|---|---|
| idasignacion (PK) | INT | |
| idprospecto | INT | FK → `Dim_Prospecto` |
| idusuariogerenteanterior | INT | NULL en primera asignación |
| idusuariogerenteactual | INT | |
| tipoasignacion | STRING | `'automatica'` \| `'manual'` |
| motivo | STRING | NULL en primera; obligatorio en reasignación |
| fechahoraasignacion, fecha_actualizacion | LONG (EPOCH ms) | |

### `Fact_Pipeline` — PK `id_transicion` · insert-only

| Columna | Tipo | Notas |
|---|---|---|
| id_transicion (PK) | INT | |
| id_prospecto | INT | FK → `Dim_Prospecto` (nombre con guion bajo en esquema legado) |
| etapa_anterior, etapa_nueva | STRING | |
| notas | STRING | Opcional |
| motivo_perdida | STRING | Obligatorio solo si `etapa_nueva='Perdido'`; si no, NULL |
| gerente_id | INT | Quién ejecuta |
| fecha_transicion, fecha_actualizacion | LONG (EPOCH ms) | |

### `Dim_Cliente` — co-escritura (creación inicial)

| Columna | Tipo | Notas en este spec |
|---|---|---|
| idcliente (PK) | INT | |
| idprospecto | INT | NULL solo en entrada directa |
| nombre, razon_social, tipo, nit_identificacion | STRING | Ver mapeo de herencia en RF-CPP-006 |
| plan_suscripcion, logo_url, admin_local_id | STRING/INT | Valores iniciales; formalización en Cuentas-Clientes |
| estado_onboarding | STRING | Valor inicial: `'Pendiente'` |
| estado | STRING | Valor inicial en este spec: `'Activo'` (cuenta ya ganada / creada por Admin) |
| fecha_inicio_contrato, fecha_actualizacion | LONG (EPOCH ms) | |

Este spec es **dueño** de `Dim_Prospecto`, `Fact_Asignacion` y `Fact_Pipeline`. Es **co-escritor** de `Dim_Cliente` (creación). **No** es dueño de `Fact_Interaccion_Demo` (pertenece a `notificacion-ventas`). **No** es dueño de `Dim_Plan` (pertenece a Suscripciones-Facturación); solo lo **lee** en RF-CPP-000.

### `Dim_Plan` — lectura referencial (no propiedad de este spec)

| Columna expuesta al Visitante | Tipo / notas |
|---|---|
| idplan | INT — PK |
| nombre | STRING |
| precio | según esquema de Suscripciones-Facturación |
| limites | límites de uso del plan |
| nivel | STRING — base para derivar severidades desbloqueadas (p. ej. Básico / Profesional / Empresarial → Baja / Media / Alta según reglas del módulo dueño) |
| activo | BOOLEAN — el portal solo lista `activo=true` |

## 5. Requisitos funcionales

### RF-CPP-000 — Consultar catálogo público de planes (alias fuente **CU-O123**; actor: Visitante)

El sistema debe permitir a un **Visitante** externo, **sin autenticación y sin JWT**, consultar en solo lectura el catálogo de planes de suscripción **activos**.

**Posición en el embudo:** es la **precondición / entrada informativa** previa a **RF-CPP-001** (registro de prospecto). No obliga al Visitante a registrarse; no inicia sesión; **no genera ninguna escritura** (ni en `Dim_Plan` ni en tablas de este spec).

**Fuente de datos:** `Dim_Plan` del módulo **Suscripciones-Facturación** (`subscriptions-and-billing` / catálogo administrado allí). Este requisito **solo lee**; la creación, edición o desactivación de planes está fuera de alcance aquí.

**Datos a exponer por plan activo (`activo=true`):**
- `nombre`
- `precio`
- `limites` (límites de uso asociados al plan)
- **severidades desbloqueadas** por plan (derivadas de `Dim_Plan.nivel` / reglas del módulo dueño; p. ej. Básico → Baja; Profesional → Baja+Media; Empresarial → Baja+Media+Alta)

**Comportamiento:**
- `GET` público del catálogo; sin Bearer.
- Filtrar estrictamente planes con `activo=true` (planes desactivados no aparecen).
- Respuesta vacía válida si el catálogo activo está vacío (HTTP 200 + lista vacía), no error de negocio.
- No rate-limit de escritura; puede aplicarse rate limit de lectura defensivo en `/plan` sin alterar la semántica de solo lectura.

**Alias de trazabilidad:** en la fuente documental aparece como CU-O123. **No** está confirmado como ID oficial en `module-map.md`; se trata igual que los demás alias de este documento (ID canónico a definir).

### RF-CPP-001 — Registrarse como prospecto (**O116**, actor: Prospecto)

El sistema debe permitir a un visitante externo, sin autenticación, registrarse como Prospecto.

**Campos obligatorios:** `nombres`, `apellidos`, `gmail`, `empresa`, `tipo_organizacion` (`'Público'` \| `'Privado'`), `cargo`, `telefono`, `como_nos_conocio`.  
**Opcional:** `valor_estimado`.

**Comportamiento:**
- INSERT en `Dim_Prospecto`: `etapa_actual='Nuevo'`, `idusuario=NULL`, `activo=true`, `motivo_inactividad=NULL`, `fecha_registro=now`.
- No escribe `Fact_Asignacion` ni `Fact_Pipeline` en este paso.
- Dispara automáticamente `RF-CPP-002` tras INSERT exitoso.

### RF-CPP-002 — Asignación automática inicial (**O117**, actor: Sistema)

**Entrada:** prospecto recién creado por RF-CPP-001, sin filas previas en `Fact_Asignacion`.

**Regla de routing (cerrada):**
- `tipo_organizacion='Público'` → pool de usuarios con rol Gerente de Cuentas Públicas activos.
- `tipo_organizacion='Privado'` → pool de usuarios con rol Gerente de Ventas activos.
- Selección: el gerente del pool con **menor cantidad** de prospectos con `activo=true` asignados (`Dim_Prospecto.idusuario`). Empate: el de menor `idusuario`.
- Si el pool está vacío: la asignación automática falla de forma controlada; el prospecto permanece con `idusuario=NULL` **sin** fila en `Fact_Asignacion`. La **primera** asignación manual la realiza solo el **Administrador** (ver RF-CPP-003); no se inventa un gerente por defecto.

**Comportamiento:**
- INSERT `Fact_Asignacion`: `idusuariogerenteanterior=NULL`, `tipoasignacion='automatica'`, `motivo=NULL`.
- UPDATE `Dim_Prospecto.idusuario`.

### RF-CPP-003 — Asignación / reasignación manual (**O117**, actores: Gerente dueño o Administrador)

**Dos modos:**

1. **Primera asignación (huérfano):** `activo=true`, `idusuario=NULL`, sin filas previas en `Fact_Asignacion`. **Solo Administrador.** INSERT con `idusuariogerenteanterior=NULL`, `tipoasignacion='manual'`, `motivo` obligatorio (ej. `'pool vacío — asignación inicial'`).
2. **Reasignación:** `activo=true`, ya existe dueño / historial de asignación. Actor = Gerente dueño vigente **o** Administrador. INSERT con `idusuariogerenteanterior` = dueño saliente, `tipoasignacion='manual'`, `motivo` obligatorio.

**Comportamiento común:** UPDATE `Dim_Prospecto.idusuario` al nuevo gerente.  
**Errores:** rechazar si `activo=false`; si un Gerente intenta mutar un prospecto que no le pertenece; si un Gerente intenta la primera asignación de un huérfano; si en reasignación el `idusuario` esperado no coincide con el vigente (RN-CPP-011).

### RF-CPP-004 — Registrar transición de etapa (**O119**, actores: Gerente dueño o Administrador)

**Entrada:** prospecto con `activo=true`.  
**Autorización:** igual que RF-CPP-003 (dueño o Administrador).

**Secuencia válida (estricta, sin saltos ni retrocesos en este alcance):**
`Nuevo → Contactado → Calificado → Propuesta → Negociación`.

Desde cualquier etapa activa (incluida `Nuevo`) también se permite `etapa_nueva='Perdido'` (ver RF-CPP-005). **No** se permiten retrocesos (p. ej. `Negociación` → `Propuesta`).

**Prohibido en este requisito:**
- Saltar etapas hacia adelante (p. ej. `Nuevo` → `Ganado` o `Nuevo` → `Propuesta`).
- Retroceder a una etapa anterior.
- Escribir `etapa_nueva='Ganado'` — **solo** RF-CPP-006 puede producir `Ganado`, en la misma operación de conversión.

**Comportamiento:**
- INSERT `Fact_Pipeline` + UPDATE `Dim_Prospecto.etapa_actual`.
- **Concurrencia (RN-CPP-011):** el request incluye la `etapa_actual` esperada; si no coincide con la vigente → rechazo por conflicto, sin INSERT.

### RF-CPP-005 — Registrar pérdida (**O119**, bifurcación de RF-CPP-004)

**Entrada:** transición con `etapa_nueva='Perdido'` y `motivo_perdida` obligatorio.

**Comportamiento (misma operación que RF-CPP-004):**
- INSERT `Fact_Pipeline` con `motivo_perdida`.
- UPDATE `Dim_Prospecto`: `activo=false`, `motivo_inactividad='perdido'`, `etapa_actual='Perdido'`.

### RF-CPP-006 — Convertir prospecto en cliente (**O121**, actores: Gerente dueño o Administrador)

**Precondición (cerrada):** `activo=true` **y** `etapa_actual='Negociación'`.  
**Autorización:** Gerente dueño (`idusuario` = él) o Administrador.  
No se exige que ya exista una fila `Ganado` previa: la conversión es atómica.

**Comportamiento (transacción lógica única):**
1. INSERT `Fact_Pipeline` con `etapa_nueva='Ganado'`.
2. INSERT `Dim_Cliente` con:
   - `idprospecto` = FK al prospecto
   - `nombre` = concatenación `nombres + ' ' + apellidos`
   - `razon_social` = `empresa`
   - `tipo` = valor **explícito** del request, restringido a `Proveedor` \| `Aseguradora` \| `Municipio` \| `Smart City` (sugerencia UI: `'Público'`→`Municipio`, `'Privado'`→`Aseguradora`; no se fuerza)
   - `nit_identificacion` = valor **obligatorio del request** (no existe en `Dim_Prospecto`)
   - `estado='Activo'`, `estado_onboarding='Pendiente'`
   - `plan_suscripcion`, `logo_url`, `admin_local_id` en valor inicial vacío/NULL según permita el modelo; formalización en Cuentas-Clientes
   - `fecha_inicio_contrato=now`
3. UPDATE `Dim_Prospecto`: `activo=false`, `motivo_inactividad='convertido'`, `etapa_actual='Ganado'`.

**Errores:** rechazar si `activo=false`, si `etapa_actual ≠ 'Negociación'`, si faltan `tipo` / `nit_identificacion`, si ya existe cualquier `Dim_Cliente` con el mismo `nit_identificacion` (RN-CPP-010), o si la `etapa_actual` esperada no coincide (RN-CPP-011).

**Nota:** el Sistema **no** dispara conversión automática en este alcance; la conversión es acción explícita del Gerente.

### RF-CPP-007 — Entrada directa de cliente sin prospecto (Parte 3; actor: Administrador)

**Comportamiento:**
- INSERT `Dim_Cliente` con `idprospecto=NULL`, datos completos de cliente (`nombre`, `razon_social`, `tipo`, `nit_identificacion`), `estado='Activo'`, `estado_onboarding='Pendiente'`, `fecha_inicio_contrato=now`.
- No crea filas en `Dim_Prospecto`, `Fact_Asignacion` ni `Fact_Pipeline`.
- **Error:** rechazar si `nit_identificacion` ya existe en cualquier `Dim_Cliente` (RN-CPP-010).
- Reporting: métricas de conversión de embudo deben filtrar `idprospecto IS NOT NULL`.

### RF-CPP-008 — Consultar prospectos y pipeline

- **Gerente de Ventas / Gerente de Cuentas Públicas:** listan y ven detalle **solo** de prospectos con `Dim_Prospecto.idusuario` = su id (historial de `Fact_Pipeline` y `Fact_Asignacion` incluido). Intentar acceder a un prospecto de otro dueño → rechazo de autorización.
- **Administrador:** lista y ve **todos** los prospectos, sin filtro por dueño.

## 6. Requisitos no funcionales (ISO/IEC 25010:2023)

| ID | Característica | Aplica | Requisito / justificación | Criterio medible |
|---|---|---|---|---|
| RNF-CPP-001 | **Functional Suitability** | Sí | Completar consulta de planes → registro→asignación→pipeline→conversión/pérdida y entrada directa | 100% de CA-CPP-000…012 verificables por prueba de aceptación |
| RNF-CPP-002 | **Security** | Sí | Escrituras autenticadas por rol (matriz §3); endpoints públicos de catálogo (solo lectura) y registro con rate limit | 100% escrituras no públicas con Bearer JWT; registro ≤ **10 req/min por IP**; RF-CPP-000 sin JWT y sin escritura |
| RNF-CPP-003 | **Performance Efficiency** | Sí | Listados y mutaciones dentro de umbrales de `testing.md` | Endpoint completo ≤ 500ms P95; consulta Pinot simple ≤ 100ms P95 |
| RNF-CPP-004 | **Reliability** | Sí | `Fact_Asignacion` / `Fact_Pipeline` insert-only; conflictos concurrentes no dejan estado desincronizado (RN-CPP-011) | 0 UPDATE/DELETE físicos sobre esas tablas; 100% mutaciones concurrentes conflictivas responden rechazo sin doble transición incoherente |
| RNF-CPP-005 | **Interaction Capability** | Sí | Tablero/listado con loading / vacío / error | 100% vistas de datos asíncronos de este módulo con skeleton, vacío accionable y error con reintento |
| RNF-CPP-006 | **Maintainability** | Sí | Cobertura por capa según `testing.md` | Repos ≥85%, Servicios ≥80%, Vistas ≥75% |
| RNF-CPP-007 | **Compatibility** | Sí | API versionada | Contrato estable bajo `/api/v1/`; breaking → `/api/v2/` |
| RNF-CPP-008 | **Flexibility** | N/A | Este spec no introduce despliegue multi-región ni adaptación geográfica del despacho; el pool de gerentes ya cubre escalado de capacidad comercial sin cambiar el modelo | Documentado como N/A |
| RNF-CPP-009 | **Safety** | N/A | No participa en la cadena accidente→despacho→confirmación; un fallo aquí no desvía unidades de emergencia | Documentado como N/A |
| RNF-CPP-010 | Trazabilidad de negocio | Sí | Todo `activo=false` tiene `motivo_inactividad` no nulo | 0 filas `activo=false AND motivo_inactividad IS NULL` |

## 7. Reglas de negocio

- **RN-CPP-001:** `gmail` único en `Dim_Prospecto`. Validación en capa de servicio antes de publicar; rechazo con mensaje específico de duplicado. (Pinot no se asume como enforcer de UNIQUE.)
- **RN-CPP-002:** solo transiciones adyacentes **hacia adelante** en `Nuevo→…→Negociación`, más `*→Perdido`. Sin saltos. Sin retrocesos. Sin `Ganado` fuera de RF-CPP-006.
- **RN-CPP-003:** `motivo_perdida` obligatorio sii `etapa_nueva='Perdido'`; en otro caso NULL.
- **RN-CPP-004:** `activo=false` es terminal — sin nuevas filas en `Fact_Pipeline` ni `Fact_Asignacion`. Sin reactivación en este alcance.
- **RN-CPP-005:** `idprospecto` NULL solo en RF-CPP-007.
- **RN-CPP-006:** primera asignación automática e inmediata tras RF-CPP-001 (RF-CPP-002).
- **RN-CPP-007:** toda asignación/reasignación manual exige `motivo` no nulo (incluida la primera de huérfano).
- **RN-CPP-008:** puede haber varios gerentes activos por segmento; el balanceo de RF-CPP-002 usa menor carga de prospectos activos.
- **RN-CPP-009:** la primera asignación de un prospecto con `idusuario=NULL` (sin historial) solo la ejecuta el Administrador.
- **RN-CPP-010:** `Dim_Cliente.nit_identificacion` debe ser único a nivel de negocio en este spec: conversión (RF-CPP-006) y entrada directa (RF-CPP-007) rechazan si ya existe cualquier fila con el mismo NIT, sin importar `estado`.
- **RN-CPP-011:** mutaciones concurrentes sobre el mismo prospecto usan control optimista: la operación declara la `etapa_actual` (pipeline/conversión/pérdida) o el `idusuario` vigente (reasignación) observados al cargar; si al aplicar ya no coinciden, se rechaza con conflicto y no se inserta fila nueva. El cliente debe refrescar y reintentar.

## 8. Entradas / Salidas

**Entradas:** consulta pública del catálogo de planes (sin body / sin auth); formulario público de registro; decisión de reasignación; transición de etapa; conversión (`tipo`, `nit_identificacion` + id prospecto); alta directa (payload completo de cliente).  
**Salidas:** listado de planes activos (`nombre`, `precio`, `limites`, severidades desbloqueadas); confirmaciones; listados de prospectos; errores de validación/regla de negocio (duplicado, secuencia inválida, terminal, pool vacío, campos faltantes).

## 9. Estados

**`etapa_actual` (activo=true):** `Nuevo` → `Contactado` → `Calificado` → `Propuesta` → `Negociación` (y terminales vía flujo: `Perdido` / `Ganado`).

| activo | motivo_inactividad | Significado |
|---|---|---|
| true | NULL | En curso |
| false | perdido | RF-CPP-005 |
| false | convertido | RF-CPP-006 |

**`Dim_Cliente` al crear desde este spec:** `estado='Activo'`, `estado_onboarding='Pendiente'` (avance posterior = Cuentas-Clientes).

## 10. Escenarios de aceptación

0. **Catálogo de planes OK:** Visitante sin JWT solicita el catálogo → recibe solo planes con `activo=true`, cada uno con `nombre`, `precio`, `limites` y severidades desbloqueadas; **cero** escrituras en `Dim_Plan` ni en tablas de este spec.
0b. **Catálogo vacío:** no hay planes activos → `200` con lista vacía (no error).
0c. **Plan desactivado oculto:** un plan con `activo=false` no aparece en la respuesta pública.
1. **Registro OK:** formulario válido + gmail nuevo → Prospecto `Nuevo` + asignación automática intentada (tras o a continuación del portal de planes, sin exigir selección de plan en este alcance).
2. **Gmail duplicado:** rechazo con mensaje específico de duplicado; sin INSERT.
3. **Asignación automática:** fila `automatica` + `idusuario` del gerente de menor carga del pool correcto.
4. **Pool vacío:** registro OK pero `idusuario` NULL sin `Fact_Asignacion`; solo Administrador puede hacer la primera asignación manual.
5. **Reasignación sin motivo:** rechazo; sin fila en `Fact_Asignacion`.
6. **Salto de etapa:** `Nuevo`→`Propuesta` o `Nuevo`→`Ganado` vía pipeline → rechazo.
6b. **Retroceso de etapa:** `Negociación`→`Propuesta` → rechazo.
7. **Pérdida sin motivo:** rechazo.
8. **Pérdida OK:** `activo=false`, `motivo_inactividad='perdido'`.
9. **Conversión OK desde Negociación:** inserta `Ganado`, crea `Dim_Cliente` con herencia + `nit`/`tipo` del request, prospecto `convertido`.
10. **Conversión desde etapa ≠ Negociación:** rechazo.
11. **Reasignación sobre terminal:** rechazo.
12. **Entrada directa:** `Dim_Cliente` con `idprospecto=NULL` por Administrador.
13. **Gerente no dueño:** acceso a detalle/pipeline/reasignación/conversión de prospecto ajeno → rechazo de autorización; Administrador sí puede.
14. **Gerente intenta asignar huérfano:** rechazo; solo Administrador.
15. **NIT duplicado en conversión o entrada directa:** rechazo; no se crea `Dim_Cliente`.
16. **Conflicto concurrente:** dos mutaciones con etapa/`idusuario` de partida desfasado → la segunda se rechaza; sin INSERT adicional.

## 11. Criterios de aceptación

- **CA-CPP-000:** el portal público lista solo planes `activo=true` con nombre, precio, límites y severidades desbloqueadas, sin JWT y sin escrituras (RF-CPP-000).
- **CA-CPP-001:** registro con campos obligatorios; rechazo de gmail duplicado (RF-CPP-001, RN-CPP-001).
- **CA-CPP-002:** asignación inicial automática inmediata tras registro (RF-CPP-002, RN-CPP-006).
- **CA-CPP-003:** reasignación/primera asignación manual exige `motivo` no nulo; primera de huérfano solo Administrador (RF-CPP-003, RN-CPP-007).
- **CA-CPP-004:** pipeline impide saltos, retrocesos e impide `Ganado` fuera de conversión (RF-CPP-004, RN-CPP-002).
- **CA-CPP-005:** `motivo_perdida` solo y siempre con `Perdido` (RF-CPP-005, RN-CPP-003).
- **CA-CPP-006:** conversión desde `Negociación` hereda contacto/empresa, exige `tipo`+`nit`, y rechaza NIT duplicado (RF-CPP-006, RN-CPP-010).
- **CA-CPP-007:** todo `activo=false` tiene `motivo_inactividad` explícito (RNF-CPP-010).
- **CA-CPP-008:** entrada directa con `idprospecto=NULL` sin filas de embudo; rechaza NIT duplicado (RF-CPP-007, RN-CPP-010).
- **CA-CPP-009:** listado de prospectos ≤ 500ms P95 bajo carga normal (RNF-CPP-003).
- **CA-CPP-010:** un Gerente solo lista/muta prospectos con `idusuario` = su id; el Administrador no tiene ese filtro (RF-CPP-008, matriz §3).
- **CA-CPP-011:** prospecto huérfano (`idusuario=NULL`) solo puede recibir primera asignación manual del Administrador (RF-CPP-002/003).
- **CA-CPP-012:** mutación concurrente con etapa/`idusuario` esperado obsoleto se rechaza sin escribir (RN-CPP-011, RNF-CPP-004).

## 12. Decisiones de diseño (recomendaciones para `/plan`)

### D1 — Validación de secuencia
Validar transiciones en capa de servicio (diccionario de adyacencias). No crear tabla nueva de catálogo: máquina de estados fija y pequeña.

### D2 — Asignación automática
Pool por `tipo_organizacion` + menor carga de prospectos activos (ver RF-CPP-002). Compatible con RN-CPP-008.

### D3 — Único camino a `Ganado`
Solo RF-CPP-006. Evita prospectos “Ganado” sin `Dim_Cliente` y elimina disparadores ambiguos del Sistema.

## 13. Contrato de API (alineado a `api-standards.md`)

Base: `/api/v1/ventas-crm/` · Bearer JWT salvo **catálogo de planes** y **registro** · Paginación por cursor (donde aplique).

| Método | Endpoint | Auth | RF |
|---|---|---|---|
| `GET` | `/planes` | Público (sin JWT); solo lectura | RF-CPP-000 |
| `POST` | `/prospectos` | Público + rate limit 10/min/IP | RF-CPP-001 |
| `GET` | `/prospectos` | Gerente (solo suyos) / Admin (todos) | RF-CPP-008 |
| `GET` | `/prospectos/{idprospecto}` | Gerente dueño / Admin | RF-CPP-008 |
| `PATCH` | `/prospectos/{idprospecto}/asignacion` | Gerente dueño / Admin | RF-CPP-003 |
| `POST` | `/prospectos/{idprospecto}/pipeline` | Gerente dueño / Admin | RF-CPP-004/005 (`Ganado` rechazado) |
| `POST` | `/prospectos/{idprospecto}/conversion` | Gerente dueño / Admin · `Idempotency-Key` obligatorio | RF-CPP-006 |
| `POST` | `/clientes/entrada-directa` | Administrador | RF-CPP-007 |

La primera asignación (RF-CPP-002) es interna (Sistema); no es endpoint público.  
`GET /planes` no acepta mutaciones; cualquier método de escritura sobre planes pertenece a Suscripciones-Facturación.

## 14. Dependencias

- **autenticacion-y-rbac (#01):** JWT y roles Gerente de Ventas / Gerente de Cuentas Públicas / Administrador / Sistema (no aplica a RF-CPP-000 ni al registro público).
- **Suscripciones-Facturación (`subscriptions-and-billing`, #06):** **lectura** de `Dim_Plan` (planes activos: nombre, precio, límites, nivel/severidades) para RF-CPP-000. Este spec **no escribe** en `Dim_Plan` ni en sus tópicos Kafka.
- **Cuentas-Clientes:** onboarding tras `estado_onboarding='Pendiente'`.
- **notificacion-ventas (#05):** depende de este spec (`Dim_Prospecto.idusuario`); no al revés.

## 15. Fuera de alcance

- Reactivación de prospectos terminales.
- `Fact_Interaccion_Demo` y notificaciones (`notificacion-ventas`).
- Administración del catálogo de planes (alta/edición/desactivación de `Dim_Plan`) — pertenece a Suscripciones-Facturación; aquí solo lectura pública (RF-CPP-000).
- Onboarding formal post-conversión (etapas O02+).
- Reportes agregados de tasa de conversión (solo la regla de filtrado).
- Saltos de etapa con “excepción documentada” (excluido del MVP; reabrir solo con mecanismo de auditoría explícito).
- Conversión automática por el Sistema al detectar `Ganado`.
- Obligar al Visitante a seleccionar un plan en el registro (RF-CPP-001) — el portal es informativo; la vinculación formal plan↔cliente ocurre en Suscripciones-Facturación / onboarding.

## 16. Assumptions (defaults adoptados al corregir el analyze)

1. IDs canónicos = O116/O117/O119/O121; alias de fuente solo documentales (incluye **CU-O123** para RF-CPP-000; ID canónico a definir en `module-map.md`).
2. `tipo_organizacion` ∈ {`Público`,`Privado`}.
3. Rate limit registro = 10 req/min/IP.
4. UNIQUE `gmail` enforced en servicio, no en Pinot.
5. Sin saltos de etapa en MVP.
6. `Ganado` solo vía conversión atómica desde `Negociación`.
7. Entrada directa = rol Administrador; cliente nace `Activo` + onboarding `Pendiente`.
8. `nit_identificacion` y `tipo` de cliente se capturan en conversión/alta, no en el prospecto.
9. Safety y Flexibility = N/A con justificación en §6.
10. `Fact_Interaccion_Demo` no pertenece a este spec (corrección vs. `module-map.md` previo).
11. Visibilidad/mutación: Gerente = solo dueño (`idusuario`); Administrador = todos (clarificación 2026-07-25).
12. Huérfanos por pool vacío: primera asignación manual solo Administrador (clarificación 2026-07-25).
13. NIT de cliente único: rechazo si ya existe en cualquier `Dim_Cliente` (clarificación 2026-07-25).
14. Pipeline sin retrocesos: solo avance adyacente + `Perdido` (clarificación 2026-07-25).
15. Concurrencia: optimistic check en mutaciones de pipeline/asignación/conversión (clarificación 2026-07-25).
16. Portal de planes (RF-CPP-000): solo lectura de `Dim_Plan` activos; severidades derivadas de `nivel` según reglas del módulo dueño; sin JWT ni escrituras (clarificación 2026-07-26).
