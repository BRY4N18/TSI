# Tasks — Informes Tácticos Simples de Cuentas y Clientes (Frontend)

**Input**: [`spec.md`](spec.md), [`plan.md`](plan.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Tests**: incluidos y obligatorios. Tres de ellos —FR-F09, FR-F10 y FR-F18— son la razón de ser de
la capa compartida.

---

## ⚠️ Dependencia

`frontend/src/app/shared/informes/` completo y verde. **Este módulo la consume y no la modifica**: si
hiciera falta tocarla, la generalización quedó incompleta y la corrección va allí.

---

## Fase 1: Catálogo de definiciones

- [X] T001 Crear `definiciones/informes-cuentas.definiciones.ts` con las **ocho** definiciones:
      ruta, título, columnas y filtros, tomados **del contrato OpenAPI del backend**, no de memoria
- [X] T002 Marcar `transferencias-propiedad` como único listado con rango de fechas (`admiteRango`),
      porque es el único que el backend declara de hechos del período (FR-F06)
- [X] T003 Dar a `transferencias-propiedad` un mensaje vacío propio que advierta que **la fuente aún
      no se alimenta** (decisión #28, FR-F13). Sin él, un vacío permanente se lee como defecto
- [X] T004 [P] Prueba de que las columnas declaradas **coinciden con el contrato OpenAPI**, listado
      por listado (FR-F03). Es lo que impide que una pantalla muestre un campo que el backend no da
- [X] T005 [P] Prueba de que el enum de `estado` en `cuentas-por-estado` **coincide con el contrato**
      (plan D1): es una copia inevitable y esta prueba es lo que evita que se desactualice

## Fase 2: Acceso

- [X] T006 Crear `guards/informes-cuentas.guard.ts` (**Administrador**) y
      `guards/informes-accesos-tecnicos.guard.ts` (**Administrador o Director Tecnológico**),
      siguiendo el patrón de `emergencias-informes.guard.ts` (FR-F16)
- [X] T007 ⚠️ **Prueba de que el Director Tecnológico NO entra a los otros siete** — un guard único
      con la unión de roles se los daría, que es la contradicción que `acceso-tactico.md` §5 marca
- [X] T008 [P] Prueba de que un usuario sin rol es redirigido y **no** ve una tabla vacía (FR-F10)

## Fase 3: Las pantallas

- [X] T009 Crear `pages/informe/informe.page.ts`: resuelve la definición desde la ruta y la pasa a la
      capa compartida. **Una sola página parametrizada, no ocho** (FR-F02)
- [X] T010 Crear `pages/indice/indice-informes.page.ts`, generado **del mismo catálogo** que las
      páginas, para que no pueda ofrecer un informe que ya no existe (plan D3, FR-F04)
- [X] T011 Registrar `cuentas-clientes-informes.routes.ts` con las ocho rutas y el índice, cada una
      con su guard, y colgarlas de `app.routes.ts`
- [X] T012 Añadir la entrada de navegación en `shared/layout/nav-links.ts` con los roles correctos

## Fase 4: Pruebas de comportamiento

- [X] T013 [P] ⛔ **Prueba de que un `400` muestra el mensaje del backend y NO una tabla vacía**
      (FR-F09, SC-F03). Es la mitad del valor de la capa: un backend que rechaza y una pantalla que
      lo pinta como vacío desperdician exactamente el trabajo que costó rechazar
- [X] T014 [P] Prueba de que ese `400` **no ofrece «Reintentar»** y un `500` sí (FR-F11)
- [X] T015 [P] Prueba de que un `403` se distingue de un resultado vacío (FR-F10, SC-F04)
- [X] T016 [P] ⚠️ **Prueba de que un valor ausente no se muestra como cero ni como fecha de época**,
      contrastada con un `0` real que sí debe verse (FR-F18, SC-F05)
- [X] T017 [P] Prueba de que el selector de fechas **solo** aparece en `transferencias-propiedad`
      (FR-F06)
- [X] T018 [P] Prueba de que **no** aparece recuento total ni número de página navegable (FR-F14,
      SC-F06)
- [X] T019 [P] Prueba de que cambiar de filtros vuelve a la primera página (FR-F08)

## Fase 5: Cierre

- [X] T020 Ejecutar la suite completa del frontend y verificar que **nada existente se movió**
- [X] T021 Verificar que las ocho pantallas consumen la capa compartida y **ninguna** implementa
      tabla, paginación o manejo de error propio (SC-F02)
- [X] T022 **Recorrer las ocho pantallas en el navegador contra el stack levantado**, con especial
      atención a un `400` real, a un `403` real y al vacío de transferencias
- [X] T023 Documentar en `.specify/docs/changelog.md` y anotar si la capa compartida necesitó
      cambios — que es el resultado que este piloto existe para descubrir

---

## Riesgo principal

**T022 es lo que ninguna prueba unitaria sustituye.** Las pruebas de componente usan dobles; el
recorrido en navegador es lo único que comprueba que la ruta, el guard, el proxy y el backend real
encajan. Los seis departamentos siguientes se apoyarán en lo que aquí se valide.


---

## Resultado del piloto *(2026-08-15)*

**La hipótesis se confirma: declarar columnas y filtros basta para tener una pantalla.** Las ocho
salen de un catálogo y una sola página; ninguna implementa tabla, paginación ni manejo de error.

### La capa compartida necesitó tres cambios — y eso es el hallazgo, no un fallo

Es exactamente lo que este piloto existía para descubrir. Los tres se corrigieron **en
`shared/informes`**, no en una pantalla:

1. **Faltaba el formato `lista`.** Tres listados devuelven arreglos (`roles`, `roles_servidor`,
   `roles_negocio`) y se pintaban con las comas pegadas de `String(['a','b'])`. De paso quedó fijado
   que **un arreglo vacío es ausencia**: quien no tiene roles no tiene «cero roles».
2. **`controlClass` no existía.** Importé la constante de estilo y nunca la asigné. **Karma no lo
   detectó** —compila en JIT con comprobación más laxa—; lo encontró el build AOT al arrancar el
   servidor. Es la razón de que el recorrido en navegador no sea opcional.
3. **El pipe de números con locale fijo** lanzaba al renderizar. Ya usa el `LOCALE_ID` de la
   aplicación.

### Lo verificado en navegador contra el stack real

Con los contenedores reconstruidos —el de Django corría una imagen anterior a **todos** los informes,
que es la decisión #26—:

| Comprobación | Resultado |
|---|---|
| Las ocho pantallas con datos reales | ✅ |
| **`400` real** (`dias_minimo=-5`) | ✅ muestra el `detail` del backend, **sin** «Reintentar» y **sin** tabla vacía |
| Guard: Director Tecnológico en los siete | ✅ redirigido a `access-denied` |
| Guard: Director Tecnológico en accesos técnicos | ✅ entra |
| Índice filtrado por rol | ✅ al Director Tecnológico le ofrece **solo** el suyo |
| Ausentes | ✅ guion, nunca `0` ni fecha de época |
| Vacío de transferencias | ✅ explica la decisión #28 |
| Rango de fechas | ✅ solo en transferencias |
| Recuento total | ✅ no aparece |

### Lo que este piloto NO validó

**`meta.acotado_a`**, porque ninguno de los ocho listados de este departamento acota. Queda cubierto
solo por pruebas de componente. **Se cierra con el siguiente departamento acotado.**
