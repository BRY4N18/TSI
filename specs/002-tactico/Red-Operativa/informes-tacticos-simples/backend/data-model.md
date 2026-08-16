# Data Model — Informes Tácticos Simples de Red Operativa (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

**Ninguna tabla nueva. Ningún cambio de esquema.**

---

## 1. Tablas leídas

| Tabla | Rol | Listados |
|---|---|---|
| `Dim_UnidadEmergencia` | Entidad principal | L1 |
| `Fact_BajaUnidad` | Entidad principal | L2 |
| `Dim_RegionOperativa` | Entidad principal | L3 |
| `Dim_ValidacionRegion` | Entidad principal | L4 |
| `Dim_Condado`, `Dim_Estado` | Catálogo geográfico | L1, L3 |
| `Dim_Cliente` | Catálogo (proveedor) | L1, L2 |
| `Dim_Usuarios` | Catálogo (ejecutor) | L2, L4 |

Todas de solo lectura.

**Tabla deliberadamente NO leída:** el histórico de estados de unidad. Ver §2.

---

## 2. Existencia y disponibilidad: la distinción que gobierna el módulo

| Noción | Dónde vive | En este módulo |
|---|---|---|
| **Existencia** — alta o baja | `Dim_UnidadEmergencia.activo` | ✅ Se expone |
| **Disponibilidad operativa** — Activa, Ocupada, En Misión, Fuera de servicio | **Solo** en `Fact_HistorialEstadoUnidad` | ⛔ **Fuera de alcance** |

La disponibilidad se obtiene con `get_current_estado()`, que consulta **una vez por unidad**. Para
una página de N unidades son N+1 consultas, o una agregación del histórico más un cruce —compuesto
en ambos casos.

**`activo` significa «existe», no «puede acudir».** Un listado filtrado por `activo = true` y
presentado como flota disponible contaría unidades fuera de servicio, ocupadas o en camino a otro
accidente. La cobertura disponible es **CU-T08**, compuesta.

---

## 3. El eje de acotamiento, con su criterio explícito

| Listado | Columna de titularidad | Criterio de pertenencia |
|---|---|---|
| L1 Flota | `Dim_UnidadEmergencia.idcliente` | **Administrador local** de la cuenta |
| L2 Bajas | vía la unidad → `idcliente` | **Administrador local** |
| L3 Regiones | — | Sin acotamiento: solo Administrador y Director Tecnológico |
| L4 Validaciones | — | Sin acotamiento |

**El criterio importa** (research D1). En este sistema, «pertenecer a una cuenta» significa dos cosas
distintas según el departamento: ser su administrador local, o estar vinculado a ella. Red Operativa
usa el estricto en su pantalla operativa, y el listado **debe usar el mismo** para no ampliar por
informe lo que la pantalla restringe.

---

## 4. Los cuatro listados

### L1 — Composición de la flota · `FR-001`, `FR-002`, `FR-006`–`FR-008` · OT12

- **Tabla:** `Dim_UnidadEmergencia`
- **Campos:** `idunidademergencia`*, `placa`, `nombre_unidad`, `tipo_unidad`, `capacidad`,
  `proveedor`, `condado`, `estado_geografico`, `zona_cobertura`, `tipo_propiedad`, `dado_de_alta`
- **⛔ No expuestos:** `latitud`, `longitud` (posición de la unidad — dato sensible sujeto a control
  y auditoría) ni `contactoproveedor` (dato personal). **Columnas enumeradas, prohibido `SELECT *`**
  (research D6)
- **Orden:** `idunidademergencia DESC` · **Cursor:** escalar
- **Filtros:** `proveedor`, `condado`, `tipo_unidad`, `dado_de_alta`
- **Tipo:** estado actual → rechaza rango de fechas
- **Acotado por:** `idcliente`, criterio administrador local
- **Catálogo:** `idcondado` → `Dim_Condado.condado` → `Dim_Estado.estado`; `idcliente` →
  `Dim_Cliente.razon_social`

**⚠️ `dado_de_alta` no es disponibilidad.** La respuesta declara su alcance en `meta` (FR-008) para
que ningún consumidor lo lea como cobertura.

**Una unidad sin condado aparece** con la ubicación ausente (FR-023): sin condado no puede ser
candidata en un despacho, y esa es la anomalía que la supervisión busca.

---

### L2 — Bajas de unidad · `FR-003`, `FR-021` · OT12 / CU-O42

- **Tabla:** `Fact_BajaUnidad`
- **Campos:** `idbajaunidad`*, `placa`, `proveedor`, `motivo`, `tipo_baja`, `ejecutada_por`,
  `caso_afectado`, `fechahora`
- **Orden:** `fechahora DESC` · **Cursor:** compuesto `fechahora|idbajaunidad`
- **Filtros:** `desde`, `hasta` (**opcionales**), `tipo_baja`, `proveedor`
- **Tipo:** **hechos del período**
- **Acotado por:** el proveedor de la unidad

**⚠️ Dos tipos de baja con significado muy distinto** (research D5):

| Tipo | Significa | Caso afectado |
|---|---|---|
| `Normal` | Salida ordenada de la flota | Ausente |
| `Forzada_con_reasignación` | **La unidad atendía un caso** y hubo que reasignar | **Presente** |

Sumar ambos tipos convertiría un incidente operativo en una estadística de rotación de flota. El
caso afectado es la traza de impacto que el SRS exige.

---

### L3 — Regiones operativas · `FR-004` · OT11/OT13

- **Tabla:** `Dim_RegionOperativa`
- **Campos:** `idregionoperativa`*, `nombre_region`, `estado_region`, `estado_geografico`,
  `dias_sin_cambio`, `fecha_actualizacion`
- **Orden:** `idregionoperativa DESC` · **Cursor:** escalar
- **Filtros:** `estado_region`, `detenida_mas_de_dias`
- **Tipo:** estado actual
- **Acceso:** Administrador y Director Tecnológico. Sin acotamiento — una región no pertenece a
  ningún proveedor
- **Catálogo:** `idestado` → `Dim_Estado.estado`

**⚠️ Cinco estados, y dos no significan lo que parecen** (research D4):

| Estado | Significa |
|---|---|
| `En_Validación` | Aún no opera |
| `Producción` | Opera con normalidad |
| **`En_Alerta`** | **Opera, con cobertura degradada** — candidata a despublicarse, **no** despublicada |
| `Despublicada` | Ya no opera |
| Rechazo definitivo | Descartada tras validación fallida |

**Prohibido agrupar `En_Alerta` con `Despublicada`**: ocultaría la ventana en la que OT13 puede
actuar, que es retirar una región *antes* de dejar casos sin continuidad.

Las **despublicadas se incluyen** en el listado: una región retirada sigue siendo información de
supervisión.

`dias_sin_cambio` se calcula en el servicio con reloj inyectable; `detenida_mas_de_dias` se traduce a
una fecha de corte que **sí viaja al filtro**.

---

### L4 — Intentos de validación de región · `FR-005` · OT11 / CU-O44

- **Tabla:** `Dim_ValidacionRegion`
- **Campos:** `idvalidacionregion`*, `region`, `resultado`, `motivo`, `ejecutada_por`, `fechahora`
- **Orden:** `fechahora DESC` · **Cursor:** compuesto `fechahora|idvalidacionregion`
- **Filtros:** `desde`, `hasta` (**opcionales**), `idregionoperativa`, `resultado`
- **Tipo:** **hechos del período**
- **Acceso:** Administrador y Director Tecnológico
- **Catálogo:** `idusuario` → `Dim_Usuarios`; `idregionoperativa` → `Dim_RegionOperativa`

**Se conservan todos los intentos.** Dos rechazos seguidos producen dos filas; el segundo **no**
sustituye al primero. Está verificado en el sistema real y es lo que alimenta el criterio de
validación que CU-T07 pide definir.

\* Identificadores de uso interno. **No se muestran** (`design-system.md` §8).

---

## 5. Reglas transversales

**Resolución geográfica por lotes** (research D3). Se reutiliza el repositorio de catálogo de
ubicación, que ya consulta con `IN (…)`: **dos consultas por página**, no una por fila. La unidad se
ubica por **condado**, así que la cadena es corta — condado y su estado geográfico.

**Acotamiento.** Administrador ve todos los proveedores; una empresa proveedora queda forzada a lo
suyo, resuelta por el criterio **estricto**; pedir lo ajeno es **negativa explícita**.

**Centinelas.** El cliente de la base ya devuelve ausencia para los centinelas. Una unidad sin
condado, una baja sin caso afectado y un intento sin motivo llegan como «no hay», y **se muestran**.

**Paginación.** Keyset, `limit + 1`.

**Retraso de ingesta.** 5–15 s. Una unidad recién dada de baja puede seguir apareciendo como alta.
No se compensa.

---

## 6. Forma de la respuesta

```json
{
  "data": [ { "…": "campos del listado" } ],
  "meta": {
    "pagination": { "cursor": "42", "limit": 50, "has_next": true },
    "filtros": { "condado": 7, "tipo_unidad": "Ambulancia" },
    "acotado_a": "propios",
    "alcance": "composicion_de_flota"
  }
}
```

`alcance` es específico del listado de flota y cumple FR-008: declara que el listado describe **qué
unidades existen**, no cuáles pueden acudir. Documentarlo solo en el contrato no protegería al
consumidor que no lo lee, y esa confusión cuesta una decisión de cobertura.

---

## 7. Resumen

| # | Listado | Tabla | Tipo | Cuidado |
|---|---|---|---|---|
| L1 | Composición de flota | `Dim_UnidadEmergencia` | Estado actual | ⚠️ alta ≠ disponible · ⛔ sin posición ni contacto |
| L2 | Bajas de unidad | `Fact_BajaUnidad` | Período opcional | ⚠️ forzada = dejó un caso sin unidad |
| L3 | Regiones operativas | `Dim_RegionOperativa` | Estado actual | ⚠️ `En_Alerta` opera; no agrupar con despublicada |
| L4 | Intentos de validación | `Dim_ValidacionRegion` | Período opcional | Se conservan todos los intentos |
