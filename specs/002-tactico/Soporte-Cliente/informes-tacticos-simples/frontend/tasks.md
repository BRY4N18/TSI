# Tasks — Informes Tácticos Simples de Soporte al Cliente (Frontend)

**Input**: [`spec.md`](spec.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Precedente**: el piloto de Cuentas y Clientes. Se sigue su misma estructura —catálogo de
definiciones, una página parametrizada, guards por permiso— y **no se vuelve a decidir**.

---

## Fase 0: Contrato

- [X] T001 Declarar en el contrato OpenAPI del backend el `enum` de `estado`, que el backend **sí**
      valida y el contrato dejaba como texto libre; y extender la prueba de conformidad para que no
      pueda divergir. Sin esto, el frontend no puede ofrecer un desplegable sin copiar de un sitio
      que nadie comprueba

## Fase 1: Catálogo

- [X] T002 Crear `definiciones/informes-soporte.definiciones.ts` con los **dos** listados, columnas
      y filtros tomados del contrato
- [X] T003 Marcar `escalados` como único con rango de fechas (FR-F07)
- [X] T004 [P] Prueba de que columnas y enums coinciden con el contrato

## Fase 2: Acceso

- [X] T005 Crear los dos guards: `tickets` admite atención **y** reporte; `escalados`, **solo**
      atención (FR-F08)
- [X] T006 [P] ⚠️ Prueba de que un reportador **entra a tickets y no a escalados** — es la asimetría
      del departamento, y un guard único la borraría

## Fase 3: Pantallas

- [X] T007 Crear página parametrizada e índice, con el mismo patrón del piloto
- [X] T008 Registrar rutas y añadir la entrada de navegación con los roles correctos

## Fase 4: Pruebas — lo que este módulo viene a cerrar

- [X] T009 [P] ⛔ **Prueba de que `acotado_a: propios` produce aviso y `todos` NO** (FR-F04, FR-F05,
      SC-F02). Es la garantía que el piloto no pudo validar
- [X] T010 [P] ⛔ **Prueba de que el estado vacío acotado menciona el acotamiento** (SC-F03). Es
      cuando no hay filas cuando «no hay» y «no hay de los tuyos» se leen igual
- [X] T011 [P] Prueba de que un escalado automático se ve **sin autor** y no atribuido a nadie
      (SC-F05)
- [X] T012 [P] Prueba de que un ticket sin agente ni factura **no se omite** y sus celdas se ven
      ausentes (FR-F10)

## Fase 5: Cierre

- [X] T013 Suite completa del frontend verde
- [X] T014 **Verificar en navegador con dos roles distintos**: un Agente (sin aviso) y un Cliente
      (con aviso, y con el estado vacío acotado). Es lo que cierra el hueco del piloto
- [X] T015 Documentar en el changelog y **declarar que `acotado_a` queda validado de punta a punta**

---

## Riesgo principal

**T014 es la razón de haber elegido este departamento.** Si el aviso no aparece contra el backend
real, la capa compartida tiene un defecto que los cinco departamentos restantes heredarían.


---

## Resultado *(2026-08-15)*

**`acotado_a` queda validado de punta a punta contra el backend real.** Era el hueco que dejó el
piloto, y era la razón de haber elegido este departamento.

| Comprobación | Resultado |
|---|---|
| Rol **Soporte** → `todos` | ✅ 14 filas de varias cuentas, **sin aviso** |
| Rol **Cliente** → `propios` | ✅ 12 filas de **una sola cuenta**, con «Solo se muestran tus registros» |
| **Estado vacío acotado** | ✅ «No hay tickets con esos criterios. **No hay resultados entre tus registros.**» |
| **`403` real** (cliente sin cuenta resuelta) | ✅ muestra el mensaje del backend, distinguido de una lista vacía |
| Guard: Cliente en escalados | ✅ redirigido a `access-denied` |
| Índice filtrado por rol | ✅ al Cliente le ofrece **solo** tickets |
| Enumeraciones | ✅ los 7 estados y las 5 situaciones del contrato |

### Un hueco de contrato cerrado de paso

El contrato del backend declaraba `estado` como **texto libre**, pero el backend **sí** lo valida
contra las constantes del dominio. Sin el `enum` declarado, la pantalla no podía ofrecer un
desplegable sin copiar de un sitio que nadie comprueba. Se añadió al contrato y se extendió la prueba
de conformidad para que no pueda divergir.

### Una regla de navegación que NO se rompió

`PartnerIntegracion` **no** tiene enlace en el sidebar, y no es un descuido: **FR-UI-033** dice que la
consola de Partners y su portal no se fusionan y que ningún rol descubre la existencia del otro
departamento. Una prueba existente lo verifica, y añadir el enlace la ponía en rojo.

El backend **sí** le permite el listado —puede abrir una disputa de facturación y ve solo sus
tickets—, así que la ruta le responde si llega a ella. **Lo que no tiene es un enlace.** Queda como
decisión de producto, no resuelta por conveniencia.
