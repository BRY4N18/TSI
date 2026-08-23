# Feature Specification: OE4 — Histórico como Ventaja e Inteligencia — Frontend

**Feature Branch / capa**: `001-estrategico/OE4-inteligencia-predictiva/frontend`

**Created**: 2026-08-18

**Status**: Implemented (2026-08-18). Cuatro pantallas Z (`calidad`, `concentracion`, `impacto`, `cobertura`); 9 GET; sin mapa ni modelo fingido.

**Depends-on**: [`../backend/spec.md`](../backend/spec.md), su contrato de lectura y
[`../../acceso-estrategico.md`](../../acceso-estrategico.md) §4.4, §5 y §6. Esta capa **MUST NOT**
redefinir reglas de negocio, cifras, estados, metas ni contratos de lectura.

**Gobierna el layout**: patrón Z (el mismo que OE1/OE2/OE3/OE5/OE6) y
[`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)
(máximo 6–8 bloques; Ley de Hick; sidebar por rol, sin ítems deshabilitados).

**Input**: pantallas de los **nueve informes ya publicados** de OE4; no pintar los seis bloqueados
(modelo predictivo, preposición, catálogo vendible, latencia de ingesta); no mapa con coordenadas;
no eje de región; cero no registrado ≠ cero real; copiar la cáscara Z, no extraer `shared/`.

---

## Contexto

El backend de OE4 **ya publica nueve informes** y **no publica** los otros seis. Esta capa no
calcula: pinta lo que el contrato ya corrige.

El objetivo promete histórico fiable + inteligencia vendible + modelo predictivo. **Hoy solo existen
las dos primeras mitades.** Un tablero que pinte precisión 0 % o unidades preposicionadas 0 %
**mentiría**: no hay modelo. MUST NOT existir recuadro, ítem gris ni «próximamente» para E4-07…11 ni
E4-14.

Entrega **cuatro pantallas nuevas**. No se mezclan con compuestos tácticos, OE6 (llegada a la
persona) ni OE3 (degradación del despacho).

Todas las metas de este OE son `[CALIBRAR]`. `cumple` **nunca** es booleano. MUST NOT haber
semáforo cerrado.

### La autoridad está partida

[`acceso-estrategico.md`](../../acceso-estrategico.md) §4.4: Datos es dueño; Operaciones entra
**solo** donde se mide el expediente. El `Gerente` ve las cuatro. El Partner no entra.

| Materia | Quién entra | Pantalla |
|---|---|---|
| ¿El histórico es fiable? | `DirectorDatos` · `DirectorOperaciones` · `Gerente` | **Calidad** |
| ¿Dónde y cuándo se concentran los casos? | `DirectorDatos` · `Gerente` | **Concentración** |
| ¿A quién y a qué vía afecta? | `DirectorDatos` · `DirectorOperaciones` · `Gerente` | **Impacto** |
| ¿Hay masa para entrenar, por condado? | `DirectorDatos` · `Gerente` | **Cobertura** |
| Precisión / predicción / preposición / versiones / catálogo / latencia de ingesta | **nadie** | — (sin tabla o idempotencia) |
| Partner, Finanzas, Expansión, Tecnológico, Éxito de Cliente | **nadie** | — |

El `DirectorOperaciones` **MUST NOT** ver Concentración ni Cobertura (el GET de esos informes no
lo admite). Un enlace que abriera 403 descubriría la superficie.

Ver **MUST NOT** habilitar a vender un producto, entrenar un modelo ni despachar.

### El ojo recorre el patrón Z

1. Arriba izquierda: métrica principal. Sin semáforo.
2. Arriba derecha: período obligatorio + comparación (`ninguna`, mes anterior, mismo tramo del año
   anterior). Únicas acciones.
3. Diagonal: visual grande (ranking, origen, zona por **nombre**).
4. Abajo derecha: lectura — qué implica, qué no se registra, cobertura parcial.

**No hay mapa.** E4-05 se titula «mapa» en el catálogo; el contrato entrega **nombre de zona**,
nunca coordenadas. Esta capa pinta ranking por condado/ciudad/calle, no un mapa.

### Lo que no se puede mostrar

Un índice único sin sus cuatro piezas **esconde la causa**. MUST verse completitud, descarte,
fusión y evidencia **junto** al consolidado, y la fórmula declarada.

Un campo crítico con 0 ausencias **MUST seguir en el ranking**. Omitirlo se confunde con «nadie
lo revisó».

Clima con 3 casos MUST leerse **parcial / anécdota**, no patrón.

Víctimas no registradas MUST NOT contar como 0 víctimas. Distancia NULL MUST NOT ser 0 km.
Denominadores de duración y distancia van **separados**.

Zona bajo umbral MUST decir **sin masa crítica** y mostrar el umbral. Agrupa por **condado**.

Período sin accidentes MUST verse vacío con cobertura completa: es buena noticia, no fallo.

Los seis bloqueados MUST NOT tener recuadro. Un 0 % de precisión fingiría un modelo que no existe.

### Qué entra en cada pantalla

| Pantalla | Pregunta | Héroe | Visual | Lectura | Apoyo |
|---|---|---|---|---|---|
| **Calidad** | ¿El histórico es fiable? | E4-01 índice + 4 componentes | E4-02 completitud | E4-03 ranking de ausencias (ceros incluidos) | E4-04 origen central vs campo (plegado) |
| **Concentración** | ¿Dónde y cuándo? | E4-05 ranking por zona (nombre) | E4-06 horario; clima si hay muestra | Alcance: no es mapa; clima parcial | — |
| **Impacto** | ¿A quién y a qué vía? | E4-12 víctimas con `casos_con_dato` | E4-13 duración y distancia | Denominadores distintos; no-dato ≠ cero | — |
| **Cobertura** | ¿Hay masa por condado? | E4-15 casos vs umbral | Condados **sin masa crítica** | Umbral publicado; grano condado | — |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Director de Datos ve si el histórico es fiable (Priority: P1) 🎯 MVP

Abre **Calidad**, fija un período y ve el índice **y** sus cuatro componentes. El visual es la
completitud. La lectura es el ranking de campos (también los que no fallan). El origen
central/campo queda plegado. Operaciones también entra. Un Partner no.

**Why this priority**: vender inteligencia sobre un histórico no medido es vender a ciegas.

**Independent Test**: las cuatro piezas se leen en el mismo bloque que el índice. Expansión no ve
el enlace.

**Acceptance Scenarios**:

1. **Given** un Director de Datos autenticado, **When** abre Calidad, **Then** ve patrón Z:
   índice+componentes, período, completitud, ranking de ausencias.
2. **Given** el héroe, **When** se muestra, **Then** completitud, descarte, fusión y evidencia van
   **con** el consolidado, y se declara cómo se combina.
3. **Given** un campo crítico con 0 ausencias, **When** se mira el ranking, **Then** aparece con
   cero; MUST NOT desaparecer.
4. **Given** un período sin accidentes, **When** se mira, **Then** está **vacío** con cobertura
   completa, no 0 % de calidad.
5. **Given** un Director de Operaciones, **When** busca Calidad, **Then** ve el enlace. Un
   Partner, Tecnológico o Financiero no.

---

### User Story 2 - Ver concentración sin pintar un mapa (Priority: P2)

El Director de Datos abre **Concentración**. El héroe es el ranking de zonas **por nombre**. El
visual es el patrón horario; el clima se declara **parcial** si la muestra es escasa. Operaciones
**no** ve este enlace.

**Why this priority**: es el producto vendible, después de saber si el histórico vale.

**Independent Test**: no hay mapa ni lat/lon. Operaciones no ve el ítem. Clima con n bajo no se
lee como patrón cerrado.

**Acceptance Scenarios**:

1. **Given** un Director de Datos, **When** abre Concentración, **Then** ve ranking por nombre de
   zona y patrón horario.
2. **Given** la pantalla, **When** se recorre, **Then** **no** hay mapa, coordenadas ni eje de
   región.
3. **Given** muestra climática bajo mínimo, **When** se mira, **Then** se lee **parcial**, no un
   patrón de clima.
4. **Given** un Director de Operaciones, **When** busca Concentración, **Then** no ve el enlace.

---

### User Story 3 - Ver impacto humano y vial sin ceros fingidos (Priority: P3)

Operaciones y Datos abren **Impacto**. El héroe distingue víctimas registradas de casos sin dato.
El visual muestra duración y distancia **con denominadores distintos**.

**Independent Test**: un caso sin víctimas no suma 0. Distancia NULL no es 0 km.

**Acceptance Scenarios**:

1. **Given** un Director de Operaciones, **When** abre Impacto, **Then** ve impacto humano y vial
   por condado.
2. **Given** casos sin víctimas registradas, **When** se mira, **Then** van en `casos_con_dato`,
   no como cero víctimas.
3. **Given** el impacto vial, **When** se muestra, **Then** duración y distancia tienen
   denominadores **separados**.
4. **Given** un Partner, **When** busca Impacto, **Then** no ve el enlace.

---

### User Story 4 - Ver si hay masa crítica por condado (Priority: P4)

El Director de Datos abre **Cobertura**. Cada condado muestra casos, umbral y si está **sin masa
crítica**. Operaciones no entra. No hay latencia de ingesta.

**Independent Test**: el umbral está a la vista. Condado bajo umbral no se disfraza de listo para
entrenar. Operaciones sin menú.

**Acceptance Scenarios**:

1. **Given** un Director de Datos, **When** abre Cobertura, **Then** ve casos vs umbral por
   condado.
2. **Given** un condado bajo el umbral, **When** se mira, **Then** se lee **sin masa crítica** y
   el umbral es visible.
3. **Given** un Director de Operaciones, **When** busca Cobertura, **Then** no ve el enlace.
4. **Given** el menú, **When** se busca latencia de ingesta, **Then** no hay recuadro.

---

### User Story 5 - Ni mapa, ni predicción fingida, ni bloqueados (Priority: P1)

En las cuatro pantallas **no hay** mapa, coordenadas, nombres de implicados, eje de región,
precisión del modelo, preposición, catálogo vendible ni latencia de ingesta.

**Why this priority**: un 0 % de precisión sería silencioso y falso.

**Independent Test**: ninguna pantalla contiene mapa, lat/lon, los seis slugs bloqueados ni
semáforo de `cumple`.

**Acceptance Scenarios**:

1. **Given** cualquiera de las cuatro, **When** se recorre, **Then** no hay mapa ni identidad.
2. **Given** el menú de cualquier cargo, **When** se busca el modelo predictivo, **Then** no hay
   enlace.
3. **Given** Concentración, **When** se agrupa, **Then** el grano es nombre de zona / condado,
   no región.

---

### Edge Cases

- Período sin accidentes: vacío, cobertura completa (buena noticia).
- Campo crítico con 0 ausencias: sigue en el ranking.
- Clima con 3 casos: parcial, no patrón.
- Caso sin víctimas registradas: no es 0 víctimas.
- Distancia NULL: no es 0 km.
- Condado bajo umbral: sin masa crítica, umbral visible.
- Comparación sin ventana anterior: ausente con motivo.
- Una zona falla: el resto sigue.
- Operaciones en Concentración/Cobertura: sin enlace.

---

## Functional Requirements (UI)

- **FR-UI-001**: Exactamente cuatro pantallas —Calidad, Concentración, Impacto, Cobertura.
- **FR-UI-002**: Mostrar los **nueve** publicados; MUST NOT pintar los seis bloqueados.
- **FR-UI-003**: Patrón Z; MUST NOT ser una grilla de nueve tarjetas.
- **FR-UI-004**: 6–8 bloques. Calidad MUST plegar E4-04.
- **FR-UI-005**: Período obligatorio. Comparación = única otra acción. MUST NOT mapa, filtro de
  región ni exportación.
- **FR-UI-006**: Período sin accidentes → vacío con cobertura completa, no 0 % de calidad.
- **FR-UI-007**: E4-01 MUST mostrar índice **y** cuatro componentes **y** cómo se combina.
- **FR-UI-008**: E4-03 MUST listar todos los campos críticos, también con 0 ausencias.
- **FR-UI-009**: `cumple` MUST NOT pintarse como semáforo: en este OE nunca es booleano.
- **FR-UI-010**: E4-05 MUST ser ranking por **nombre** de zona. MUST NOT coordenadas ni mapa.
- **FR-UI-011**: E4-06 MUST declarar cobertura climática; muestra baja → parcial, no patrón.
- **FR-UI-012**: E4-12 MUST separar no-dato de cero víctimas.
- **FR-UI-013**: E4-13 MUST mostrar denominadores de duración y distancia por separado.
  Distancia NULL ≠ 0 km.
- **FR-UI-014**: E4-15 MUST mostrar umbral y marcar **sin masa crítica**. Grano **condado**.
- **FR-UI-015**: MUST NOT identidad de implicados, operadores o técnicos.
- **FR-UI-016**: Menú por pantalla y cargo. MUST NOT ítems grises.
- **FR-UI-017**: Ver MUST NOT habilitar vender, entrenar ni despachar.
- **FR-UI-018**: Cobertura/recuento/alcance/falta del backend MUST ir junto a la cifra.
- **FR-UI-019**: Comparación ausente MUST declararse con motivo.
- **FR-UI-020**: MUST NOT fusionar estas historias con táctico, OE6 ni OE3.
- **FR-UI-021**: Cáscara Z copiada de OE3. MUST NOT extraer `shared/`.
- **FR-UI-022**: MUST NOT inventar eje de región ni informe geográfico nuevo.
- **FR-UI-023**: Operaciones MUST NOT ver ni entrar a Concentración ni Cobertura.
- **FR-UI-024**: El Gerente MUST ver las cuatro. El Administrador MUST NOT sustituir a Datos.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Un Director de Datos identifica índice y qué componente lo arrastra en **menos de
  5 segundos** en Calidad.
- **SC-F02**: No existe un estado en el que se vea el índice y no se vean las cuatro piezas.
- **SC-F03**: Un período sin accidentes no se puede leer como calidad 0 %.
- **SC-F04**: Un campo con 0 ausencias no desaparece del ranking.
- **SC-F05**: Concentración no se puede leer como un mapa de personas.
- **SC-F06**: Clima con muestra escasa no se puede leer como patrón cerrado.
- **SC-F07**: Un caso sin víctimas registradas no se puede leer como 0 víctimas.
- **SC-F08**: Distancia ausente no se puede leer como 0 km.
- **SC-F09**: Datos ve las cuatro. Operaciones ve Calidad e Impacto. Un partner, ninguna.
- **SC-F10**: No hay recuadros de los seis bloqueados ni semáforo de `cumple`.
- **SC-F11**: Cada vista principal queda en **8 o menos** bloques.
- **SC-F12**: Un condado bajo umbral no se puede leer como listo para entrenar.

---

## Key Entities *(pantalla)*

- **Pantalla de historia**: una de las cuatro.
- **Zona Z**: métrica, período, visual, lectura.
- **Marca de parcial / recuento / no-dato / sin masa crítica / clima escaso**.
- **Lectura**: no es un botón de venta ni de entrenamiento.

---

## Assumptions

- El backend de los nueve publicados está en servicio.
- Período obligatorio; sin default que sustituya desde/hasta/granularidad.
- Región no es construible: condado / nombre de zona.
- Los seis bloqueados siguen bloqueados.
- Z se copia de OE3 (no `shared/`).
- Todas las metas son `[CALIBRAR]`.
- No hay exportación.
- El mínimo de muestra lo resuelve el backend.

---

## Out of Scope

| Excluido | Por qué |
|---|---|
| Compuestos tácticos | Ya existen |
| OE6 llegada / OE3 degradación | Otros dueños |
| E4-07…11 | Sin tablas de modelo/predicción/catálogo |
| E4-14 | Idempotencia reescribe `cargado_en` |
| Mapa, coordenadas, identidad | Constitución / contrato |
| Eje de región | #38 |
| Acciones de venta o entrenamiento | Ver no habilita |
| Extraer `shared/` | Fuera de esta pasada |
| Cambiar OpenAPI | Depends-on |

---

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo. Z, ≤8 bloques, menú por rol. SC-F01, SC-F11. |
| **Functional Suitability** | Nueve publicados; bloqueados declarados. Cero no registrado ≠ cero. |
| **Security** | Guards partidos. Partner fuera. Sin identidad. |
| **Safety** | Un mapa de personas, un 0 % de precisión fingido o víctimas=0 por no-dato induciría
  decisiones de flota o de venta falsas. Esta capa no despacha ni vende; evita mentir a quien sí. |
| **Reliability** | Vacío ≠ 0; fallo de zona aislado. |
| **Maintainability** | Capa `frontend/`; copia Z, sin librería. |
| **Performance Efficiency** | Heredada. Umbral: héroe en <5 s. |
| **Compatibility** | N/A: sin intercambio externo. |
| **Flexibility** | Condado, no región. La mitad predictiva **no se finge**. |

**Traceability**: índice [`../OE4-inteligencia-predictiva.md`](../OE4-inteligencia-predictiva.md).
