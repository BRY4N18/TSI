# Data Model - Incorporación de Clientes

## Entidades de dominio (lectura Pinot / escritura Kafka)

## 1) Cuenta corporativa (`Dim_Cliente`)

- Primary key: `idcliente`
- Campos relevantes para este módulo:
  - `razon_social` (STRING, requerido)
  - `nombre` (STRING)
  - `tipo` (STRING: `Aseguradora` | `Municipio` | `Smart City`, inmutable post O01)
  - `nit_identificacion` (STRING, único, inmutable post O01)
  - `fecha_inicio_contrato` (LONG epoch ms)
  - `plan_suscripcion` (STRING, asignado en O12)
  - `logo_url` (STRING, URL Azure Blob, asignado en O12 u onboarding perfil)
  - `estado_onboarding` (STRING: `Pendiente` | `En progreso` | `Completado`)
  - `estado` (STRING: `Activo` desde O01)
  - `admin_local_id` (INT → `Dim_Usuarios.idusuario`)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - NIT único (RN-ONB-001).
  - `estado='Activo'` en O01; independiente de `estado_onboarding` (RN-ONB-008).
  - `estado_onboarding='Pendiente'` se establece en O12.

## 2) Usuario administrador local (`Dim_Usuarios`)

- Primary key: `idusuario`
- Campos: `gmail` (único RN-ONB-002), `nombres`, `apellidos`, `activo` (true en O01)
- Vínculo a cuenta: **solo** `Dim_Cliente.admin_local_id` (RN-ONB-007). No existe `Dim_Usuario_Cliente`.

## 3) Credencial (`Dim_Credencial`)

- FK: `idusuario`
- Campos: `contrasena` (hash), `estadocredencial` (`Cambio contraseña` en O01/O08 → `Activo` tras cambio)
- O08: regenera temp password, marca `Cambio contraseña`, envía email.

## 4) Rol de negocio (`Dim_Rol` + `Dim_Usuario_Rol`)

- O01: asignar rol `Cliente` al admin local vía `Dim_Usuario_Rol`.

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
- **Creada solo** al completar etapa `preferencias` en O02 (RN-ONB-010).
- Campos iniciales según `datos_etapa` del request.
- Topic: `Dim_Preferencias_Cliente_topic`.

## 7) Plan (`Dim_Plan`) — referencia lectura

- O12 persiste `plan_suscripcion` como STRING en `Dim_Cliente` (referencia al plan; catálogo detallado en Suscripciones-Facturacion).

## Relaciones principales

- `Dim_Cliente.admin_local_id → Dim_Usuarios.idusuario` (único vínculo usuario↔cuenta)
- `Dim_Cliente (1) → (N) Fact_Onboarding` por `id_cliente`
- `Dim_Cliente (1) → (0..1) Dim_Preferencias_Cliente` (0 hasta etapa preferencias)
- `Dim_Usuarios (1) → (1) Dim_Credencial`
- `Dim_Usuarios (N) → (N) Dim_Rol` vía `Dim_Usuario_Rol`

## Transiciones de estado

### Dim_Cliente.estado

- *(creación O01)* → `Activo`
- `Activo` → `Dado de baja` (gestion-cuentas CU-O11, fuera de este módulo)

### Dim_Cliente.estado_onboarding

- *(O01)* → null / sin valor hasta O12
- O12 → `Pendiente`
- Primera `Fact_Onboarding` → `En progreso`
- 3 etapas obligatorias `completado=true` → `Completado`

### Secuencia de etapas (O02)

```
cambio_password → perfil_corporativo → preferencias → [opcionales por plan]
```

## Eventos Kafka (escritura)

| Operación | Topic | Campos clave del payload |
|-----------|-------|--------------------------|
| Registrar cuenta O01 | `Dim_Cliente_topic` | `idcliente`, datos corporativos, `admin_local_id`, `estado='Activo'` |
| Registrar admin O01 | `Dim_Usuarios_topic` | `idusuario`, `gmail`, `nombres`, `apellidos`, `activo=true` |
| Credencial O01/O08 | `Dim_Credencial_topic` | `idusuario`, hash, `estadocredencial` |
| Rol O01 | `Dim_Usuario_Rol_topic` | `idusuario`, `idrol` (Cliente) |
| Configurar O12 | `Dim_Cliente_topic` | `plan_suscripcion`, `logo_url`, `estado_onboarding='Pendiente'` |
| Completar etapa O02 | `Fact_Onboarding_topic` | `id_onboarding`, `id_cliente`, `etapa`, `completado=true`, `fecha_completado` |
| Actualizar estado onboarding | `Dim_Cliente_topic` | `estado_onboarding` |
| Etapa preferencias O02 | `Dim_Preferencias_Cliente_topic` | primera inserción con campos de preferencias |
| Etapa perfil O02 | `Dim_Cliente_topic` | `razon_social`, `nombre`, `logo_url` |

## Auditoría (logs, no Pinot)

| Evento | Campos registrados |
|--------|-------------------|
| Registro O01 | `idusuario` (admin actor), `idcliente`, `nit`, timestamp |
| Configuración O12 | `idusuario`, `idcliente`, `plan_suscripcion`, timestamp |
| Etapa completada O02 | `idusuario`, `idcliente`, `etapa`, timestamp |
| Reenvío O08 | `idusuario` (actor), `id_usuario` (destino), timestamp |
| Recordatorio RN-ONB-004 | `idcliente`, `admin_local_id`, `evento=reminder`, timestamp |
| Fallo SMTP | `idcliente`, `evento`, `error`, timestamp |

## Validaciones de contrato (resumen)

| Campo | Regla |
|-------|-------|
| `nit_identificacion` | único en Dim_Cliente → 409 |
| `admin_local.gmail` | único en Dim_Usuarios → 409 |
| `tipo` | enum Aseguradora/Municipio/Smart City |
| `etapa` | catálogo canónico RN-ONB-009 |
| `plan_suscripcion` | requerido en O12 |
| `logo_url` | HTTPS válida si presente |
| O12 sin O01 previo | 404 |
| Etapa fuera de orden | 400 (debe completar anterior) |
| Reenviar invitación usuario ajeno a cuenta | 403 |

## Alineación cross-módulo (gestion-cuentas)

- `CuentaUsuarioRepository` debe dejar de consultar `Dim_Usuario_Cliente` y resolver membresía vía `ClienteRepository.find_by_admin_local(user_id)` y `list` solo admin local hasta que exista modelo multi-usuario.
