# Tasks — Informes Tácticos Simples de Emergencias (Frontend)

**Input**: [`spec.md`](spec.md),
[`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

**Precedente**: Cuentas y Clientes (piloto) y Soporte al Cliente. Misma estructura, **sin volver a
decidirla**.

---

## Fase 0: Contrato

- [X] T001 Normalizar `hora_fin` a ISO **en el backend**, y documentar en el contrato que la columna
      de origen es `STRING` con epoch-ms escrito como texto.

      > ⚠️ **Esta tarea se escribió al revés y se corrigió al ejecutarla.** Primero se quitó el
      > `format: date-time` del contrato, creyendo que la columna guardaba una hora de reloj —lo
      > decía un fixture que yo mismo había inventado—. Los datos reales son epoch-ms, así que el
      > formato del contrato era **correcto** y lo que estaba mal era el backend, que la devolvía
      > verbatim. Se revirtió el contrato y se arregló el servicio.

## Fase 1: Catálogo

- [X] T002 Crear `definiciones/informes-emergencias.definiciones.ts` con los **cinco** listados,
      columnas y filtros del contrato
- [X] T003 Marcar `cierres` como **único sin rango de fechas** — es el único de estado actual, porque
      su tabla no tiene fecha propia (FR-F08)
- [X] T004 Declarar `hora_fin` **como fecha** —el backend la normaliza a ISO tras la corrección de
      T001— y **no** declarar ninguna columna «estado» en casos: los tres hechos van por separado
      (FR-F05)
- [X] T005 [P] Prueba de que columnas y enums coinciden con el contrato
- [X] T006 [P] ⛔ **Prueba de que ninguna definición declara coordenadas ni identidad** (FR-F04,
      SC-F03). Es una exclusión constitucional: el catálogo es el sitio donde alguien la rompería

## Fase 2: Acceso

- [X] T007 Crear los dos guards: `casos` admite internos **y** Cliente; los otros cuatro, **solo**
      internos (FR-F07)
- [X] T008 [P] ⚠️ Prueba de que un **Partner de integración no entra a ninguno** — su acceso a estos
      datos tiene su propio camino, con su alcance y su auditoría; dejarlo entrar aquí duplicaría ese
      control con otro que no lo audita
- [X] T009 [P] Prueba de que el Cliente entra a casos y **no** a los otros cuatro

## Fase 3: Pantallas

- [X] T010 Página parametrizada e índice, con el patrón ya establecido
- [X] T011 Registrar rutas y la entrada de navegación

## Fase 4: Pruebas de comportamiento

- [X] T012 [P] ⛔ **Prueba de que `zonas_contratadas` produce su aviso propio y NO dice que los datos
      sean del cliente** (FR-F03, SC-F02). Es el tercer valor de `acotado_a` y el único que ningún
      módulo de frontend ha ejercitado
- [X] T013 [P] ⛔ **Prueba de que el estado vacío acotado por zonas menciona que puede haberlos en
      otras zonas** — un «no hay accidentes» a secas es la ambigüedad que `acotado_a` evita
- [X] T014 [P] Prueba de que un caso fusionado muestra los **tres hechos por separado** y **no** una
      columna «estado» (FR-F05)
- [X] T015 [P] Prueba de que un despacho en tránsito muestra llegada y retiro **ausentes**, no como
      fecha de época (FR-F09)
- [X] T016 [P] Prueba de que una calificación ausente **no** se muestra como `0`, contrastada con un
      `0` real
- [X] T017 [P] Prueba de que la evidencia sin conexión muestra **dos horas distintas** y la de en
      línea, dos iguales
- [X] T018 [P] Prueba de que el rango de fechas **no** aparece en `cierres` y **sí** en los otros

## Fase 5: Cierre

- [X] T019 Suite completa del frontend verde
- [X] T020 **Verificar en navegador con dos roles**: un Operador (sin aviso) y un Cliente (con el
      aviso de zonas). Cierra el último valor de `acotado_a` sin validar
- [X] T021 Documentar en el changelog

---

## Riesgo principal

**T006 y T012 son los que justifican este departamento.** T006 protege una exclusión
constitucional en el sitio donde es fácil romperla —el catálogo de columnas—, y T012 valida el
último valor de `acotado_a` que quedaba sin ver contra el backend real.


---

## Resultado *(2026-08-15)*

**Los tres valores de `acotado_a` quedan validados de punta a punta.** Con este módulo se cierra el
último: `zonas_contratadas`.

| Comprobación | Resultado |
|---|---|
| Rol **Operador** → `todos` | ✅ 50 filas de varios condados, **sin aviso** |
| Rol **Cliente** → `zonas_contratadas` | ✅ 3 filas de **un solo condado**, con «Solo se muestra lo ocurrido en las zonas que tienes contratadas» |
| El aviso **no** dice que los datos sean del cliente | ✅ |
| Situación impuesta al cliente | ✅ `meta.filtros.situacion = cerrado` |
| **Sin coordenadas** en la respuesta ni en pantalla | ✅ |
| **Sin columna «Estado»** — los tres hechos por separado | ✅ |
| Guard: Cliente en los otros cuatro | ✅ redirigido a `access-denied` |

### Un defecto que solo se vio en el navegador

`hora_fin` salía en pantalla como **`1786625595899`**.

`Fact_Accidente.horafin` es una columna `STRING`, pero **guarda epoch-ms como texto**: lo escriben
`cerrar_caso_service` y `cancelar_caso_service` con el reloj del sistema. El backend la devolvía
**verbatim** mientras normalizaba a ISO todas las demás marcas de tiempo.

Ni las pruebas de backend ni las de frontend lo detectaron, **porque el fixture lo inventaba**: yo
había sembrado `"09:30"`, un formato que no existe en producción. La prueba pasaba comparando contra
un dato falso.

Corregido en los cuatro sitios: el servicio normaliza a ISO tolerando que el valor no sea numérico,
el fixture usa epoch-ms como los escritores reales, la prueba de backend afirma el formato en vez del
literal inventado, y el contrato explica que la columna de origen es `STRING`.

> **Lección.** Un fixture inventado no es una prueba: es una afirmación sobre datos que nadie produce.
> El recorrido en navegador es lo que lo destapó, igual que destapó `controlClass` en el piloto.
