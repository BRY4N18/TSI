# Tasks — Informes Tácticos Simples de Ventas y CRM (Frontend)

**Input**: [`spec.md`](spec.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Precedente**: Cuentas y Clientes (piloto), Soporte al Cliente, Emergencias, Red Operativa y
Suscripciones. Misma estructura, **sin volver a decidirla**.

> ⚠️ **Esta lista se redactó después de construir el módulo** (2026-08-22), durante el repaso
> click a click de toda la capa táctica. Las tareas están `[X]` porque describen trabajo ya
> ejecutado y verificado, no trabajo planificado.

---

## Fase 1: Catálogo

- [X] T001 Crear `definiciones/informes-ventas.definiciones.ts` con los **cuatro** listados,
      columnas y filtros del contrato
- [X] T002 Declarar `INFORME_REASIGNACIONES` como constante: la usan el guard y el índice, de modo
      que la regla de supervisión se escribe **una sola vez**
- [X] T003 Marcar `prospectos` y `demos-activas` como **sin rango de fechas** — son de estado
      actual (FR-F09)
- [X] T004 Declarar `estado` y `etapa_actual` como **dos columnas**, sin derivar una de la otra
      (FR-F05)
- [X] T005 [P] Prueba de que columnas y enums coinciden con el contrato
- [X] T006 [P] ⛔ **Prueba de que ninguna definición declara correo ni teléfono del contacto**
      (FR-F04, SC-F03). El catálogo es donde se añadiría sin pensarlo

## Fase 2: Acceso

- [X] T007 Crear los dos guards: tres listados admiten gerentes acotados, `reasignaciones` **solo**
      amplios (FR-F06)
- [X] T008 [P] ⛔ **Prueba de que un GerenteVentas no entra a `reasignaciones`** — quien está dentro
      de un movimiento de cartera es parte interesada, no supervisor
- [X] T009 [P] Prueba de que **GerenteCuentasPublicas recibe el mismo trato** que GerenteVentas: son
      dos carteras, una sola regla
- [X] T010 [P] Prueba de que `listadosVisiblesPara` **oculta** `reasignaciones` a los acotados, en
      vez de ofrecerlo para que el guard lo rechace después (SC-F04)

## Fase 3: Pantallas

- [X] T011 Página parametrizada e índice, con el patrón ya establecido
- [X] T012 Registrar rutas y la entrada de navegación

## Fase 4: Filtros por catálogo

- [X] T013 Convertir **Ejecutivo** y **Prospecto** de campo de id a **combobox**: la consulta viaja
      con el id, la tabla muestra el nombre (FR-F08)
- [X] T014 [P] Prueba de que la consulta lleva el **id** y la celda pinta el **nombre**

## Fase 5: Nombres y comportamiento

- [X] T015 Renombrar el listado a **«Asignaciones de cartera»** y **quitar la columna «Servicio»**
      (FR-F07)

      > El título decía «Reasignaciones» y el listado incluye la **primera** asignación de un
      > prospecto, que no reasigna nada; `tipo_asignacion` ya distinguía ambos casos. La columna
      > «Servicio» no aportaba nada al movimiento de cartera. El id de ruta se conserva para no
      > romper enlaces guardados.

- [X] T016 [P] ⛔ **Prueba de que el aviso de `propios` sale también en el estado vacío** (FR-F03)
- [X] T017 [P] Prueba de que un **403** se presenta como acceso denegado y **no** como listado
      vacío (FR-F11)
- [X] T018 [P] Prueba de que un prospecto perdido conserva `motivo_perdida` y que **estado no se
      deriva de la etapa** (FR-F05)
- [X] T019 [P] Prueba de que `dias_restantes` ausente **no** se pinta `0`, contrastada con una demo
      que expira hoy
- [X] T020 [P] Prueba de que `ejecutivo_anterior` ausente en una **primera** asignación es correcto
      y **la fila no se omite** (FR-F10)

## Fase 6: Cierre

- [X] T021 Suite completa del frontend verde
- [X] T022 **Verificar en navegador con el actor correspondiente** —DirectorMarketing y un
      GerenteVentas—, **no con Administrador**
- [X] T023 Documentar en el changelog

---

## Riesgo principal

**T008 y T016.** T008 fija la única regla de acceso que no se adivina: el supervisado no supervisa.
T016 valida `propios` en el sitio donde más se olvida —el estado vacío—, que es justo cuando el
usuario más necesita saber si no hay nada o si no lo está viendo.

---

## Resultado *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `prospectos` con **DirectorMarketing** | ✅ sin aviso de alcance |
| `prospectos` con **GerenteVentas** | ✅ solo su cartera, con aviso de `propios` |
| Cartera de otro ejecutivo | ✅ **403**, mostrado como acceso denegado |
| **GerenteVentas** en `reasignaciones` | ✅ `access-denied`, y ausente del índice |
| **Sin correo ni teléfono** del contacto | ✅ |
| Combobox de Ejecutivo / Prospecto | ✅ envía id, pinta nombre |
| Título «Asignaciones de cartera», sin columna «Servicio» | ✅ |

### Una sospecha que resultó ser el dato correcto

`ejecutivo_anterior` sale **vacío en muchas filas**, y durante el repaso se tomó por un fallo de
carga. No lo era: son **primeras asignaciones**, y `tipo_asignacion` ya lo declara en la misma fila.
Se deja escrito aquí porque una ausencia legítima que parece un defecto se «arregla» sola la segunda
vez que alguien la mira.

### El caso que faltaba, sembrado *(2026-08-22)*

- [X] T024 Sembrar demos activas en los tres formatos de expiración
      (`database/seed_casos_borde_informes.py`)

| Caso | Resultado |
|---|---|
| `demos-activas` con **DirectorMarketing** | ✅ 3 filas |
| Orden ascendente: las que vencen antes, primero | ✅ 3, 9 y 21 días restantes |
| Sufijos `Z`, `+00:00` y **sin zona** | ✅ las tres pasan el prefiltro y salen normalizadas a ISO |

El seed elige los prospectos **por id** y no por «no tiene demo». Con el segundo criterio la segunda
ejecución habría elegido otros tres y cada pasada sumaría tres demos: dejaba de ser idempotente.

### Recorrido en navegador con los datos sembrados *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `demos-activas` con **DirectorMarketing** | ✅ 3 filas |
| Orden: las que vencen antes, primero | ✅ 3, 9 y 21 días restantes |
| Los tres formatos de expiración | ✅ las tres se pintan como fecha legible, ninguna cruda |
| Correo y teléfono del contacto | ✅ **ausentes** de la tabla |
