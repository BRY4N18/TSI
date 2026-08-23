# Feature Specification: Informes Tácticos Simples de Red Operativa (Frontend)

**Feature Branch / capa**: `002-tactico/Red-Operativa/informes-tacticos-simples/frontend`

**Created**: 2026-08-22

**Status**: Implemented *(retro-spec: documenta lo construido y lo verificado en navegador)*

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato OpenAPI.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## Contexto

Cuatro listados sobre dos objetos que **no son el mismo negocio**: las unidades de la flota, que
pertenecen a proveedores, y las regiones operativas, que no pertenecen a nadie. De ahí sale la
particularidad de este departamento: **la autoridad está partida en tres**, y no por acotamiento
sino por materia.

| Listado | Quién entra |
|---|---|
| `flota`, `bajas-unidad` | Administrador, **DirectorExpansion**, y acotados: Cliente, Proveedor |
| `regiones` | Administrador, DirectorTecnologico, DirectorExpansion |
| `validaciones-region` | Administrador, **DirectorTecnologico** |

⚠️ **Un Proveedor entra a flota y no entra a regiones.** Es la regla que da nombre a la primera
prueba del guard: *una región no pertenece a ninguna empresa de flota*. El proveedor tiene un
interés legítimo en las unidades —algunas son suyas— y ninguno en el mapa operativo del servicio.

⚠️ **`dado_de_alta` no es «disponible».** El alta es un hecho administrativo del registro de la
unidad; la disponibilidad es operativa y cambia por hora. La columna se etiqueta por lo que es, y
la pantalla **no** deriva un estado de servicio a partir de ella.

⚠️ **`estado_geografico` no es `estado_region`.** Conviven en `regiones`, y el mismo sustantivo
significa dos cosas: uno es la entidad federativa donde cae la región, el otro es la situación del
proceso. Las etiquetas los separan —«Estado geográfico» y «Estado»— porque una tabla con dos
columnas «Estado» es ilegible.

### Lo que la pantalla NO puede intentar

**No dibuja mapas ni pinta posiciones.** El backend no devuelve coordenadas de unidades ni polígonos
de región. Un módulo llamado «red operativa» invita a pedirlos; queda fuera de alcance.

**No muestra contacto del proveedor.** El nombre del proveedor es la identificación operativa que la
tabla necesita; teléfono, correo y contrato son datos de la relación comercial y no viajan.

**No deriva disponibilidad.** Ver el ⚠️ de arriba: ese dato lo publican los informes de gestión, con
su propio denominador y su propia autoridad.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Consultar la flota y sus bajas (Priority: P1)

Como Director de Expansión quiero ver de qué se compone la flota y qué unidades se han dado de
baja; como Proveedor quiero lo mismo **acotado a lo mío**.

**Acceptance Scenarios**:

1. **Given** un Proveedor, **When** entra a `flota`, **Then** el guard lo admite y aparece el aviso
   de alcance; **When** entra a `regiones` o a `validaciones-region`, **Then** es redirigido a
   `access-denied`.
2. **Given** el filtro **Proveedor**, **When** se despliega, **Then** ofrece un **combobox de
   nombres**; la consulta viaja con el **id** y la tabla muestra el **nombre**. Igual el filtro
   **Condado**.
3. **Given** una unidad sin condado resoluble, **When** aparece, **Then** su condado se ve
   **ausente** y **la fila no se omite**.
4. **Given** una baja, **When** aparece, **Then** `caso_afectado` está poblado solo cuando la baja
   se originó en un caso, y **ausente** —no `0`— cuando no.
5. **Given** `flota`, **When** se abre, **Then** **no** ofrece rango de fechas: es un listado de
   estado actual. `bajas-unidad` **sí** lo ofrece.

---

### US-FE-2 — Seguir las regiones y sus validaciones (Priority: P2)

Como Director Tecnológico quiero ver qué regiones llevan tiempo detenidas y cómo se resolvieron sus
validaciones.

**Acceptance Scenarios**:

1. **Given** el filtro **Detenida más de N días**, **When** se aplica, **Then** acota por
   `dias_sin_cambio`, que el backend calcula contra `fecha_actualizacion`.
2. **Given** una región, **When** aparece, **Then** «Estado geográfico» y «Estado» son **dos
   columnas distintas y así etiquetadas**.
3. **Given** el filtro de región en `validaciones-region`, **When** se despliega, **Then** es un
   **combobox** de nombres que envía `idregionoperativa`, y la tabla muestra el **nombre** de la
   región, nunca su id.
4. **Given** un `resultado` de validación, **When** se pinta, **Then** se lee en lenguaje humano y
   **no** como el literal crudo del enum.
5. **Given** un DirectorExpansion, **When** entra a `validaciones-region`, **Then** es rechazado: la
   validación es materia del Director Tecnológico.

---

### Edge Cases

- **Grafías del tipo de unidad.** ⚠️ Los datos traen `Grúa` y `Grua` como valores distintos. El
  filtro **Tipo de unidad** es de texto libre precisamente por eso: un catálogo cerrado tendría que
  elegir una de las dos y escondería la otra. La inconsistencia es del dato, no de la pantalla, y
  está registrada en `decisiones-pendientes.md`.
- **Placas duplicadas.** Existen placas repetidas en unidades distintas. La tabla **no deduplica**:
  fusionar filas ocultaría el problema a quien tiene que corregirlo.
- **Región fuera de `Producción`.** Sembrada el 2026-08-22 (`seed_casos_borde_informes.py`): hay una
  `Despublicada`, una `En_Alerta` y una `Rechazada`, con 120, 45 y 200 días sin cambio. Los cinco
  estados conviven en pantalla y **ninguno se agrupa** con otro.
- **Unidad sin condado.** Sembrada. ⚠️ Nace **dada de baja** a propósito: `activo = false` la excluye
  del algoritmo de despacho por garantía y no por un detalle de la consulta de candidatas. La
  composición de flota no filtra por `activo`, así que la fila se ve igual, con condado y estado
  geográfico **ausentes**.

---

## Requirements *(mandatory)*

- **FR-F01**: Una pantalla por listado más un índice, consumiendo la capa compartida.
- **FR-F02**: Las columnas MUST coincidir con el contrato OpenAPI.
- **FR-F03**: Los filtros **Proveedor**, **Condado** y **Región** MUST ser comboboxes que **envían
  el id y muestran el nombre**. La tabla **MUST NOT** pintar ids.
- **FR-F04**: Las pantallas **MUST NOT** mostrar coordenadas, polígonos ni datos de contacto del
  proveedor.
- **FR-F05**: `dado_de_alta` MUST etiquetarse como alta administrativa, y la pantalla **MUST NOT**
  derivar de ella un estado de disponibilidad.
- **FR-F06**: `estado_geografico` y `estado_region` MUST llevar etiquetas distinguibles.
- **FR-F07**: Los tres guards MUST respetar el reparto de la tabla del Contexto. Un **Proveedor**
  **MUST NOT** entrar a `regiones` ni a `validaciones-region`.
- **FR-F08**: El rango de fechas MUST aparecer en `bajas-unidad` y `validaciones-region`, y **no**
  en `flota` ni `regiones`, que son de estado actual.
- **FR-F09**: Un valor ausente —condado, caso afectado, motivo— MUST verse ausente, y la fila
  **MUST NOT** omitirse.
- **FR-F10**: El índice MUST listar **solo** los informes que el rol puede abrir
  (`listadosVisiblesPara`).

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los cuatro listados se consultan con las columnas declaradas.
- **SC-F02**: Un Proveedor ve `flota` y `bajas-unidad`, y **solo** esos dos en el índice.
- **SC-F03**: **En ninguna** celda aparece un id, ni coordenadas, ni contacto del proveedor.
- **SC-F04**: Ningún enum se pinta con su literal crudo.
- **SC-F05**: Ninguna pantalla implementa tabla, paginación o manejo de error propio.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Mapas de cobertura y posiciones | El backend no devuelve geometría |
| Disponibilidad y utilización | Son compuestos; los cubren los informes de gestión |
| Contacto y contrato del proveedor | Relación comercial, no operación |
| Unificar `Grúa`/`Grua` | Corrección de datos, no de pantalla — ver `decisiones-pendientes.md` |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes` |
