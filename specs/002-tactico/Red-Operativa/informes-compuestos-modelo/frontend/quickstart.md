# Quickstart — Tres pantallas Z, dos audiencias (Red Operativa)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso. La más fácil de olvidar es la **exclusión
cruzada**: un menú que muestra las tres a ambos directores no produce error, solo consecuencias.

## Prerrequisitos

- Backend de los 15 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios demo (clave `Tactico2026!`):
  - Expansión: `director.expansion@demo.tsi.com`
  - Tecnológico: `director.tecnologico@demo.tsi.com`
  - Un Cliente o Proveedor de demo para la exclusión.

## 1. Expansión entra a Flota; Tecnológico no la ve

Abrir `http://localhost:4200/red-operativa/gestion/flota` como Director de Expansión.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`). El
menú muestra **Flota y cobertura** y **Mercados y retirada**. **No** muestra Criterios de
validación.

Como Director Tecnológico, la misma URL → access-denied, y esas dos etiquetas **no están** en su
menú.

## 2. Tecnológico entra a Validación; Expansión no la ve

`/red-operativa/gestion/validacion` como Tecnológico.

**Esperado:** héroe = tasa al primer intento. Lectura nombra **intentos**, no regiones. El menú
muestra Criterios de validación y **no** Flota ni Mercados.

Como Expansión, la misma URL → access-denied.

## 3. Flota: En Misión, ausente y sin alternativas

Período con transiciones reales.

**Esperado:**

- El visual de estados incluye **En Misión** si el período lo tiene (no desaparece por catálogo).
- Una unidad sin transiciones se lee **ausente** en disponibilidad, no 0 %.
- Un condado crítico sin vecinos se lee **sin alternativas**.
- El umbral se ve (convención, no política).
- Los cinco de apoyo **plegados**. Recuento de bloques de la vista principal ≤ 8.

## 4. Mercados: convención de 30 días y medida exacta

`/red-operativa/gestion/mercados` como Expansión.

**Esperado:**

- Héroe = mercados activos (ciclo de vida, no geografía).
- Visual de puesta en operación: región aún no en producción → días **ausentes**, no 0 ni
  incumplimiento. Texto de que el objetivo es convención.
- Lectura de regiones en riesgo con umbral visible.
- Apoyo de despublicación: aunque `data` esté vacío, se ve **desde cuándo la medida es exacta**.
  Ese vacío no se lee como «nunca pasó».

## 5. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `bajas-forzadas`).

**Esperado:** esa zona (o el apoyo) en error; héroe y visual siguen.

## 6. El índice de listados no cambió

`/red-operativa/informes` como Expansión / Tecnológico / Proveedor sigue siendo el índice de
listados. **No** hay tarjetas Z ahí. El Proveedor **no** gana Flota y cobertura de gestión.

## 7. Nada sensible

Recorrer las tres: ninguna coordenada, ningún nombre de validador, ningún mapa, ningún contacto de
proveedor.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Editor de umbral o de plazo (no existe; se leen de `meta`).
- Relación región↔condado (decisión #38: la pantalla declara el hueco, no lo inventa).
- Frontend de otros departamentos.
