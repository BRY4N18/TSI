# Tasks — Informes Tácticos Simples de Suscripciones y Facturación (Frontend)

**Input**: [`spec.md`](spec.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Precedente**: Cuentas y Clientes (piloto), Soporte al Cliente, Emergencias y Red Operativa. Misma
estructura, **sin volver a decidirla**.

> ⚠️ **Esta lista se redactó después de construir el módulo** (2026-08-22), durante el repaso
> click a click de toda la capa táctica. Las tareas están `[X]` porque describen trabajo ya
> ejecutado y verificado, no trabajo planificado.

---

## Fase 1: Catálogo

- [X] T001 Crear `definiciones/informes-suscripciones.definiciones.ts` con los **cuatro** listados,
      columnas y filtros del contrato
- [X] T002 Declarar `INFORMES_FINANZAS` como la lista que parte el departamento en dos materias —
      la usan el guard y el índice, y así la separación se define **una sola vez**
- [X] T003 Marcar `facturas` como **único con rango de fechas**; `vence_en_dias` y `caduca_en_dias`
      son filtros de columna, no período (FR-F07)
- [X] T004 [P] Prueba de que columnas y enums coinciden con el contrato
- [X] T005 [P] ⛔ **Prueba de que ninguna definición declara número de tarjeta, token, titular ni
      CVV** (FR-F03, SC-F02). Es exclusión constitucional y el catálogo es donde se rompería

## Fase 2: Acceso

- [X] T006 Crear los dos guards, `informesFinanzasGuard` e `informesCatalogoGuard` (FR-F04)
- [X] T007 [P] ⛔ **Prueba de que las dos autoridades no se mezclan**: Estrategia no entra a
      finanzas, Financiero no entra a catálogo
- [X] T008 [P] Prueba de que `listadosVisiblesPara` reparte los cuatro informes usando
      `INFORMES_FINANZAS`, sin repetir la regla (FR-F10)

## Fase 3: Pantallas

- [X] T009 Página parametrizada e índice, con el patrón ya establecido
- [X] T010 Registrar rutas y la entrada de navegación

## Fase 4: Filtros por catálogo

- [X] T011 Convertir **Cuenta** de campo de id a **combobox de razones sociales**: la consulta viaja
      con el id, la tabla muestra el nombre (FR-F08). Aplica a los cuatro listados
- [X] T012 [P] Prueba de que la consulta lleva el **id** y la celda pinta la **razón social**

## Fase 5: Ausencia y formato

- [X] T013 ⚠️ Cambiar `dias_espera` por **`minutos_espera`** en el servicio y formatear por
      magnitud con `duracionLegible` (FR-F06)

      > **El defecto que motivó la tarea.** El servicio devolvía días enteros, así que toda espera
      > de menos de 24 h se pintaba **«0 días»** — la mayoría de ellas. La columna parecía correcta
      > y estaba diciendo que nadie espera nada.

- [X] T014 [P] Prueba de que `dias_mora` ausente **no** se pinta `0`, contrastada con una factura
      realmente al día (FR-F05)
- [X] T015 [P] Prueba de que `motivo_cancelacion` y `fecha_cancelacion` están **solo** en las
      suscripciones canceladas
- [X] T016 [P] Prueba de que `motivo_rechazo` está **solo** en las solicitudes rechazadas
- [X] T017 [P] Prueba de que `renovacion_automatica` se pinta sí/no y no `true`/`false`
- [X] T018 [P] Prueba de que el rango de fechas aparece **solo** en `facturas` (FR-F07)

## Fase 6: Cierre

- [X] T019 Suite completa del frontend verde
- [X] T020 **Verificar en navegador con los dos actores** —DirectorFinanciero y DirectorEstrategia—,
      **no con Administrador**
- [X] T021 Documentar en el changelog

---

## Riesgo principal

**T005 y T007.** T005 protege el dato más sensible de toda la capa táctica en el único sitio donde
se puede añadir por descuido. T007 fija que la separación finanzas/catálogo es **de materia**: no se
arregla dando más alcance, porque no es un problema de alcance.

---

## Resultado *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `facturas` y `metodos-pago` con **DirectorFinanciero** | ✅ |
| `suscripciones` y `solicitudes-cambio-plan` con **DirectorEstrategia** | ✅ |
| Estrategia en `facturas` / Financiero en `suscripciones` | ✅ `access-denied` en ambos sentidos |
| **Sin identificador de pago** en ninguna respuesta ni celda | ✅ |
| Combobox de Cuenta | ✅ envía id, pinta razón social |
| Espera de cambio de plan | ✅ «19 min» en vez de «0 días» |
| `dias_mora` ausente ≠ `0` | ✅ |

### Los dos casos que faltaban, sembrados *(2026-08-22)*

- [X] T022 Sembrar factura `En disputa` y cuenta dada de baja
      (`database/seed_casos_borde_informes.py`)

| Caso | Resultado |
|---|---|
| Factura `En disputa`, vencida hace 40 días | ✅ aparece **sin `dias_mora`** |
| Factura `Pendiente` vencida, misma página | ✅ `dias_mora: 13` — el contraste es visible |
| Cuenta `Dado de baja` en `cuentas-por-estado` | ✅ la fila **sobrevive** con su razón social |

⚠️ La cuenta se sembró **nueva y sin personal**. Marcar de baja una existente habría dejado a sus
usuarios sin poder iniciar sesión: desde la corrección B9 el login comprueba las cuentas del
usuario. Un fixture de informe no puede tener ese efecto.

> **Lección.** `dias_espera` pasó las pruebas durante semanas porque `0` es un entero perfectamente
> válido. Una unidad demasiado gruesa no rompe nada: convierte el dato en ceros y los ceros no se
> denuncian solos.

### Recorrido en navegador con los datos sembrados *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `facturas` con **DirectorFinanciero** | ✅ |
| Factura `En disputa` vencida el 13/07 | ✅ «Días de mora: —» |
| Factura `Pendiente` vencida el 08/08, misma pantalla | ✅ «Días de mora: 13» |
| Aviso de la pantalla | ✅ «"En disputa" no es impaga: el sistema dejó de cobrarla a propósito» |
| Identificador de pago en alguna celda | ✅ ninguno |

**Un requisito propio que resultó estar mal.** FR-F09 exigía mostrar los importes «con su moneda».
Al ver la pantalla quedó claro que **el sistema no almacena moneda en ninguna tabla**: el requisito
se había escrito por analogía y sin comprobarlo. Corregido en la spec; el detalle de decimales
desiguales queda anotado en `decisiones-pendientes.md`.
