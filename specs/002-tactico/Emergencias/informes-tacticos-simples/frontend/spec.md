# Feature Specification: Informes Tácticos Simples de Emergencias (Frontend)

**Feature Branch / capa**: `002-tactico/Emergencias/informes-tacticos-simples/frontend`

**Created**: 2026-08-15

**Status**: Draft

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato OpenAPI.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## Contexto

Cinco listados, y **dos cosas que ningún módulo anterior de frontend ha ejercitado**:

1. **`zonas_contratadas`**, el tercer valor de `acotado_a`. Cuentas y Clientes no acota; Soporte
   valida `propios`. Este es el único que valida el eje de cobertura.
2. **Datos sensibles excluidos por la constitución** —coordenadas del accidente e identidad de
   implicados—, con la particularidad de que **la autoridad del departamento tampoco los ve**.

⚠️ **`zonas_contratadas` no es `propios`.** Los accidentes ocurridos en una zona contratada **no
pertenecen al cliente**: son hechos de terceros ocurridos donde él contrató cobertura. La pantalla
tiene texto propio para ese valor, y un «tus accidentes» afirmaría algo falso sobre datos de
siniestralidad ajenos.

### Lo que la pantalla NO puede intentar

**No dibuja mapas ni pinta posiciones.** El backend no devuelve coordenadas —exclusión
constitucional, no de acotamiento—, así que no hay nada que mapear. Un módulo con «mapa» en el
nombre podría invitar a pedirlas al backend; la spec lo declara fuera de alcance para que la
pregunta no se abra.

**No reconstruye el estado formal del caso.** El backend devuelve **tres hechos** —`activo`,
`hora_fin`, `duplicado_de`— y no un estado calculado, porque la exclusividad entre cerrado,
descartado y fusionado la garantiza otro módulo. La pantalla **los muestra por separado**: derivar
una etiqueta aquí repetiría, en el último paso, la inferencia que el backend evitó a propósito.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Consultar los casos con el alcance que corresponde (Priority: P1)

Como Operador quiero ver todos los casos; como Cliente quiero ver los cerrados **de mis zonas** y
saber que son solo esos.

**Acceptance Scenarios**:

1. **Given** un rol interno, **When** consulta los casos, **Then** **no** aparece aviso de alcance.
2. **Given** un Cliente, **When** consulta, **Then** aparece el aviso de **zonas contratadas**, y
   **no** dice que los accidentes sean suyos.
3. **Given** un Cliente sin resultados, **When** consulta, **Then** el estado vacío dice que no hay
   resultados **en sus zonas** y que puede haberlos en otras.
4. **Given** cualquier rol, **When** consulta, **Then** **ninguna** columna muestra coordenadas ni
   identidad de personas implicadas.
5. **Given** un caso fusionado, **When** aparece, **Then** muestra de qué caso es duplicado, y los
   tres hechos van **por separado**: no hay columna «estado».
6. **Given** un Partner de integración, **When** entra, **Then** el guard lo rechaza: el acceso
   programático a estos datos tiene su propio camino, con su alcance y su auditoría.

---

### US-FE-2 — Seguir despachos, evidencia y cierres (Priority: P2)

Como Operador o Administrador quiero los otros cuatro listados, que son internos.

**Acceptance Scenarios**:

1. **Given** un despacho en tránsito, **When** aparece, **Then** sus horas de llegada y retiro se ven
   **ausentes** — no como fecha de 1970 — y `en_transito` dice que sí.
2. **Given** una evidencia capturada sin conexión, **When** aparece, **Then** su hora de captura y su
   hora de registro **difieren**, y la de captura es la del sitio.
3. **Given** un cierre sin calificar, **When** aparece, **Then** la calificación se ve **ausente**,
   nunca como `0`.
4. **Given** un Cliente, **When** entra a cualquiera de los cuatro, **Then** el guard lo rechaza.
5. **Given** que `cierres` es de estado actual, **When** se abre, **Then** **no** ofrece rango de
   fechas; los otros cuatro sí.

---

### Edge Cases

- **Caso sin ubicación resoluble.** Calle, ciudad y condado ausentes, y **la fila no se omite**.
- **Cliente sin zonas contratadas.** Resultado vacío, con el aviso de alcance. Nunca el listado
  completo.
- **`hora_fin`.** ⚠️ Su columna es `STRING` y guarda **epoch-ms como texto**. El backend la
  normaliza a ISO antes de devolverla; hasta el 2026-08-15 no lo hacía, y en pantalla salía el número
  crudo. Un fixture inventado —`"09:30"`— escondía el defecto en las pruebas.

---

## Requirements *(mandatory)*

- **FR-F01**: Una pantalla por listado más un índice, consumiendo la capa compartida.
- **FR-F02**: Las columnas MUST coincidir con el contrato OpenAPI.
- **FR-F03**: ⚠️ El aviso de `zonas_contratadas` MUST mostrarse, **también en el estado vacío**, y
  **MUST NOT** afirmar que los datos pertenecen al cliente.
- **FR-F04**: Las pantallas **MUST NOT** mostrar coordenadas ni identidad de implicados, **ni
  siquiera a la autoridad del departamento**. Es exclusión constitucional, no de acotamiento.
- **FR-F05**: El listado de casos **MUST NOT** derivar una columna «estado»: los tres hechos van por
  separado.
- **FR-F06**: `hora_fin` MUST mostrarse como fecha legible. La columna de origen es `STRING` con
  epoch-ms escrito como texto, y el backend la **normaliza a ISO** — corregido el 2026-08-15, cuando
  se vio que salía en pantalla como `1786625595899`.
- **FR-F07**: El guard de `casos` admite roles internos **y** Cliente; los otros cuatro, **solo**
  internos. `PartnerIntegracion` **MUST NOT** entrar a ninguno.
- **FR-F08**: El rango de fechas MUST aparecer en los cuatro de período y **no** en `cierres`.
- **FR-F09**: Un valor ausente —hora de llegada, calificación, ubicación— MUST verse ausente, y la
  fila **MUST NOT** omitirse.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los cinco listados se consultan con las columnas declaradas.
- **SC-F02**: Un Cliente ve el aviso de zonas contratadas; un rol interno **no** lo ve.
- **SC-F03**: **En ninguna** respuesta ni celda aparecen coordenadas o identidad de implicados.
- **SC-F04**: **Cero** columnas «estado» en casos.
- **SC-F05**: Un Partner recibe negativa en los cinco.
- **SC-F06**: Ninguna pantalla implementa tabla, paginación o manejo de error propio.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Mapas y posiciones | ⛔ El backend no devuelve coordenadas: exclusión constitucional |
| Estado formal del caso | Es compuesto; ya lo cubren los informes agregados |
| Texto de mensajes internos | El backend no lo consulta |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes` |
