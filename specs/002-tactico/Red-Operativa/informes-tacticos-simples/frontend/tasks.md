# Tasks — Informes Tácticos Simples de Red Operativa (Frontend)

**Input**: [`spec.md`](spec.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Precedente**: Cuentas y Clientes (piloto), Soporte al Cliente y Emergencias. Misma estructura,
**sin volver a decidirla**.

> ⚠️ **Esta lista se redactó después de construir el módulo** (2026-08-22), durante el repaso
> click a click de toda la capa táctica. Las tareas están marcadas `[X]` porque describen trabajo
> ya ejecutado y verificado, no trabajo planificado. Se escribe para que el módulo tenga la misma
> contraparte documental que los demás departamentos.

---

## Fase 1: Catálogo

- [X] T001 Crear `definiciones/informes-red-operativa.definiciones.ts` con los **cuatro** listados,
      columnas y filtros del contrato
- [X] T002 Marcar `flota` y `regiones` como **sin rango de fechas** — son de estado actual;
      `bajas-unidad` y `validaciones-region` sí lo llevan (FR-F08)
- [X] T003 Etiquetar `estado_geografico` como **«Estado geográfico»** y `estado_region` como
      **«Estado»**: conviven en la misma tabla y el sustantivo suelto es ambiguo (FR-F06)
- [X] T004 Etiquetar `dado_de_alta` como alta administrativa y **no** declarar ninguna columna de
      disponibilidad (FR-F05)
- [X] T005 [P] Prueba de que columnas y enums coinciden con el contrato
- [X] T006 [P] ⛔ **Prueba de que ninguna definición declara coordenadas, polígonos ni contacto del
      proveedor** (FR-F04, SC-F03). El catálogo es el sitio donde alguien lo rompería

## Fase 2: Acceso

- [X] T007 Crear los **tres** guards con el reparto por materia: flota (Expansión + acotados),
      regiones (Tecnológico + Expansión), validaciones (Tecnológico) (FR-F07)
- [X] T008 [P] ⚠️ Prueba de que un **Proveedor entra a flota y NO a regiones ni a validaciones** —
      una región no pertenece a ninguna empresa de flota
- [X] T009 [P] Prueba de que un **DirectorExpansion no entra a `validaciones-region`**: la
      validación es materia del Director Tecnológico
- [X] T010 [P] Prueba de que `listadosVisiblesPara` no ofrece en el índice lo que el guard
      rechazaría (FR-F10)

## Fase 3: Pantallas

- [X] T011 Página parametrizada e índice, con el patrón ya establecido
- [X] T012 Registrar rutas y la entrada de navegación

## Fase 4: Filtros por catálogo

- [X] T013 Convertir **Proveedor**, **Condado** y **Región** de campo de id a **combobox**: la
      consulta viaja con el id, la tabla muestra el nombre (FR-F03)

      > Antes se pedía teclear el número. El filtro existía y era inusable: nadie conoce el
      > `idregionoperativa` de memoria, y la tabla devolvía el mismo número que había que teclear.

- [X] T014 Dejar **Tipo de unidad** como texto libre, con nota de por qué

      > ⚠️ Los datos traen `Grúa` y `Grua`. Un catálogo cerrado tendría que elegir una grafía y
      > escondería la otra. Registrado en `decisiones-pendientes.md`.

- [X] T015 [P] Prueba de que la consulta lleva el **id** y la celda pinta el **nombre**

## Fase 5: Pruebas de comportamiento

- [X] T016 [P] Prueba de que una unidad sin condado se muestra con el condado **ausente** y **no se
      omite** (FR-F09)
- [X] T017 [P] Prueba de que `caso_afectado` ausente **no** se pinta como `0`
- [X] T018 [P] Prueba de que el rango de fechas aparece **solo** en los dos de período (FR-F08)
- [X] T019 [P] Prueba de que ningún enum se pinta con su literal crudo (SC-F04)

## Fase 6: Cierre

- [X] T020 Suite completa del frontend verde
- [X] T021 **Verificar en navegador con el actor correspondiente** —DirectorExpansion para flota,
      DirectorTecnologico para validación—, **no con Administrador**
- [X] T022 Documentar en el changelog

---

## Riesgo principal

**T006 y T008.** T006 protege en el catálogo la exclusión de geometría y contacto, que es donde es
fácil romperla. T008 fija la única regla de acceso de este departamento que no se adivina: el
Proveedor tiene interés en las unidades y ninguno en el mapa operativo.

---

## Resultado *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `flota` con **DirectorExpansion** | ✅ listado completo, sin aviso de alcance |
| `regiones` / `validaciones-region` con **DirectorTecnologico** | ✅ |
| **Proveedor** en `regiones` | ✅ redirigido a `access-denied` |
| Combobox de Proveedor / Condado / Región | ✅ envía id, pinta nombre |
| Dos columnas «Estado» distinguibles | ✅ |
| Sin coordenadas ni contacto del proveedor | ✅ |

### Los dos casos que faltaban, sembrados *(2026-08-22)*

- [X] T023 Sembrar región fuera de `Producción` y unidad sin condado
      (`database/seed_casos_borde_informes.py`)

Dejaron de estar «solo en contrato». Medido contra la API con **DirectorTecnologico** y
**DirectorExpansion**:

| Caso | Resultado |
|---|---|
| `regiones` | ✅ 5 filas: 2 `Producción`, 1 `Despublicada`, 1 `En_Alerta`, 1 `Rechazada` |
| `detenida_mas_de_dias=100` | ✅ filtra a 2 de 5 (200 y 120 días) |
| `validaciones-region` de la región rechazada | ✅ **dos** intentos, cada uno con su motivo (FR-005) |
| Unidad sin condado en `flota` | ✅ `condado: null`, `estado_geografico: null`, **fila presente** |

La unidad se sembró **`activo = false`**: `list_candidatas_por_condado` filtra `activo = true`, así
que de baja no puede entrar al despacho **por garantía**. Activa, quedaría excluida solo porque su
`idcondado = 0` no cae en ningún condado — cierto hoy, y dependiente de un detalle de la consulta.

### Un dato que la pantalla no puede arreglar

`Grúa` y `Grua` conviven como tipos distintos, y hay **placas repetidas** en unidades distintas.
Ninguna de las dos cosas se corrige pintando: unificar en la tabla escondería un problema de datos
a la única persona que puede corregirlo. Ambas están en `decisiones-pendientes.md`.

### Recorrido en navegador con los datos sembrados *(2026-08-22)*

| Comprobación | Resultado |
|---|---|
| `flota` con **DirectorExpansion** | ✅ `TSI-099` con condado y estado geográfico en `—`, fila presente, «Dada de alta: No» |
| `regiones` | ✅ los cinco estados, humanizados («En Alerta», no `En_Alerta`) |
| Aviso de la pantalla | ✅ «"En Alerta" sigue operando con cobertura degradada; "Despublicada" no» |
| «Detenida más de» = 100 | ✅ acota de 5 filas a 2 |
| **DirectorExpansion** en `validaciones-region` | ✅ «Acceso denegado», con el rol en pantalla |
| `validaciones-region` con **DirectorTecnologico** | ✅ los **dos** intentos de Valle Sur, cada uno con su motivo |
| Combobox de Región | ✅ el `<option>` lleva `value="9103"` y muestra «Valle Sur» |
