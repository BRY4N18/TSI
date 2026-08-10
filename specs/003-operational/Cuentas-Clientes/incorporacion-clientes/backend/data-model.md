# Data Model - Incorporación de Clientes

**Numeración de CU corregida 2026-08-08** al catálogo vigente (`TSI-Catalogo-CU-RF-RNF.md`; ver `spec.md` Clarifications). "O01" y las menciones de "O12" ligadas a plan/logo/configuración son **capacidades retiradas sin CU vigente** — no confundir con el **CU-O12 vigente** (reenviar invitación).

## Entidades de dominio (lectura Pinot / escritura Kafka)

## 1) Cuenta corporativa (`Dim_Cliente`)

- Primary key: `idcliente`
- Campos relevantes para este módulo:
  - `razon_social` (STRING, requerido)
  - `nombre` (STRING)
  - `tipo` (STRING: `Proveedor` | `Aseguradora` | `Municipio` | `Smart City`; canónico Proveedor vía CU-O09)
  - `nit_identificacion` (STRING, único, inmutable post alta)
  - `fecha_inicio_contrato` (LONG epoch ms, opcional en solicitud)
  - `plan_suscripcion` (STRING, ⛔ no asignado en esta oleada — Suscripciones-Facturación)
  - `logo_url` (STRING, URL Azure Blob — lo setea el **cliente** en O11 `perfil_corporativo` / CU-O13 (spec `gestion-cuentas`); **nunca** el Admin en aprobación)
  - `estado_onboarding` (STRING: `Pendiente` | `En progreso` | `Completado`) — `Pendiente` al aprobar (CU-O10)
  - `estado` (STRING: `Pendiente_Aprobación` | `Activo` | `Rechazado` | `Rechazado_Anulado` | `Dado de baja`)
  - `admin_local_id` (INT → `Dim_Usuarios.idusuario`)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - NIT único (RN-ONB-001).
  - Proveedor: `estado='Pendiente_Aprobación'` en O09; `Activo`/`Rechazado` solo en O10 (RN-ONB-008).
  - Onboarding solo si `estado='Activo'` (RN-ONB-011).
  - Registro directo / config. plan+logo (legado, retirados, sin CU vigente): no canónicos para Proveedor.

## 2) Usuario administrador local (`Dim_Usuarios`)

- Primary key: `idusuario`
- Campos: `gmail` (único RN-ONB-002), `nombres`, `apellidos`, `activo` (true al crear el admin local, en O09 o entrada directa Ventas-CRM CU-O96)
- Vínculo a cuenta: **solo** `Dim_Cliente.admin_local_id` (RN-ONB-007). No existe `Dim_Usuario_Cliente`.

## 3) Credencial (`Dim_Credencial`)

- FK: `idusuario`
- Campos: `contrasena` (hash), `estadocredencial` (`Cambio contraseña` en O01/O12 → `Activo` tras cambio)
- O12: regenera temp password, marca `Cambio contraseña`, envía email.

## 4) Rol de negocio (`Dim_Rol` + `Dim_Usuario_Rol`)

- O09: asignar rol `Cliente` al admin local vía `Dim_Usuario_Rol`.

## 5) Progreso de onboarding (`Fact_Onboarding`)

- Primary key: `id_onboarding`
- FK: `id_cliente` → `Dim_Cliente.idcliente`
- Campos:
  - `etapa` (STRING canónico: `cambio_password` | `perfil_corporativo` | `preferencias` | opcionales por plan)
  - `completado` (BOOLEAN)
  - `fecha_completado` (LONG epoch ms)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - Una fila por etapa completada (RN-ONB-009).
  - Progreso = presencia de filas con `completado=true` (RF-ONB-004).
  - Topic Kafka: `Fact_Onboarding_topic` (añadir a `KAFKA_TOPICS` en settings).

## 6) Preferencias operativas (`Dim_Preferencias_Cliente`)

- Primary key: `id_preferencia`
- FK: `id_cliente` → `Dim_Cliente.idcliente` (1:1)
- **Creada solo** al completar etapa `preferencias` en O11 (RN-ONB-010).
- Campos iniciales según `datos_etapa` del request.
- Topic: `Dim_Preferencias_Cliente_topic`.

## 7) Plan (`Dim_Plan`) — referencia lectura

- Config. plan+logo (legado, retirado, sin CU vigente) persistía `plan_suscripcion` como STRING en `Dim_Cliente` (referencia al plan; catálogo detallado en Suscripciones-Facturacion). Hoy la asignación de plan es responsabilidad de Suscripciones-Facturación.

## Relaciones principales

- `Dim_Cliente.admin_local_id → Dim_Usuarios.idusuario` (único vínculo usuario↔cuenta)
- `Dim_Cliente (1) → (N) Fact_Onboarding` por `id_cliente`
- `Dim_Cliente (1) → (0..1) Dim_Preferencias_Cliente` (0 hasta etapa preferencias)
- `Dim_Usuarios (1) → (1) Dim_Credencial`
- `Dim_Usuarios (N) → (N) Dim_Rol` vía `Dim_Usuario_Rol`

## Transiciones de estado

### Dim_Cliente.estado

- O09 → `Pendiente_Aprobación`
- O10 aprobar → `Activo` (+ `estado_onboarding='Pendiente'`)
- O10 rechazar → `Rechazado`
- O10 anular rechazo → `Rechazado_Anulado` (soft; NIT libre para nuevo O09)
- `Activo` → `Dado de baja` (spec `gestion-cuentas` CU-O16)

### Dim_Cliente.estado_onboarding

- O10 aprobar → `Pendiente`
- Primera `Fact_Onboarding` → `En progreso`
- 3 etapas obligatorias `completado=true` → `Completado`

### Secuencia de etapas (O11)

```
cambio_password → perfil_corporativo → preferencias → [opcionales por plan]
```

## Eventos Kafka (escritura)

| Operación | Topic | Campos clave del payload |
|-----------|-------|--------------------------|
| Registrar cuenta (O09 autorregistro; registro directo legado retirado) | `Dim_Cliente_topic` | `idcliente`, datos corporativos, `admin_local_id`, `estado` |
| Registrar admin (O09; registro directo legado retirado) | `Dim_Usuarios_topic` | `idusuario`, `gmail`, `nombres`, `apellidos`, `activo=true` |
| Credencial (O09 / O12 reenviar invitación) | `Dim_Credencial_topic` | `idusuario`, hash, `estadocredencial` |
| Rol (O09; registro directo legado retirado) | `Dim_Usuario_Rol_topic` | `idusuario`, `idrol` (Cliente) |
| Configurar plan+logo (legado, retirado, sin CU vigente) | `Dim_Cliente_topic` | `plan_suscripcion`, `logo_url`, `estado_onboarding='Pendiente'` |
| Completar etapa O11 | `Fact_Onboarding_topic` | `id_onboarding`, `id_cliente`, `etapa`, `completado=true`, `fecha_completado` |
| Actualizar estado onboarding | `Dim_Cliente_topic` | `estado_onboarding` |
| Etapa preferencias O11 | `Dim_Preferencias_Cliente_topic` | primera inserción con campos de preferencias |
| Etapa perfil O11 | `Dim_Cliente_topic` | `razon_social`, `nombre`, `logo_url` |

## Auditoría (logs, no Pinot)

| Evento | Campos registrados |
|--------|-------------------|
| Registro (O09; registro directo legado retirado) | `idusuario` (admin actor), `idcliente`, `nit`, timestamp |
| Configuración plan+logo (legado, retirado, sin CU vigente) | `idusuario`, `idcliente`, `plan_suscripcion`, timestamp |
| Etapa completada O11 | `idusuario`, `idcliente`, `etapa`, timestamp |
| Reenvío O12 | `idusuario` (actor), `id_usuario` (destino), timestamp |
| Recordatorio RN-ONB-004 | `idcliente`, `admin_local_id`, `evento=reminder`, timestamp |
| Fallo SMTP | `idcliente`, `evento`, `error`, timestamp |

## Validaciones de contrato (resumen)

| Campo | Regla |
|-------|-------|
| `nit_identificacion` | único en Dim_Cliente → 409 |
| `admin_local.gmail` | único en Dim_Usuarios → 409 |
| `tipo` | enum Aseguradora/Municipio/Smart City |
| `etapa` | catálogo canónico RN-ONB-009 |
| `plan_suscripcion` | requerido en config. plan+logo (legado, retirado, sin CU vigente) |
| `logo_url` | HTTPS válida si presente |
| Config. plan+logo sin registro directo previo (ambos legados, retirados) | 404 |
| Etapa fuera de orden | 400 (debe completar anterior) |
| Reenviar invitación usuario ajeno a cuenta | 403 |

## Alineación cross-módulo (gestion-cuentas)

- `CuentaUsuarioRepository` debe dejar de consultar `Dim_Usuario_Cliente` y resolver membresía vía `ClienteRepository.find_by_admin_local(user_id)` y `list` solo admin local hasta que exista modelo multi-usuario.
