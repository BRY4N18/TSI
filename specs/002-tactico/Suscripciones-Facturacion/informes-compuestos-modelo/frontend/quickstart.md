# Quickstart — Tres pantallas Z, dos audiencias (Suscripciones y Facturación)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso. La más fácil de olvidar es la **exclusión
cruzada**: un menú que muestra las tres a ambos directores no produce error, solo consecuencias.

## Prerrequisitos

- Backend de los 13 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios demo (clave `Tactico2026!`):
  - Financiero: `director.financiero@demo.tsi.com`
  - Estrategia: `director.estrategia@demo.tsi.com`
- Un Cliente o un Operador de demo para la exclusión.

## 1. El Financiero entra a Cobro; Estrategia no la ve

Abrir `http://localhost:4200/suscripciones/gestion/cobro` como Director Financiero.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-mes`, `zona-visual`,
`zona-lectura`). El menú muestra **Cobro e ingreso** y **Movimientos de cartera**. **No** muestra
Catálogo y uso. `zona-mes` declara el mes natural.

Como Director de Estrategia, la misma URL → access-denied, y esas dos etiquetas **no están** en su
menú.

## 2. Estrategia entra a Catálogo; el Financiero no la ve

`/suscripciones/gestion/catalogo` como Director de Estrategia.

**Esperado:** héroe = distribución (clientes e ingreso **por separado**). Visual = utilizado y
contratado, con `nota_dimension_pendiente`. **Ninguna** zona se titula llamadas. El menú muestra
Catálogo y uso y **no** Cobro ni Movimientos.

Como Financiero, la misma URL → access-denied.

## 3. Cobro: cancelada fuera, notas restan, sin periodicidad aparte

Período con datos reales (p. ej. 2026) en Cobro.

**Esperado:**

- El héroe de MRR **no** incluye el precio de una suscripción cancelada.
- `sin_periodicidad` se ve aparte, no como 0 de ingreso.
- El visual de ingresos muestra `notas_credito`; el neto es menor que el facturado si hay crédito.
- Dunning y «sin método» **plegados**. Recuento de bloques de la vista principal ≤ 8.
- Un período 1999 → vacío, no 0 %.

## 4. Movimientos: NRR de existentes, pendiente aparte, delta de precio

`/suscripciones/gestion/movimientos` como Financiero.

**Esperado:**

- Héroe = NRR con componentes; `zona-mes` visible.
- Un cambio a un plan de nivel «superior» más barato se lee como **downgrade** (el tipo llega del
  backend; no se retitula).
- Lectura de tiempo: `pendientes` visible; la mediana no mejora con solicitudes abiertas.
- Apoyo de suspensión **plegado**. Sin nombre de quien resolvió.

## 5. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `efectividad-dunning`).

**Esperado:** esa zona (o el apoyo) en error; héroe y visual siguen.

## 6. El índice de listados y el catálogo de planes no cambiaron

`/suscripciones/informes` sigue siendo el índice de listados (Cliente entra a **su** cuenta).
`/suscripciones/catalogo-planes` sigue siendo el catálogo operativo. **No** hay tarjetas Z ahí. El
Cliente **no** gana Cobro e ingreso.

## 7. Nada sensible

Recorrer las tres: ningún token, últimos dígitos, fiscal, mapa ni identidad de administrador. El
apoyo de «sin método», si se abre, muestra **nombre comercial** y caducidad, no el instrumento, y
**no** enlaza a métodos de pago.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Editor de escalones de dunning o de días de aviso (no existe; se leen de `meta`).
- Consumo de llamadas API (el backend no lo entrega; la pantalla no lo inventa).
- Frontend de Emergencias, Red Operativa o Ventas.
- Ampliar el acceso a Cliente o Proveedor (el backend no lo admite).
