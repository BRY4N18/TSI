# Data Model — Informes Tácticos Simples de Partners y API (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema. Ningún cambio en la capa transversal.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Dim_Partner` | Entidad principal | L1 |
| `Dim_CredencialAPI` | Entidad principal | L2 |
| `Fact_HistorialAccesoPartner` | Entidad principal | L3 |
| `Dim_VersionContratoAPI` | Entidad principal | L4 |
| `Dim_Preferencias_Cliente` | Entidad principal | L5 |
| `Dim_Cliente`, `Dim_Usuarios`, `Dim_Servicio` | Catálogos | L1–L5 |

**Tabla deliberadamente NO leída:** el registro de llamadas a la API. Las llamadas rechazadas por
límite ya las cubre la consola existente (research D4), y al no leer esa tabla **la cuestión de
exponer la dirección de origen de cada petición no llega a plantearse**.

---

## 2. Lo que una credencial NO puede decir

| Pregunta | ¿Se responde aquí? |
|---|---|
| ¿Está activa esta credencial? | ✅ L2 |
| ¿En qué entorno? ¿Hasta cuándo? | ✅ L2 |
| **¿Por qué está inactiva?** | ⛔ **No.** El registro de la credencial **no lo contiene** |
| ¿Qué cambios de acceso ha habido, con qué motivo? | ✅ L3 |
| ¿Cuál de esos cambios explica el estado de esta credencial? | ⚠️ **Compuesto** |

Revocación por seguridad, desactivación en cascada por impago y expiración son **indistinguibles** en
la credencial. El propio código lo declara al explicar la reactivación selectiva. Los motivos viven
en la bitácora; unirlos a la credencial exige localizar el último evento relevante por credencial y
volver a cruzar.

**Consecuencia de negocio:** un listado que afirmara el motivo pondría en la misma línea una decisión
de seguridad del partner y un impago administrativo. Reactivar guiándose por él resucitaría una
credencial comprometida.

---

## 3. El eje de acotamiento

| Listado | Columna de titularidad | Acceso |
|---|---|---|
| L1 Partners | `Dim_Partner.idcliente` | Gestores: todos · Partner: el suyo |
| L2 Credenciales | `Dim_CredencialAPI.idcliente` | Gestores: todas · Partner: las suyas |
| L3 Cambios de acceso | vía el partner → `idcliente` | Gestores: todos · Partner: los suyos |
| L4 Versiones del contrato | — | **Solo gestores** |
| L5 Alcance de datos | — | **Solo gestores** |

Se reutiliza `verificar_propiedad`, que **lanza en vez de devolver un booleano** — un `if` olvidado
sería un fallo silencioso de autorización.

> ⚠️ **Limitación heredada** (research D1): la cuenta se resuelve de hecho por administrador local,
> porque la tabla de vínculos no la escribe ningún código. Un usuario de partner que no lo sea
> recibirá una negativa. Ya anotado en el módulo de Soporte.

---

## 4. Los cinco listados

### L1 — Partners · `FR-001` · OT08 / OP26

- **Tabla:** `Dim_Partner`
- **Campos:** `idpartner`*, `cuenta`, `nombre_partner`, `estado_acceso`, `plan_api`,
  `limite_llamadas_mes`, `limite_llamadas_minuto`, `contacto_tecnico`, `fecha_suspension`,
  `motivo_suspension`
- **Orden:** `idpartner DESC` · **Cursor:** escalar
- **Filtros:** `estado`, `plan`, `cuenta`
- **Tipo:** estado actual
- **Acotado por:** `idcliente`

**Seis estados de incorporación** (research D5), **importados del dominio, no copiados**: Registrado,
Plan asignado, Pruebas activo, Pendiente de aprobación, Producción activa, Suspendido.

Un partner **no suspendido** devuelve fecha y motivo de suspensión **ausentes**, no vacíos.

---

### L2 — Credenciales de integración · `FR-002`, `FR-006`, `FR-008` · OT08 / CU-O49

- **Tabla:** `Dim_CredencialAPI`
- **Campos:** `idcredencial`*, `partner`, `nombre_credencial`, `entorno`, `activa`,
  `fecha_creacion`, `fecha_expiracion`, `dias_para_caducar`
- **⛔ No consultado:** el secreto de autenticación, en ninguna de sus formas. **Lista blanca de
  columnas** (research D3): se enumeran las que salen, no se descartan las prohibidas
- **Orden:** `fecha_expiracion ASC` — lo que antes caduca, primero · **Cursor:** compuesto
- **Filtros:** `entorno`, `activa`, `caduca_en_dias`, `partner`
- **Tipo:** estado actual
- **Acotado por:** `idcliente`

**⚠️ `activa` dice si lo está, no por qué no** (research D2). El listado **no incluye** ningún campo
de motivo.

**Las credenciales de pruebas y de producción coexisten**: activar producción no elimina el acceso de
pruebas, así que un partner puede aportar filas de ambos entornos.

`dias_para_caducar` se calcula en el servicio con reloj inyectable; `caduca_en_dias` se traduce a una
fecha de corte que **sí viaja al filtro**, porque la fecha de expiración es una marca de tiempo
numérica (research D7).

---

### L3 — Cambios de acceso · `FR-003`, `FR-007` · OT08/OT09

- **Tabla:** `Fact_HistorialAccesoPartner`
- **Campos:** `idhistorial`*, `partner`, `credencial`, `tipo_cambio`, `estado_anterior`,
  `estado_nuevo`, `motivo`, `ejecutado_por`, `fecha_cambio`
- **Orden:** `fecha_cambio DESC` · **Cursor:** compuesto `fecha_cambio|idhistorial`
- **Filtros:** `desde`, `hasta` (**opcionales**), `tipo_cambio`, `partner`
- **Tipo:** **hechos del período**
- **Acotado por:** el partner

**Aquí sí viven los motivos.** Trece tipos de cambio, **importados del dominio**, entre ellos los dos
que D2 exige distinguir:

| Tipo | Significa |
|---|---|
| `revocacion_credencial` | **Decisión de seguridad del partner** |
| `desactivacion_por_cascada` | **Consecuencia administrativa** de una suspensión |

Son situaciones opuestas y **cada una conserva su tipo propio**.

**La suspensión trae motivo; la reactivación puede no traerlo** (research D6). Es una asimetría
deliberada de la regla —se exige al cortar el acceso, no al devolverlo—, así que el motivo ausente en
una reactivación **no es un dato incompleto**.

---

### L4 — Versiones del contrato de integración · `FR-004` · OT08 / CU-O50

- **Tabla:** `Dim_VersionContratoAPI`
- **Campos:** `idversion`*, `servicio`, `version`, `estado`, `spec_url`, `fecha_publicacion`,
  `fecha_retiro`
- **Orden:** `fecha_publicacion DESC` · **Cursor:** compuesto
- **Filtros:** `estado`, `servicio`
- **Tipo:** estado actual
- **Acceso:** solo gestores

**Las versiones retiradas se incluyen.** Saber qué se retiró y cuándo es parte de la supervisión del
contrato; omitirlas escondería justo lo que hay que vigilar antes de retirar una más.

---

### L5 — Alcance de datos contratado · `FR-005`, `FR-023` · OT10 / OP31

- **Tabla:** `Dim_Preferencias_Cliente`
- **Campos:** `id_preferencia`*, `cuenta`, `zonas_geograficas`, `frecuencia_reportes`,
  `formato_reportes`, `canales_notificacion`, `destinatarios_reportes`
- **Orden:** `id_preferencia DESC` · **Cursor:** escalar
- **Filtros:** `cuenta`, `frecuencia`
- **Tipo:** estado actual
- **Acceso:** solo gestores

**⚠️ Un cliente sin preferencias configuradas se presenta con el alcance ausente**, **nunca** como
acceso ilimitado (FR-023). De las dos lecturas posibles de un dato vacío, es la única segura.

\* Identificadores de uso interno. **No se muestran** (`design-system.md` §8).

---

## 5. Reglas transversales

**Lista blanca de columnas en los cinco repositorios.** Se enumera lo que sale. La lista negra
existente del módulo se conserva como segunda línea, no como única: una lista negra falla abierta
ante una columna nueva; una blanca falla cerrada (research D3).

**Enumeraciones importadas, no copiadas.** Estados de partner y tipos de cambio se validan contra las
constantes del dominio, para que un valor nuevo no produzca un `400` engañoso (research D5).

**Resolución de catálogo.** Dos consultas y unión en memoria — sin JOIN.

**Centinelas.** El cliente de la base ya devuelve ausencia. Un partner sin suspender, una
reactivación sin motivo y un cliente sin preferencias llegan como «no hay», y **se muestran**.

**Paginación.** Keyset, `limit + 1`.

**Retraso de ingesta.** 5–15 s. Una credencial recién revocada puede seguir apareciendo activa. No se
compensa.

---

## 6. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "1786569480560|42", "limit": 50, "has_next": true },
    "filtros": { "entorno": "Produccion", "caduca_en_dias": 30 },
    "acotado_a": "propios"
  }
}
```

---

## 7. Resumen

| # | Listado | Tabla | Tipo | Cuidado |
|---|---|---|---|---|
| L1 | Partners | `Dim_Partner` | Estado actual | Estados importados del dominio |
| L2 | Credenciales | `Dim_CredencialAPI` | Estado actual | ⛔ el secreto no se consulta · ⚠️ no afirma el motivo de inactividad |
| L3 | Cambios de acceso | `Fact_HistorialAccesoPartner` | Período opcional | ⚠️ revocación ≠ cascada · reactivación sin motivo es correcto |
| L4 | Versiones del contrato | `Dim_VersionContratoAPI` | Estado actual | Las retiradas se incluyen |
| L5 | Alcance de datos | `Dim_Preferencias_Cliente` | Estado actual | ⚠️ ausente ≠ ilimitado |
