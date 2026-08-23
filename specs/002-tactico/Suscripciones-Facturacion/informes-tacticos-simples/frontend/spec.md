# Feature Specification: Informes Tácticos Simples de Suscripciones y Facturación (Frontend)

**Feature Branch / capa**: `002-tactico/Suscripciones-Facturacion/informes-tacticos-simples/frontend`

**Created**: 2026-08-22

**Status**: Implemented *(retro-spec: documenta lo construido y lo verificado en navegador)*

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) y su contrato OpenAPI.

**Gobierna**: [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## Contexto

Cuatro listados, y el único departamento donde **el dato es dinero**. Eso impone dos cosas que
ningún otro módulo táctico tiene que resolver.

**1. La autoridad se parte por materia, no por alcance.**

| Materia | Listados | Quién entra |
|---|---|---|
| **Finanzas** | `facturas`, `metodos-pago` | Administrador, **DirectorFinanciero** |
| **Catálogo** | `suscripciones`, `solicitudes-cambio-plan` | Administrador, **DirectorEstrategia** |

Ambos guards admiten además a los acotados —Cliente y Proveedor—, que ven lo suyo. Lo que **no**
pasa es que Estrategia vea facturas ni que Finanzas vea el catálogo de planes: quien decide la
oferta y quien cobra son cargos distintos.

**2. ⛔ Ningún listado publica un identificador de pago.**

`metodos-pago` muestra `tipo`, `ultimos_digitos` y `fecha_expiracion`. **No** hay número de tarjeta,
ni token de la pasarela, ni titular, ni CVV — ni siquiera para el Director Financiero. Es exclusión
constitucional, no de acotamiento, y por eso la prueba que la protege vive en el catálogo de
columnas: ahí es donde alguien la rompería sin darse cuenta.

### Lo que la pantalla NO puede intentar

**No calcula ingresos, morosidad ni churn.** Todo eso es compuesto y tiene su propio denominador
declarado en los informes de gestión. Sumar la columna `monto_total` de una página paginada daría un
número plausible y falso.

**No cobra ni reintenta.** Los listados son de lectura. `reintentos` dice cuántos hubo; no ofrece
hacer otro.

**No traduce estados de pago a semáforos de riesgo.** «Vencida» es un hecho; «en riesgo» es un
juicio, y el juicio lo emite el modelo analítico, no la tabla.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Ver la facturación y sus medios de cobro (Priority: P1)

Como Director Financiero quiero ver qué se facturó, qué está vencido y qué medios de pago están por
caducar.

**Acceptance Scenarios**:

1. **Given** un **DirectorEstrategia**, **When** entra a `facturas` o a `metodos-pago`, **Then** es
   redirigido a `access-denied`.
2. **Given** cualquier rol, **When** consulta `metodos-pago`, **Then** **no** aparece número de
   tarjeta, token, titular ni CVV: solo tipo, últimos dígitos y expiración.
3. **Given** una factura al corriente, **When** aparece, **Then** `dias_mora` se ve **ausente**,
   nunca `0`: cero días de mora y «no está en mora» no son lo mismo.
4. **Given** `facturas`, **When** se abre, **Then** ofrece **rango de fechas** —es el único de los
   cuatro que lo hace— y el filtro **Vencidas**.
5. **Given** el filtro **Cuenta**, **When** se despliega, **Then** es un **combobox de razones
   sociales**; la consulta viaja con el **id** y la tabla muestra el **nombre**.

---

### US-FE-2 — Ver el catálogo contratado y sus cambios (Priority: P2)

Como Director de Estrategia quiero ver qué planes están contratados y qué cambios se piden.

**Acceptance Scenarios**:

1. **Given** un **DirectorFinanciero**, **When** entra a `suscripciones` o a
   `solicitudes-cambio-plan`, **Then** es redirigido a `access-denied`.
2. **Given** una suscripción activa, **When** aparece, **Then** `motivo_cancelacion` y
   `fecha_cancelacion` se ven **ausentes** — están poblados **solo** cuando aplica.
3. **Given** una solicitud resuelta favorablemente, **When** aparece, **Then** `motivo_rechazo` se ve
   **ausente**; el rechazo es lo excepcional, no el valor por defecto.
4. **Given** una espera de cambio de plan, **When** se pinta `minutos_espera`, **Then** se muestra
   **según su magnitud** —«19 min», «1.5 h», «3.0 días»— y nunca como un entero desnudo.
5. **Given** `suscripciones`, **When** se abre, **Then** **no** ofrece rango de fechas; los filtros
   de vencimiento (`vence_en_dias`) y de caducidad (`caduca_en_dias`) son **columnas**, no período.

---

### Edge Cases

- **`minutos_espera` era `dias_espera`.** ⚠️ El servicio devolvía días enteros, así que **toda espera
  de menos de 24 h se pintaba «0 días»** — que es la mayoría. Se cambió la unidad a minutos y el
  formato pasó a elegirse por magnitud. Corregido el 2026-08-22.
- **Factura `En disputa`.** Sembrada el 2026-08-22, **vencida hace 40 días y sin `dias_mora`**.
  `ESTADOS_EN_MORA` son `Pendiente` y `Fallida`; «en disputa» no acumula mora. El contraste se ve
  ahora en la misma página: una `Pendiente` vencida muestra 13 días de mora y la disputada, ninguno.
- **Cuenta dada de baja.** Sembrada, y ⚠️ **sin personal asignado**: marcar de baja una cuenta con
  usuarios les impide iniciar sesión (corrección B9 del changelog). Un caso de borde para un informe
  no puede sacar gente del sistema.
- **Renovación automática.** Es booleano y se pinta como sí/no, **no** como `true`/`false`.

---

## Requirements *(mandatory)*

- **FR-F01**: Una pantalla por listado más un índice, consumiendo la capa compartida.
- **FR-F02**: Las columnas MUST coincidir con el contrato OpenAPI.
- **FR-F03**: ⛔ **Ninguna pantalla MUST mostrar identificador de pago** —número, token, titular,
  CVV—, **ni siquiera a la autoridad financiera**. Exclusión constitucional.
- **FR-F04**: Los dos guards MUST separar finanzas de catálogo. **DirectorEstrategia MUST NOT** ver
  `facturas` ni `metodos-pago`; **DirectorFinanciero MUST NOT** ver `suscripciones` ni
  `solicitudes-cambio-plan`.
- **FR-F05**: `dias_mora`, `motivo_cancelacion`, `fecha_cancelacion` y `motivo_rechazo` MUST verse
  **ausentes** cuando no aplican, y **MUST NOT** pintarse como `0` ni como cadena vacía.
- **FR-F06**: `minutos_espera` MUST formatearse **por magnitud** mediante la utilidad compartida
  `duracionLegible`.
- **FR-F07**: El rango de fechas MUST aparecer **solo** en `facturas`. Los umbrales
  `vence_en_dias` y `caduca_en_dias` son filtros de columna y **MUST NOT** presentarse como período.
- **FR-F08**: El filtro **Cuenta** MUST ser un combobox que **envía el id y muestra la razón
  social**. La tabla **MUST NOT** pintar ids.
- **FR-F09**: Los importes MUST declararse con formato **`moneda`**, que los pinta **siempre con
  dos decimales** y **sin símbolo de divisa**.

  > ⚠️ **Este requisito decía «con su moneda» y estaba mal.** Se escribió por analogía, sin
  > comprobarlo: **el sistema no almacena moneda en ninguna parte**. `Fact_Factura` no tiene
  > columna, y el único «moneda» del repositorio es una *etiqueta de unidad* de la capa
  > estratégica, no un código de divisa. Un símbolo en la celda lo habría inventado el frontend.
  > Corregido el 2026-08-22, al ver la pantalla con datos.
  >
  > **Ampliado el mismo día.** El requisito ahora exige además **dos decimales siempre**: la
  > columna mezclaba `49`, `63.5` y `166.88` en filas contiguas y no se podía comparar leyendo
  > hacia abajo. Lo garantiza el formato `moneda` del catálogo de columnas, creado para esto.
  > `numero` se queda sin rellenar: un conteo de 4 unidades no es `4.00`.
- **FR-F10**: El índice MUST listar **solo** los informes que el rol puede abrir
  (`listadosVisiblesPara`).

---

## Success Criteria *(mandatory)*

- **SC-F01**: Los cuatro listados se consultan con las columnas declaradas.
- **SC-F02**: **En ninguna** respuesta ni celda aparece un identificador de pago.
- **SC-F03**: Estrategia y Finanzas ven **conjuntos disjuntos** de dos informes cada uno.
- **SC-F04**: **Cero** valores no aplicables pintados como `0`.
- **SC-F05**: Ninguna espera se muestra como «0 días».
- **SC-F06**: Ninguna pantalla implementa tabla, paginación o manejo de error propio.

---

## Fuera de alcance

| Excluido | Por qué |
|---|---|
| Ingresos, morosidad, churn | Son compuestos, con denominador declarado |
| Identificadores de pago | ⛔ Exclusión constitucional |
| Cobrar o reintentar | Los listados son de lectura |
| Semáforos de riesgo | Juicio del modelo analítico, no de la tabla |
| Modificar la capa compartida | Si hace falta, la corrección va a `shared/informes` |
