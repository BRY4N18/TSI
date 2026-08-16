# Data Model — Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema.** Los ocho listados leen tablas que ya existen en
`database/esquemas.json` y que produce el módulo operativo de Cuentas y Clientes.

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Dim_Cliente` | Entidad principal | L1, L3 |
| `Fact_Onboarding` | Entidad principal | L2 |
| `Fact_HistorialTransferenciaPropiedad` | Entidad principal | L4 |
| `Dim_Usuarios` | Entidad principal / catálogo | L5, L6, L7, L8 · catálogo en L1, L3, L4 |
| `Dim_Usuario_Rol` | Relación | L5 |
| `Dim_Rol` | Catálogo | L5 |
| `Fact_Session` | Entidad principal | L6 |
| `Dim_Credencial` | Entidad principal | L7 |
| `Dim_UsuariosServidor` | Entidad principal | L8 |
| `Dim_RolesServidor`, `Dim_UsuariosServidorRolesServidor`, `Dim_RolesServidorRoles` | Relación y catálogo | L8 |

Todas de **solo lectura**. Ningún `INSERT`, `UPDATE` ni publicación en Kafka.

---

## 2. Los ocho listados

Notación: **PK** clave primaria · **orden** campo de orden por defecto · **cursor** forma del cursor.

### L1 — Solicitudes de alta pendientes · `FR-001` · OT04 / OP04

- **Tabla:** `Dim_Cliente` · filtro `estado = 'Pendiente'`
- **Campos expuestos:** `idcliente`*, `razon_social`, `tipo`, `fecha_creacion`, `dias_transcurridos`
- **Orden:** `fecha_creacion ASC` (lo más antiguo primero — es una bandeja de trabajo)
- **Cursor:** compuesto `fecha_creacion|idcliente`
- **Filtros:** `tipo`, `dias_minimo`
- **Tipo:** estado actual → **rechaza `desde`/`hasta` con 400** (FR-012)
- **Derivado:** `dias_transcurridos` se calcula en el servicio con reloj inyectable (research D5).
  `dias_minimo` se traduce a fecha de corte y viaja al `WHERE`.

### L2 — Incorporación incompleta · `FR-002` · OT04 / OP05

- **Tabla:** `Fact_Onboarding` · filtro `completado = false`
- **Campos:** `id_onboarding`*, `id_cliente`*, `razon_social`, `etapa`, `fecha_actualizacion`
- **Orden:** `fecha_actualizacion ASC` · **Cursor:** `fecha_actualizacion|id_onboarding`
- **Filtros:** `etapa`, `dias_minimo`
- **Tipo:** estado actual
- **Catálogo:** `id_cliente` → `Dim_Cliente.razon_social`
- **Alcance:** una fila por etapa pendiente existente. **No se infieren etapas ausentes** (research D6).

### L3 — Cuentas por estado · `FR-003` · OT17 / OP07

- **Tabla:** `Dim_Cliente` · sin filtro de estado por defecto
- **Campos:** `idcliente`*, `razon_social`, `tipo`, `estado`, `estado_onboarding`,
  `fecha_inicio_contrato`, `propietario`
- **Orden:** `idcliente DESC` · **Cursor:** escalar `idcliente`
- **Filtros:** `estado`, `tipo`
- **Tipo:** estado actual
- **Catálogo:** `admin_local_id` → `Dim_Usuarios` (nombre del propietario)
- **Regla:** **incluye las cuentas dadas de baja.** La baja es lógica y la fila sobrevive con su
  historial (escenario 2 de la User Story 3). Si `admin_local_id` no resuelve, la fila se devuelve
  con el propietario marcado como no resuelto — **no se omite**.

### L4 — Transferencias de propiedad · `FR-004` · OT17 / CU-O15

- **Tabla:** `Fact_HistorialTransferenciaPropiedad`
- **Campos:** `idhistorialtransferencia`*, `idcliente`*, `razon_social`, `propietario_anterior`,
  `propietario_nuevo`, `fechahora`
- **Orden:** `fechahora DESC` · **Cursor:** `fechahora|idhistorialtransferencia`
- **Filtros:** `desde`, `hasta` (**opcionales**), `idcliente`
- **Tipo:** **hechos del período** — único de los ocho. Omitir el rango devuelve el histórico
  completo paginado (FR-013).
- **Catálogo:** `idusuarioanterior` / `idusuarionuevo` → `Dim_Usuarios`; `idcliente` → `Dim_Cliente`

### L5 — Usuarios y sus roles · `FR-005` · OT18 / OP02

- **Tabla de paginación:** `Dim_Usuarios` — **no** `Dim_Usuario_Rol` (research D4)
- **Campos:** `idusuario`*, `nombres`, `apellidos`, `gmail`, `activo`, `roles[]`
- **Orden:** `idusuario ASC` · **Cursor:** escalar `idusuario`
- **Filtros:** `rol`, `activo`
- **Tipo:** estado actual
- **Resolución:** para los usuarios de la página, `Dim_Usuario_Rol` (activos) → `Dim_Rol.rol`
- **Reglas:** un usuario con dos roles es **una fila con dos roles**, no dos filas. Un usuario **sin
  ningún rol aparece** con `roles: []` (FR-023) — es la anomalía que el Administrador debe ver.
- **Nota:** filtrar por `rol` invierte el orden de consulta (primero la relación, luego los usuarios),
  pero la unidad de paginación sigue siendo el usuario.

> ## ⚠️ Corrección aplicada el 2026-08-15 durante la implementación — L6 y L7
>
> Este documento declaraba **dos literales de estado que no existen en el sistema**. Implementarlos
> al pie de la letra habría dejado los dos listados **vacíos para siempre**, respondiendo `200` con
> `data: []` — sin error, sin aviso, y sin nada que distinga «no hay sesiones abiertas» de «el filtro
> no encaja con ningún valor real».
>
> | Listado | Decía | Valor canónico real | Fuente |
> |---|---|---|---|
> | L6 | `estadosession = 'Activa'` | **`'Inicio sesion'`** | `session_repository.py` |
> | L7 | `estadocredencial = 'Temporal'` | **`'Cambio contraseña'`** | `credential_repository.py` |
>
> No es hipotético: `credential_repository.py:14` documenta que este **mismo fallo ya ocurrió** —un
> seed escribía `"ACTIVA"` mientras el código comparaba contra `"Activo"`, y eso invalidaba la
> credencial de todos los usuarios sembrados—.
>
> **Además, el orden de L7 cambia.** `fecha_solicitud_cambio` existe en el esquema pero **ningún
> escritor la rellena**: `credential_repository` sella `fecha_actualizacion` en cada transición a
> «Cambio contraseña». Un cursor sobre una columna siempre ausente no localiza ninguna fila, así que
> la **segunda página** del listado habría fallado — y solo con datos suficientes para que hubiera
> segunda página, que es como este defecto llega a producción. Se ordena por `fecha_actualizacion`,
> que lleva el dato y significa lo mismo. **El nombre del campo en la respuesta no cambia**: el
> contrato OpenAPI se respeta tal cual.
>
> Los estados **se importan de su módulo canónico** en vez de repetirse como literal, y
> `session_repository` gana las constantes `ESTADO_SESION_ACTIVA/CERRADA/EXPULSADO` que antes eran
> literales sueltos dentro de sus métodos.

### L6 — Sesiones abiertas · `FR-006` · OT18 / CU-O05

- **Tabla:** `Fact_Session` · filtro `estadosession = 'Inicio sesion'` *(ver corrección arriba)*
- **Campos:** `idsession`*, `idusuario`*, `nombre_usuario`, `navegador`, `fechahorainiciosesion`
- **Orden:** `fechahorainiciosesion DESC` · **Cursor:** `fechahorainiciosesion|idsession`
- **Filtros:** `idusuario`
- **Tipo:** estado actual
- **⚠️ Seguridad:** `token` **nunca sale**. Columnas enumeradas, prohibido `SELECT *` (research D7).

### L7 — Credenciales temporales pendientes · `FR-007` · OT18 / CU-O04

- **Tabla:** `Dim_Credencial` · filtro `estadocredencial = 'Cambio contraseña'` *(ver corrección arriba)*
- **Campos:** `idcredencial`*, `idusuario`*, `nombre_usuario`, `gmail`, `fecha_solicitud_cambio`
- **Orden:** `fecha_actualizacion ASC` · **Cursor:** `fecha_actualizacion|idcredencial`
  *(la columna `fecha_solicitud_cambio` no la rellena ningún escritor; el campo de la respuesta
  conserva su nombre y se alimenta de `fecha_actualizacion`)*
- **Tipo:** estado actual
- **⚠️ Seguridad:** `contrasena` **nunca sale**. Columnas enumeradas (research D7).

### L8 — Accesos técnicos de infraestructura · `FR-008` · OT18 / CU-O08

- **Tabla:** `Dim_UsuariosServidor` · filtro `activo = true`
- **Campos:** `idusuarioservidor`*, `idusuario`*, `nombre_usuario`, `usuario`, `roles_servidor[]`,
  `roles_negocio[]`
- **Orden:** `idusuarioservidor ASC` · **Cursor:** escalar
- **Tipo:** estado actual
- **Resolución en cadena:** `Dim_UsuariosServidorRolesServidor` → `Dim_RolesServidor` (rol técnico) →
  `Dim_RolesServidorRoles` → `Dim_Rol` (rol de negocio)
- **⚠️ Seguridad:** `contrasena` **nunca sale**. Columnas enumeradas (research D7).

\* Los identificadores marcados se usan internamente para resolver catálogos y componer el cursor.
**No se muestran en pantalla** (`design-system.md` §8); el consumidor recibe el nombre.

---

## 3. Reglas transversales

**Resolución de catálogo.** Dos consultas y unión en memoria — Pinot no admite JOIN. Es el patrón de
`registro_repository._nombres_calles()`. **No convierte el listado en compuesto**: traduce etiquetas,
no calcula métricas.

**Centinelas.** `core/pinot/client.py:_coerce_value` ya devuelve `None` para `"null"` (STRING), los
mínimos de INT/LONG y los no finitos. **No hace falta código nuevo** (research D3). La prohibición de
`IS NOT NULL` como filtro sigue vigente y es independiente: la coerción ocurre al leer, no al
filtrar.

**Paginación.** Keyset. Se piden `limit + 1` filas; si vuelven más de `limit`, hay página siguiente
y el cursor se compone con la última fila devuelta. Nunca `OFFSET` (research D2).

**Orden determinista.** Todo listado ordena por su campo declarado **más** la clave primaria como
desempate, salvo cuando el campo de orden ya es la clave. Sin esto la paginación repite o salta filas
(SC-005).

**Retraso de ingesta.** 5–15 s entre escritura y visibilidad. Una solicitud recién aprobada puede
seguir apareciendo en L1. **No se compensa**; se documenta.

---

## 4. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|42", "limit": 50, "has_next": true },
    "filtros": { "tipo": "aseguradora", "dias_minimo": 7 }
  }
}
```

`cursor` es `null` cuando no hay página siguiente. `filtros` refleja los filtros **aplicados**, ya
normalizados, para que el consumidor confirme cómo se interpretó su petición.

---

## 5. Resumen

| # | Listado | Tabla principal | Tipo | Cursor | Sensible |
|---|---|---|---|---|:--:|
| L1 | Solicitudes de alta pendientes | `Dim_Cliente` | Estado actual | Compuesto | — |
| L2 | Incorporación incompleta | `Fact_Onboarding` | Estado actual | Compuesto | — |
| L3 | Cuentas por estado | `Dim_Cliente` | Estado actual | Escalar | — |
| L4 | Transferencias de propiedad | `Fact_HistorialTransferenciaPropiedad` | **Período opcional** | Compuesto | — |
| L5 | Usuarios y sus roles | `Dim_Usuarios` | Estado actual | Escalar | — |
| L6 | Sesiones abiertas | `Fact_Session` | Estado actual | Compuesto | ⚠️ `token` |
| L7 | Credenciales temporales | `Dim_Credencial` | Estado actual | Compuesto | ⚠️ `contrasena` |
| L8 | Accesos técnicos | `Dim_UsuariosServidor` | Estado actual | Escalar | ⚠️ `contrasena` |
