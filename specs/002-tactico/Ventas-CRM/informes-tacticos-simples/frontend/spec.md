# Feature Specification: Informes Tácticos Simples de Ventas y CRM (Frontend)

**Feature Branch / capa**: `002-tactico/Ventas-CRM/informes-tacticos-simples/frontend`

**Created**: 2026-08-22

**Status**: Implemented *(retro-spec: documenta lo construido y lo verificado en navegador)*

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato OpenAPI.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## Contexto

Cuatro listados y **el único departamento donde el acotamiento es `propios` sobre una cartera de
personas**. Un Gerente de Ventas ve sus prospectos; los del gerente de al lado no existen para él.

| Listado | Quién entra |
|---|---|
| `prospectos`, `demos-activas`, `notificaciones-enviadas` | Administrador, DirectorMarketing, y acotados: **GerenteVentas**, **GerenteCuentasPublicas** |
| `reasignaciones` | **Solo** Administrador y DirectorMarketing |

⚠️ **Las asignaciones de cartera son supervisión pura.** Quien está *dentro* de un movimiento de
cartera es parte interesada: el listado dice de qué ejecutivo salió cada prospecto y a cuál entró.
Dárselo a los gerentes convertiría un instrumento de supervisión en un marcador entre ellos. Por eso
`reasignaciones` es el único de los cuatro sin roles acotados — y por eso el índice **tampoco lo
ofrece** a quien no puede abrirlo.

⚠️ **«Reasignaciones» se llama «Asignaciones de cartera».** El id de ruta sigue siendo
`reasignaciones` —cambiarlo rompería enlaces guardados—, pero el título no: el listado incluye la
**primera** asignación de un prospecto, que no reasigna nada. `tipo_asignacion` distingue una de
otra.

⛔ **No se publica dato de contacto del prospecto.** La tabla muestra empresa, nombre del contacto y
cargo — lo que hace falta para reconocerlo. **No** muestra correo ni teléfono, ni siquiera al
Director de Marketing.

### Lo que la pantalla NO puede intentar

**No calcula conversión, embudo ni pronóstico.** Todo eso es compuesto, con su denominador declarado,
y vive en los informes de gestión. `valor_estimado` es una estimación por fila y **no se suma**.

**No deriva «perdido» de la etapa.** `estado` y `etapa_actual` son columnas distintas: un prospecto
puede estar perdido en cualquier etapa, y un prospecto en la última etapa no está convertido hasta
que el estado lo dice. Colapsarlas produciría un embudo optimista.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Trabajar la cartera propia (Priority: P1)

Como Gerente de Ventas quiero ver mis prospectos, mis demos vigentes y qué se les notificó, y saber
que estoy viendo **solo lo mío**.

**Acceptance Scenarios**:

1. **Given** un GerenteVentas, **When** consulta `prospectos`, **Then** aparece el aviso de alcance
   **propios**, y el estado vacío dice que solo ve lo suyo.
2. **Given** un GerenteVentas, **When** intenta consultar la cartera de otro ejecutivo, **Then** el
   backend responde **403** y la pantalla lo muestra como acceso denegado, no como «sin resultados».
3. **Given** un DirectorMarketing, **When** consulta, **Then** **no** aparece aviso de alcance.
4. **Given** cualquier rol, **When** consulta, **Then** **ninguna** columna muestra correo ni
   teléfono del contacto.
5. **Given** el filtro **Ejecutivo**, **When** se despliega, **Then** es un **combobox de nombres**;
   la consulta viaja con el **id** y la tabla muestra el **nombre**.
6. **Given** un prospecto perdido, **When** aparece, **Then** su `motivo_perdida` está poblado y
   **`estado` no se deduce de `etapa_actual`**: son dos columnas.

---

### US-FE-2 — Supervisar los movimientos de cartera (Priority: P2)

Como Director de Marketing quiero ver cómo se ha movido la cartera entre ejecutivos.

**Acceptance Scenarios**:

1. **Given** un GerenteVentas o un GerenteCuentasPublicas, **When** entra a `reasignaciones`,
   **Then** es redirigido a `access-denied`, y el índice **no** se lo había ofrecido.
2. **Given** la **primera** asignación de un prospecto, **When** aparece, **Then**
   `ejecutivo_anterior` se ve **ausente** —no había ninguno— y `tipo_asignacion` lo dice.
3. **Given** el filtro de prospecto, **When** se despliega, **Then** es un **combobox** que envía
   `idprospecto` y la tabla muestra el **nombre de la empresa**, nunca el id.
4. **Given** el listado, **When** se abre, **Then** el título es **«Asignaciones de cartera»** y
   **no** hay columna «Servicio».

---

### Edge Cases

- **`ejecutivo_anterior` vacío.** ⚠️ Se ve ausente en muchas filas, y **eso es correcto**: son
  primeras asignaciones. Durante el repaso se sospechó un defecto de carga; el dato estaba bien y la
  hipótesis se descartó. Queda escrito para que nadie vuelva a «arreglarlo».
- **Demo sin expiración.** `dias_restantes` se ve ausente, **no** `0`: cero días restantes significa
  que expira hoy.
- **Prospecto sin ejecutivo asignado.** El ejecutivo se ve ausente y **la fila no se omite**.
- **Demos activas.** Sembradas el 2026-08-22: **tres**, con expiración a 3, 9 y 21 días, y escritas
  a propósito en los **tres formatos** que `demo_tokens.py` tolera —sufijo `Z`, sufijo `+00:00` y sin
  zona horaria—. Con un formato uniforme la comparación lexicográfica en SQL bastaría y el
  refinamiento en dos pasos del servicio no quedaría ejercitado, que es justo lo que había que ver.

---

## Requirements *(mandatory)*

- **FR-F01**: Una pantalla por listado más un índice, consumiendo la capa compartida.
- **FR-F02**: Las columnas MUST coincidir con el contrato OpenAPI.
- **FR-F03**: El aviso de alcance **propios** MUST mostrarse a los roles acotados, **también en el
  estado vacío**, y **MUST NOT** mostrarse a los amplios.
- **FR-F04**: ⛔ Las pantallas **MUST NOT** mostrar correo ni teléfono del contacto, **ni siquiera a
  la autoridad del departamento**.
- **FR-F05**: `estado` y `etapa_actual` MUST ser columnas independientes; la pantalla **MUST NOT**
  derivar una de la otra.
- **FR-F06**: `reasignaciones` MUST admitir **solo** roles amplios, y el índice **MUST NOT**
  ofrecerlo a quien el guard rechazaría.
- **FR-F07**: El listado MUST titularse **«Asignaciones de cartera»** y **MUST NOT** incluir columna
  «Servicio». El id de ruta `reasignaciones` se conserva.
- **FR-F08**: Los filtros **Ejecutivo** y **Prospecto** MUST ser comboboxes que **envían el id y
  muestran el nombre**. La tabla **MUST NOT** pintar ids.
- **FR-F09**: El rango de fechas MUST aparecer en `reasignaciones` y `notificaciones-enviadas`, y
  **no** en `prospectos` ni `demos-activas`, que son de estado actual.
- **FR-F10**: Un valor ausente —ejecutivo anterior, motivo de pérdida, días restantes— MUST verse
  ausente, y la fila **MUST NOT** omitirse.
- **FR-F11**: Un **403** MUST presentarse como acceso denegado, y **MUST NOT** confundirse con un
  resultado vacío.

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los cuatro listados se consultan con las columnas declaradas.
- **SC-F02**: Un GerenteVentas ve el aviso de propios; un DirectorMarketing **no** lo ve.
- **SC-F03**: **En ninguna** respuesta ni celda aparece correo o teléfono del contacto.
- **SC-F04**: Un rol acotado recibe negativa en `reasignaciones` **y** no lo ve en el índice.
- **SC-F05**: **Cero** ids pintados en celdas.
- **SC-F06**: Ninguna pantalla implementa tabla, paginación o manejo de error propio.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Conversión, embudo, pronóstico | Son compuestos, con denominador declarado |
| Correo y teléfono del contacto | ⛔ Exclusión constitucional |
| Sumar `valor_estimado` | Estimación por fila; una suma paginada sería falsa |
| Renombrar la ruta `reasignaciones` | Rompería enlaces guardados; solo cambia el título |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes` |
