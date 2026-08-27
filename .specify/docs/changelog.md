# Changelog fuera de ciclo — cambios de código no originados en `/plan`→`/tasks`

Este documento registra cambios de código aplicados directamente al detectar brechas
entre `spec.md` y el comportamiento real del sistema (vía `/speckit-analyze` extendido),
fuera del flujo normal Spec-Driven. Cada entrada debe quedar reflejada también en el
`traceability.md` de la feature afectada.

---

## 2026-08-27 — QA de sistema completo vía UI: regresión de botón sin icono y ordinales sin ordenar en gráficos

**Causa:** Barrido de todas las pantallas en navegador, por rol, verificando visibilidad cruzada de datos entre actores (tickets, evidencia, expedientes).

**Bugs encontrados y corregidos sin preguntar (según instrucción del usuario), documentados aquí:**

1. **Botón "Enviar respuesta" vacío en Cola de soporte** (`frontend/src/app/modules/soporte-cliente/pages/cola-agente/cola-agente.page.html`): el barrido previo de iconos decorativos (design-system v9, §botones) eliminó por error el icono de este botón `tsi-btn-icon`, que es icon-only (sin texto, solo `aria-label`). Quedó como botón vacío e inutilizable visualmente. Restaurado con `<app-tabler-icon name="chevron-right" [size]="16" />` (el primer intento usó `name="send"`, que no existe en `TablerIconName` — rompía la compilación de TODA la app con `NG2: Type '"send"' is not assignable to type 'TablerIconName'`, detectado al revisar los logs del dev server tras otro bug que parecía no solucionarse). Verificado extremo a extremo: agente responde ticket #3 → cliente ve el mensaje en su detalle de ticket.
2. **Orden ordinal en gráficos de barra** (ya corregido en sesión anterior, verificado de nuevo en este barrido): `ventas-crm`, `cuentas-clientes` y `estrategico/oe1` ordenan sus embudos por la etapa real antes de pintarlos — confirmado sin regresión.

**Verificación cruzada de actores (tickets):** Cliente (`ana.torres.cliente@demo.tsi.com`) crea ticket #9 → visible de inmediato para agente de soporte (`lucia.vera.soporte@demo.tsi.com`) en Cola de soporte. Agente responde ticket #3 → respuesta visible para el cliente en Mis tickets. Sin brechas de visibilidad detectadas.

**Confirmado como comportamiento correcto (no bug):** acceso denegado (403) a `DirectorTecnologico` en informe "Dinero de la API" (OE2) — la autoridad está repartida por informe (`AUTORIDAD_OE2_DINERO` vs `AUTORIDAD_OE2_CONSUMO` en `backend/apps/informes_estrategicos/permissions.py`); `DirectorFinanciero`/`DirectorExpansion` sí acceden, verificado.

**Archivos:**
- `frontend/src/app/modules/soporte-cliente/pages/cola-agente/cola-agente.page.html`

---

## 2026-08-27 — `DashboardSoporteView` en 403 para roles de nivel de escalado (QA continuada)

**Causa:** El menú (`frontend/src/app/shared/layout/nav-links.ts`) expone "Dashboard de soporte" a `Soporte`, `DesarrolladorAPIs` y `DirectorTecnologico`, pero el backend (`backend/apps/soporte_cliente/views.py`, `DashboardSoporteView`) solo permitía `IsSoporteAgente` (rol `Soporte`). Verificado en navegador con `director.tecnologico@demo.tsi.com`: clic en el enlace del menú → 403.

**Efecto:** cambiado a `IsSoporteAgenteOrNivelEscalado` (ya usada para resolver tickets escalados), consistente con `ROLES_ATENCION` de `backend/apps/soporte_cliente/permissions.py`. Verificado tras redeploy: `DirectorTecnologico` ve el dashboard con sus métricas (9 tickets, 1 SLA vencido, etc.).

**Archivos:**
- `backend/apps/soporte_cliente/views.py`

---

## 2026-08-27 — Índice de "Informes de Red Operativa" en 403 para `DirectorTecnologico` (QA continuada)

**Causa:** `frontend/src/app/modules/red-operativa/informes/red-operativa-informes.routes.ts` guardaba la ruta índice (`''`) con `informesFlotaGuard`, que solo admite `Administrador`, `DirectorExpansion`, `Cliente` y `Proveedor` (`AMPLIOS_FLOTA` + `ROLES_ACOTADOS` en `guards/informes-red-operativa.guard.ts`). `DirectorTecnologico` está en `AMPLIOS_REGION` y `AMPLIOS_VALIDACION` — puede abrir `/regiones` y `/validaciones-region` directo — pero no en `AMPLIOS_FLOTA`, así que el enlace del menú (`nav-links.ts`, que sí lo lista) llevaba al índice y éste lo rechazaba con "Acceso denegado".

**Efecto:** nuevo guard `informesIndiceGuard` (unión de los tres grupos) para la ruta índice; el índice sigue sin mostrar datos —solo enlaces— y cada informe interno conserva su propio guard estricto. Verificado: `DirectorTecnologico` ahora ve el índice con exactamente "Regiones operativas" y "Validaciones de región" (sin "Flota", correcto — no está en ese grupo).

**Archivos:**
- `frontend/src/app/modules/red-operativa/informes/guards/informes-red-operativa.guard.ts`
- `frontend/src/app/modules/red-operativa/informes/red-operativa-informes.routes.ts`

---

## 2026-08-27 — Placeholder copiado por error en filtros de fecha/checkbox de "Lista de accidentes"

**Causa:** `frontend/src/app/modules/accidentes/pages/lista-accidentes/lista-accidentes.page.html` tenía `placeholder="Buscar por ID o nombre"` copiado sobre los inputs `type="date"` (Desde/Hasta) y el checkbox "Solo activos" — sin efecto visual pero código muerto/confuso heredado de un copy-paste. Encontrado inspeccionando el árbol de accesibilidad (`read_page`) durante la prueba end-to-end como `Operador`.

**Efecto:** placeholders eliminados de los 3 inputs (no aplican a `date` ni a `checkbox`). Verificado: filtros siguen funcionando, sin errores de consola.

**Archivos:**
- `frontend/src/app/modules/accidentes/pages/lista-accidentes/lista-accidentes.page.html`

---

## 2026-08-27 — "Historial de emergencias" en 400 para TODO request tras la carga de 2M accidentes de US_Accidents

**Causa:** `HistorialEmergenciasView` (`GET /api/v1/emergencias/historial`) devolvía 400 "Parámetros de filtro inválidos" incluso sin ningún filtro aplicado — probado como `Operador`, pantalla completamente inutilizable. La vista atrapa cualquier `ValueError` bajo ese mensaje genérico, lo cual ocultaba la causa real. Reproducido en el shell del contenedor: `HistorialEmergenciasService().listar(limit=20)` lanzaba `ValueError: invalid literal for int() with base 10: '2023-03-31 23:25:30'` en `historial_emergencias_service.py:128`.

El campo `horainicio` se asume epoch-ms en todo el resto del código, pero el lote de 2 millones de accidentes cargado desde US_Accidents (commit `64e6a53`, "Limpieza total de la base y carga de 2M de accidentes") lo escribió como texto de fecha (`'YYYY-MM-DD HH:MM:SS'`), no como entero. Con esos ~2M registros dominando el dataset, la primera página del historial siempre tropieza con uno.

**Efecto:** nuevo método `HistorialEmergenciasService._epoch_ms()` que intenta `int()` primero (camino normal) y cae a `datetime.fromisoformat(...).timestamp() * 1000` para el formato de texto: mismo epoch-ms de salida sin importar cuál de las dos fuentes lo escribió. No se tocó el pipeline de carga (`dags/`) — el consumidor ahora tolera ambos formatos en vez de asumir que la ETL nunca cambiará de forma. Verificado: `HistorialEmergenciasService().listar(limit=20)` ya no lanza excepción, y la pantalla carga su tabla en el navegador.

⚠️ **Posible causa raíz más amplia sin confirmar todavía:** si `horainicio` llegó como texto desde el DAG de carga, es razonable sospechar que OTROS campos de fecha del mismo lote (p. ej. algún timestamp en `Fact_Despacho` derivado de las mismas filas) tengan el mismo problema de formato. No se auditó el resto de consumidores de este dataset en esta pasada — queda para una revisión posterior si aparecen más 400/500 al navegar reportes que toquen el lote de 2M accidentes.

**Archivos:**
- `backend/apps/seguimiento/services/historial_emergencias_service.py`

---

## 2026-08-27 — "Gestión de cuenta" mostraba "Sin rol" para TODOS los usuarios, incluido el propio Administrador

**Causa:** `UserManagementService.list_users()` (`backend/apps/cuentas_clientes/services/user_management_service.py`) devolvía las filas de `UserRepository.list_users()` sin adjuntarles `roles` — a diferencia de `get_user()` (detalle de un usuario), que sí llama a `role_repo.get_user_roles()`. El listado que alimenta la tabla de `GestionCuentaHubPage` (`GET /api/v1/usuarios`) nunca traía el campo, así que el template (`hub.page.html`) caía siempre en su rama `@empty` → "Sin rol" para cada fila, sin importar los roles reales del usuario. Encontrado navegando la pantalla como `Administrador` y viendo que ni su propia cuenta mostraba "Administrador".

**Efecto:** `list_users()` ahora enriquece cada usuario con `role_repo.get_user_roles(idusuario)`, igual que ya hacía `get_user()`. Verificado en shell y en navegador: la tabla ahora muestra los roles reales (`Cliente, Proveedor` / `Administrador, SupervisorSoporte` / etc.) para cada fila.

**Archivos:**
- `backend/apps/cuentas_clientes/services/user_management_service.py`

---

## 2026-08-27 — "Asignar rol" en Gestión de cuenta fallaba SIEMPRE con 404

**Causa:** `UserRoleAdminService.assignRole()` (`frontend/src/app/modules/cuentas-clientes/auth/services/user-role-admin.service.ts`) llamaba a `POST /api/v1/usuarios/{id}/roles`, pero el backend nunca registró esa ruta — solo existe `POST /api/v1/usuarios/roles/asignar` (`backend/apps/cuentas_clientes/views/urls.py:131`, `UserRoleAssignView`). Cualquier intento de asignar un rol desde el formulario de "Gestión de cuenta" devolvía 404 y el mensaje "No se pudo asignar el rol." — la única forma de administrar roles en todo el sistema estaba completamente inoperante. Encontrado al intentar asignar temporalmente el rol `Gerente` a una cuenta de prueba para poder verificar las pantallas de OE6.

**Efecto:** `assignRole()` corregido para apuntar a `POST /api/v1/usuarios/roles/asignar` con `{idusuario, idrol}` en el body, igual que espera `UserRoleAssignView`. Verificado: la asignación ahora devuelve 200 y la tabla de usuarios refleja el rol nuevo de inmediato.

**Archivos:**
- `frontend/src/app/modules/cuentas-clientes/auth/services/user-role-admin.service.ts`

---

## 2026-08-27 — Validación estricta y filtrado en tiempo real en Registro de Prospecto (`RegistroPublicoPage` y `RegistroProspectoService`)

**Causa:** Petición de usuario para asegurar que en el formulario público de registro de prospectos solo se permita el ingreso del tipo de dato correcto en cada campo (solo letras en nombres y apellidos, formato telefónico válido sin letras, correo sin espacios, cargos válidos).

**Efecto verificado:**
- En `RegistroPublicoPage` (`frontend/src/app/modules/ventas-crm/pages/registro-publico/registro-publico.page.ts` y `.html`):
  - `nombres` y `apellidos`: Restricción y filtrado en tiempo real para admitir solo letras, tildes y espacios (`onTextoInput`), con patrón estricto `Validators.pattern(TEXTO_LETRAS_RE)`.
  - `gmail`: Filtrado automático de espacios y conversión a minúsculas (`onEmailInput`), con patrón de correo formal.
  - `cargo`: Filtrado en tiempo real (`onCargoInput`) y validación de texto.
  - `telefono`: Filtrado en tiempo real para admitir solo prefijo `+` y dígitos numéricos (`onTelefonoInput`), con validador de longitud de 7 a 15 dígitos.
  - Mensajes de error contextualizados y específicos por tipo de error (patrón, obligatoriedad, longitud).
- En `RegistroProspectoService` (`backend/apps/ventas_crm/services/registro_prospecto_service.py`), se reforzaron las validaciones de caracteres válidos en el backend.

**Archivos:**
- `frontend/src/app/modules/ventas-crm/pages/registro-publico/registro-publico.page.ts`
- `frontend/src/app/modules/ventas-crm/pages/registro-publico/registro-publico.page.html`
- `backend/apps/ventas_crm/services/registro_prospecto_service.py`

---

## 2026-08-27 — Cálculo dinámico y consulta real de planes más usados/populares (`ConsultaPlanesPublicosService` y `CatalogoPlanesPage`)

**Causa:** Petición de usuario para asegurar que la insignia "POPULAR" en el catálogo de planes no se asigne de forma fija o aleatoria (ni a planes de prueba/demo como $0), sino que provenga de una consulta analítica real que determine los planes con mayor cantidad de suscripciones activas y vigentes en el período.

**Efecto verificado:**
- En `ConsultaPlanesPublicosService` (`backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`), se incorporó la consulta a `Fact_Suscripcion` en Pinot (`SELECT idplan, count(*) AS total FROM Fact_Suscripcion WHERE estado = 'Activa' GROUP BY idplan`) para calcular el plan comercial con mayor adopción y retornar `destacado: true` únicamente para el plan líder real con precio comercial.
- En `CatalogoPlanesPage` (`frontend/src/app/modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page.ts`), se actualizó `esPopular(plan)` para respetar el valor booleano `destacado` provisto por el backend y filtrar cualquier plan demo o sin tarifa ($0).

**Archivos:**
- `backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`
- `frontend/src/app/modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page.ts`

---

## 2026-08-27 — Combobox de Género, Selector amigable de Cliente, Nombres legibles en Planes SLA y Rediseño de Entrada Directa

**Causa:** Petición de usuario para:
1. Reemplazar el input de texto libre de Género en implicados de accidente por un combobox select con solo 2 opciones (`Masculino` o `Femenino`).
2. Eliminar el input numérico crudo de "ID cliente" en Gestión de cuenta (`hub.page`), permitiendo una selección y gestión clara de las acciones corporativas (Perfil, Preferencias, Transferencia y Baja de Cuenta).
3. Mostrar el nombre legible del plan (ej. *Básico*, *Estándar*, *Empresarial*, *Premium*) en la columna "Plan" de la tabla de políticas SLA en lugar del ID numérico crudo.
4. Rediseñar y estructurar en tarjetas de dos columnas la pantalla de Entrada Directa de clientes (`EntradaDirectaPage`).

**Efecto verificado:**
- En `EnriquecimientoAccidentePage` (`frontend/src/app/modules/evidencia-unidad/pages/enriquecimiento-accidente/enriquecimiento-accidente.page.html`), se sustituyó el `<input>` de género por un `<select>` con opciones *Masculino* y *Femenino*.
- En `GestionCuentaHubPage` (`frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/hub/`), se rediseñó el panel de cuenta corporativa con selector amigable y tarjetas de acción dedicadas para Perfil, Preferencias, Transferencia y Baja.
- En `ConfiguracionSlaPage` (`frontend/src/app/modules/soporte-cliente/pages/configuracion-sla/`), se integró `PlanApiService` con helper `nombrePlan(idplan)` para renderizar el nombre oficial del plan en la tabla y en el formulario.
- En `EntradaDirectaPage` (`frontend/src/app/modules/ventas-crm/pages/entrada-directa/`), se rediseñó la vista en tarjetas de 2 columnas ("1. Datos de la organización" y "2. Administrador local principal") con botones y validaciones mejoradas.

**Archivos:**
- `frontend/src/app/modules/evidencia-unidad/pages/enriquecimiento-accidente/enriquecimiento-accidente.page.html`
- `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/hub/hub.page.ts`
- `frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/hub/hub.page.html`
- `frontend/src/app/modules/soporte-cliente/pages/configuracion-sla/configuracion-sla.page.ts`
- `frontend/src/app/modules/soporte-cliente/pages/configuracion-sla/configuracion-sla.page.html`
- `frontend/src/app/modules/ventas-crm/pages/entrada-directa/entrada-directa.page.ts`

---

## 2026-08-27 — Mejoras de espaciado en Pipeline, rediseño de Parámetros del Algoritmo y Modal de Tickets de Soporte

**Causa:** Petición de usuario para:
1. Corregir el espaciado y márgenes laterales del tablero Pipeline (`PipelineBoardPage`), que se mostraba pegado a los bordes de la pantalla.
2. Rediseñar profesionalmente la interfaz de "Parámetros del algoritmo" (`ParametrosAlgoritmoPage`) para el Administrador según el sistema de diseño.
3. Mejorar la interfaz del cliente en "Mis tickets de soporte" (`MisTicketsPage`) añadiendo un botón destacado "Registrar ticket" que despliega un diálogo modal limpio en lugar del formulario expandido.

**Efecto verificado:**
- En `PipelineBoardPage` (`frontend/src/app/modules/ventas-crm/pages/pipeline-board/pipeline-board.page.ts`), se incorporó contenedor centrado con márgenes y padding responsive (`mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6`), tarjetas con sombras suaves, badges de recuento y separación armónica.
- En `ParametrosAlgoritmoPage` (`frontend/src/app/modules/despacho/pages/parametros-algoritmo/parametros-algoritmo.page.ts`), se estructuró un panel elevado con tipografía del sistema, input numérico estilizado con sufijo de unidad ("seg"), badge de rango (30 s a 300 s), feedback de estado y botón con estado de carga.
- En `MisTicketsPage` (`frontend/src/app/modules/soporte-cliente/pages/mis-tickets/mis-tickets.page.ts` y `.html`), se sustituyó el bloque `<details>` estático por un botón de acción en cabecera y un diálogo modal interactivo con backdrop desenfocado, manteniendo el listado de tickets limpio y despejado.

**Archivos:**
- `frontend/src/app/modules/ventas-crm/pages/pipeline-board/pipeline-board.page.ts`
- `frontend/src/app/modules/despacho/pages/parametros-algoritmo/parametros-algoritmo.page.ts`
- `frontend/src/app/modules/soporte-cliente/pages/mis-tickets/mis-tickets.page.ts`
- `frontend/src/app/modules/soporte-cliente/pages/mis-tickets/mis-tickets.page.html`

---

## 2026-08-27 — Modal de registro de método de pago exclusivo para tarjeta con validaciones estrictas (`MetodosPagoPage`)

**Causa:** Petición de usuario para unificar el registro de métodos de pago exclusivamente mediante Tarjeta (removiendo opciones heterogéneas como transferencia y paypal), activándolo a través de un botón de acción "Agregar método de pago" en la cabecera que despliega un diálogo modal centrado con validaciones especializadas para número de tarjeta (solo números con espaciado de 4 en 4), fecha de expiración (MM/AA) y código de seguridad CVV/CVC (3 o 4 dígitos numéricos).

**Efecto verificado:**
- En `MetodosPagoPage` (`frontend/src/app/modules/suscripciones/pages/metodos-pago/metodos-pago.page.ts` y `.html`), se sustituyó el formulario estático inferior por un botón "Agregar método de pago" y un diálogo modal interactivo con backdrop desenfocado.
- Se implementó sanitización y validación estricta de entradas numéricas en tiempo real para el PAN (13 a 19 dígitos), expiración MM/AA (mes 01 a 12) y CVV (3 a 4 dígitos).
- Se protegió la acción de guardado habilitando el botón únicamente si todos los campos requeridos son válidos.

**Archivos:**
- `frontend/src/app/modules/suscripciones/pages/metodos-pago/metodos-pago.page.ts`
- `frontend/src/app/modules/suscripciones/pages/metodos-pago/metodos-pago.page.html`

---

## 2026-08-27 — Botón de ojito, tablas comprimidas y diálogo modal en todos los Informes Tácticos Simples

**Causa:** Petición de usuario para comprimir las tablas de los informes simples de todos los módulos del sistema (Emergencias, Cuentas y Clientes, Partners, Red Operativa, Soporte y Suscripciones/Facturación, Ventas/CRM) mostrando solo las columnas prioritarias y desplegando en un diálogo modal con botón de ojito (`eye`) la totalidad de los datos estructurados del registro seleccionado.

**Efecto verificado:**
- En `ColumnaListado` (`informes-listado.types.ts`), se introdujo el atributo `soloDetalle?: boolean` para aislar campos secundarios del renderizado de la tabla y reservarlos para el modal.
- En `InformesListadoComponent` (`informes-listado.component.ts`), la tabla y tarjetas móviles computan `columnasTabla` excluyendo `soloDetalle`, e incorporan la columna de acción con botón de ojo interactivo (`eye`). Al hacer clic, se abre un diálogo modal centrado con backdrop desenfocado mostrando todos los campos (`columnas`) con formato legible.
- En las definiciones de informes tácticos de todos los módulos (`informes-emergencias.definiciones.ts`, `informes-cuentas.definiciones.ts`, `informes-partners.definiciones.ts`, `informes-red-operativa.definiciones.ts`, `informes-soporte.definiciones.ts`, `informes-suscripciones.definiciones.ts`, `informes-ventas.definiciones.ts`), se marcaron con `soloDetalle: true` las columnas secundarias o extensas para asegurar tablas limpias y compactas en toda la plataforma.

**Archivos:**
- `frontend/src/app/shared/informes/informes-listado.types.ts`
- `frontend/src/app/shared/informes/informes-listado.component.ts`
- `frontend/src/app/modules/emergencias/informes/definiciones/informes-emergencias.definiciones.ts`
- `frontend/src/app/modules/cuentas-clientes/informes/definiciones/informes-cuentas.definiciones.ts`
- `frontend/src/app/modules/partners/informes/definiciones/informes-partners.definiciones.ts`
- `frontend/src/app/modules/red-operativa/informes/definiciones/informes-red-operativa.definiciones.ts`
- `frontend/src/app/modules/soporte-cliente/informes/definiciones/informes-soporte.definiciones.ts`
- `frontend/src/app/modules/suscripciones/informes/definiciones/informes-suscripciones.definiciones.ts`
- `frontend/src/app/modules/ventas-crm/informes/definiciones/informes-ventas.definiciones.ts`

---

## 2026-08-27 — Ajuste de opciones de navegación del Administrador en el Sidebar (`nav-links.ts`)

**Causa:** Petición de usuario para retirar del menú lateral del Administrador los accesos a Prospectos, Pipeline, Informes comerciales, Regiones operativas, Validación de región e Informes de red, conservando Entrada directa y Parámetros del algoritmo.

**Efecto verificado:**
- En `frontend/src/app/shared/layout/nav-links.ts`, se eliminó el rol `Administrador` de `Prospectos`, `Pipeline`, `Informes comerciales`, `Regiones operativas`, `Validación de región` e `Informes de red`.
- Se mantuvieron `Entrada directa` y `Parámetros del algoritmo` para el rol `Administrador`.

**Archivos:** `frontend/src/app/shared/layout/nav-links.ts`.

---

## 2026-08-27 — Selector legible de regiones en `ValidacionPage` y eliminación de códigos técnicos (CU/RF/RN) en la UI

**Causa:** Petición de usuario para mostrar únicamente los nombres legibles de las regiones operativas en la validación (reemplazando la caja numérica de `idregionoperativa`) y eliminar todos los códigos técnicos de casos de uso o requerimientos (ej. `CU-O55`, `CU-O61`, `CU-O26`, `CU-O97`, `CU-O40`, `CU-O30`, `RF-TIC-007`, `RNF-REG-006`) visibles en la interfaz.

**Efecto verificado:**
- En `ValidacionPage`, se reemplazó el campo numérico por un `<select>` que lista las regiones operativas por nombre (`nombreregion`), permitiendo también el alta de nueva región con un selector de estados geográficos.
- Se retiraron prefijos y referencias como `CU-O55`, `CU-O61`, `CU-O26`, `CU-O97`, `CU-O40`, `CU-O30`, `RF-TIC-007`, `RNF-REG-006` en subtítulos, textos de ayuda y descripciones en todas las vistas afectadas.

**Archivos:** `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/validacion/validacion.page.ts`, `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/reevaluacion/reevaluacion.page.ts`, `frontend/src/app/modules/partners/pages/excepciones-facturacion/excepciones-facturacion.page.ts`, `frontend/src/app/modules/soporte-cliente/pages/configuracion-sla/configuracion-sla.page.html`, `frontend/src/app/modules/soporte-cliente/pages/dashboard-soporte/dashboard-soporte.page.html`, `frontend/src/app/modules/suscripciones/pages/plan-form/plan-form.page.html`, `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.html`, `frontend/src/app/modules/cuentas-clientes/home/home.page.html`.

---

## 2026-08-27 — Formato legible de etiquetas de estado de accidente y despacho (`ESTADO_INFO`, `ESTADO_DESPACHO_LABEL`)

**Causa:** Petición de usuario para mostrar los estados del caso en formato legible ("En atención", "Buscando unidad", "Asignado", "En sitio", etc.) en lugar de enums técnicos en mayúsculas/snake_case (`EN_ATENCIÓN`, `BUSCANDO_UNIDAD`, `En_sitio`).

**Efecto verificado:**
- Se actualizaron las etiquetas en `ESTADO_INFO` (`frontend/src/app/modules/accidentes/estado.constants.ts`) a Title Case legible en español (`Borrador`, `Reportado`, `Buscando unidad`, `Asignado`, `En atención`, `Cerrado`, `Descartado`, `Fusionado`).
- Se formateó la visualización del historial de estados en `DetalleAccidentePage` y los selectores de filtro en `ListaAccidentesPage`.
- Se añadió `estadoDespachoLabel` en `despacho-tono.constants.ts` para transformar `En_sitio` -> `En sitio`, `Timeout` -> `Tiempo agotado`, etc., aplicándolo en `DetalleAccidentePage` y `MonitoreoDespachoPage`.

**Archivos:** `frontend/src/app/modules/accidentes/estado.constants.ts`, `frontend/src/app/modules/despacho/despacho-tono.constants.ts`, `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.html`, `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.ts`, `frontend/src/app/modules/accidentes/pages/lista-accidentes/lista-accidentes.page.html`, `frontend/src/app/modules/despacho/pages/monitoreo-despacho/monitoreo-despacho.page.ts`, `frontend/src/app/modules/despacho/pages/monitoreo-despacho/monitoreo-despacho.page.html`.

---

## 2026-08-27 — Modal de escalar severidad y simplificación de aviso de llegada en `MiSeguimientoPage`

**Causa:** Petición de usuario para mostrar el formulario de escalar severidad dentro de un cuadro de diálogo modal únicamente al presionar el botón "Escalar severidad", y remover el enlace redundante a "Evidencia del caso" dentro del aviso verde de llegada.

**Efecto verificado:**
- En `MiSeguimientoPage`, se transformó el panel embebido de `EscalarSeveridadPanel` en un modal dialog con backdrop accesible (`modalEscalarAbierto`, botón de cierre y botón de cancelación).
- Se agregó el botón "Escalar severidad" en la barra de acciones de la vista en sitio.
- Se simplificó el texto del banner verde a `Ya registraste tu llegada al sitio del accidente.`, evitando la duplicación con el botón superior de "Evidencia del caso".

**Archivos:** `frontend/src/app/modules/seguimiento/pages/mi-seguimiento/mi-seguimiento.page.html`, `frontend/src/app/modules/seguimiento/pages/mi-seguimiento/mi-seguimiento.page.ts`, `frontend/src/app/modules/accidentes/pages/detalle-accidente/escalar-severidad.panel.ts`.

---

## 2026-08-27 — Eliminación de buscador global, selector de región y campana en `AppShellComponent`

**Causa:** Petición de usuario para limpiar la cabecera superior y retirar controles decorativos/no implementados (caja de búsqueda global "Buscar accidentes, expedientes, unidades...", botón de ubicación/región con ícono `map-pin` y botón de notificaciones con ícono `bell`).

**Efecto verificado:**
- Se eliminó el bloque del buscador (tanto para escritorio como el colapsable móvil).
- Se eliminó el botón de región (`map-pin`).
- Se eliminó el botón y desplegable de notificaciones (`bell`).
- La cabecera conserva el menú hamburguesa, el logotipo con nombre del producto, el avatar con iniciales/correo/roles y el botón de cierre de sesión.

**Archivos:** `frontend/src/app/shared/layout/app-shell.component.ts`.

---

## 2026-08-27 — Paginación estándar en `ListaMonitoreoPage` y limpieza de texto en `RegistroAccidentePage`

**Causa:** Reemplazo del aviso de advertencia de truncado (`Mostrando los 100 accidentes activos más recientes...`) en `ListaMonitoreoPage` por la barra de paginación estándar del sistema (con botones Anterior / Siguiente y control por cursor/páginas), y remoción del texto de ayuda bajo el input de Víctimas (total) en `RegistroAccidentePage`.

**Efecto verificado:**
- En `ListaMonitoreoPage`, se eliminó el banner de advertencia y se implementó paginación con `pageLimit = 20` mediante cursores (`nextCursor`, `cursorStack`, botones Anterior/Siguiente).
- En `RegistroAccidentePage`, se eliminó el texto inferior explicativo del campo Víctimas (total), manteniendo el campo como de solo lectura con cálculo reactivo.

**Archivos:** `frontend/src/app/modules/despacho/pages/lista-monitoreo/lista-monitoreo.page.ts`, `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.html`.

---

## 2026-08-27 — Nombre legible de calle y cálculo automático de víctimas totales en `RegistroAccidentePage`

**Causa:** Mejora de UX en el formulario de registro de accidentes para evitar mostrar IDs numéricos en crudo (`idcalle: 1`) al operador y automatizar la suma de `numvictimas = numheridos + numfallecidos`.

**Efecto verificado:**
- La calle sugerida por geocodificación inversa y la calle seleccionada (vía mapa o cascada manual) muestran ahora su nombre legible y ciudad (`calle, ciudad` o `nombre`), manteniendo el `idcalle` internamente para el envío del payload.
- El campo `Víctimas (total)` se convirtió en un campo de solo lectura calculado reactivamente a partir de los valores de `Heridos` y `Fallecidos`.

**Archivos:** `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`, `frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.html`.

---

## 2026-08-27 — design-system v9 (cierre): gráficos en los nueve departamentos y el botón como placa

**Efecto verificado:**
- **Barrido completo de gráficos.** Ya no queda **ninguna** barra inline hecha a
  mano en el frontend: 13 pantallas-Z (Cuentas, Emergencias, Partners, Red Operativa,
  Suscripciones, Ventas y CRM, Soporte, OE1, OE2) más el dashboard de Soporte. Se
  retiraron de paso 9 helpers muertos (`maxDe`, `maxBarra`, `anchoRelativo`,
  `maxUnidadesEstado`, `maxRechazos`) y un `@let` sin uso.
- **`MeterComponent` nuevo** para consumo contra límite, y **escala divergente** y
  **tono semántico** añadidos a `BarChartComponent`.
- **`.tsi-btn` pasa a placa de señalización**: ambas esquinas superiores en ángulo,
  display en mayúsculas con tracking, canto inferior reflectante de 3px, y botón
  solo-ícono hexagonal.

**Dos defectos de datos que la lista escondía y el gráfico destapó:**
1. **El signo del delta se borraba.** `anchoRelativo()` en Suscripciones aplicaba
   `Math.abs()`, así que un downgrade de −200 y un upgrade de +200 dibujaban la misma
   barra: la única información que distingue un movimiento del contrario se perdía
   justo en el gráfico que existe para compararlos. Ahora es divergente desde el
   centro — verificado en pantalla con datos reales (+400 a la derecha en azul, −200 a
   la izquierda en carmesí y de la mitad de largo).
2. **El exceso de cupo era invisible.** «Utilización de límites» era texto plano:
   «19 de 5 unidades» se leía igual que «1 de 25». Con medidor sale al 380% en rojo con
   «Excedido en 14 unidades».

**Un conflicto con el sistema importado, resuelto en vez de obedecido.** Su
`components.css` pone `clip-path` en `.tsi-btn`, pero el CSS de TSI documentaba por qué
lo había evitado: **un recorte se come el anillo de foco del teclado**, porque `outline`
se pinta fuera de la caja. El sistema importado es una vista estática y nunca se
enfrentó a eso. Se adopta la forma de placa y se resuelve el foco con un anillo
`inset` —`box-shadow: inset` se pinta dentro y sobrevive al recorte—, comprobado
tabulando de verdad en el navegador. Ni se ignoró el diseño ni se perdió la
accesibilidad.

**Regla de botón aplicada:** los botones de texto no llevan ícono. Se retiraron los 34
repartidos por 17 pantallas; es el mismo criterio que la regla anti-íconos-de-IA de §5.
Tres imports de `TablerIconComponent` quedaron sin uso por ello y se limpiaron.

**Archivos:** `frontend/src/styles.css`,
`frontend/src/app/shared/ui/charts/{bar-chart,line-chart,meter}.component.ts`,
las 13 `*/pages/pantalla-z.page.{ts,html}`, `dashboard-soporte/*`, y 17 plantillas con
botones. `.specify/docs/design/design-system.md`.

---

## 2026-08-27 — design-system v9 (cont.): gráficos de datos y correo transaccional maquetado

**Causa.** Varias pantallas de gestión mostraban como lista cosas que eran repartos o
evoluciones. El caso más claro: en Tendencias, «carga entrante **frente a** resuelta»
dibujaba una barra solo para `creados` y dejaba `resueltos` como texto al lado — es
decir, la comparación que el título promete era la única que no se podía hacer de un
vistazo. En Cola en curso la evolución temporal era texto puro, sin ninguna
representación.

**Efecto verificado:**
- Dos componentes nuevos en `shared/ui/charts/`: `BarChartComponent` (barras
  horizontales, escalas nominal y ordinal) y `LineChartComponent` (serie temporal en
  SVG, responsivo por `ResizeObserver`, leyenda, crosshair con tooltip).
- Paleta de gráficos propia (`--chart-cat-1..4`, `--chart-seq-1..5`, `--chart-grid`),
  separada de la de UI y la de marca porque codifica identidad y no jerarquía.
  **Verificada con el validador de la skill `dataviz`**, no elegida a ojo: separación
  con daltonismo ΔE 10.2 (objetivo ≥ 8), piso de visión normal 19.8 (piso 15),
  contraste ≥ 3:1 los cuatro; la rampa ordinal pasa monotonía, salto adyacente y
  extremo claro 2.14:1.
- Aplicado en las 4 pantallas de Soporte: dashboard (4 distribuciones), cumplimiento
  por plan, evolución del incumplimiento y carga entrante frente a resuelta.
- Correo transaccional maquetado: `backend/templates/emails/alerta_critica_despacho.html`
  (tablas + inline, bulletproof), `EmailNotificationSender` gana `html_body` opcional
  → `multipart/alternative`, y `AlertaAdminService` lo renderiza con *fail-open* (si la
  plantilla falla, la alerta sale igual en texto plano). Nuevo `CONSOLA_BASE_URL`.

**Tres defectos reales encontrados al verificar en navegador, no al escribir:**
1. `new DecimalPipe('es-EC')` lanzaba `NG0701` (locale no registrado) y se comía **en
   silencio** el valor y el ancho de todas las barras. Se pasa a `inject(LOCALE_ID)`,
   que es la pauta que ya seguía `informes-listado.component.ts`.
2. Los `{# … #}` multilínea de la plantilla de correo **no son comentarios** en Django
   (solo valen de una línea), así que el bloque entero de documentación se estaba
   renderizando dentro del correo. Lo cazó el test nuevo, no la vista. Pasan a
   `{% comment %}`.
3. El eje Y rotulaba «2» sobre una rejilla situada en 1,5 (tope impar, cortes en ½).
   El tope se redondea ahora a par. Además, rótulos del eje X medidos contra el ancho
   real y anclados al borde en los extremos, en vez de un número fijo de etiquetas.

**Pendiente declarado:** 9 pantallas-Z conservan barras inline hechas a mano; ver
«Pendiente de v9» en `design-system.md` §5.

**Archivos:** `frontend/src/styles.css`,
`frontend/src/app/shared/ui/charts/{bar-chart,line-chart}.component.ts` (nuevos),
`frontend/src/app/modules/soporte-cliente/gestion/pages/pantalla-z.page.{ts,html}`,
`frontend/src/app/modules/soporte-cliente/pages/dashboard-soporte/*`,
`backend/templates/emails/alerta_critica_despacho.html` (nuevo),
`backend/core/notificaciones/email_sender.py`,
`backend/apps/despacho/services/alerta_admin_service.py`,
`backend/apps/despacho/tests/services/test_reasignacion_alerta_admin.py`,
`backend/config/settings.py`, `.specify/docs/design/design-system.md`.

---

## 2026-08-27 — design-system v9: modo claro único, paleta de ruta y tres componentes nuevos (`CaseCard`, `RouteTracker`, `ReportTile`)

**Origen.** Importación del proyecto de Claude Design "TSI — Nodo Integral Design System"
(reinterpretación del sistema existente, no un espejo 1:1 — su propio `readme.md` lo dice
explícitamente). Se adoptaron las piezas que suman sin contradecir decisiones ya
verificadas del sistema, y se dejó fuera lo que el propio import marcaba como
reinterpretación libre (motivo de carretera literal en el sidebar, placas de doble corte
en superficies de datos densos, retirar buscador/campana del header).

**Modo oscuro retirado (revierte v6/v7).** El import proponía light-only por decisión de
su autor; tras confirmarlo con el propietario del sistema, se retira `ThemeService`
completo, el toggle del header, los tiles oscuros de Leaflet (CartoDB Dark Matter) y el
script inline de `index.html` que fijaba `data-theme` antes del primer paint. Motivo
documentado en §3 de `design-system.md`: un segundo tema necesita mantenimiento propio y
nadie lo estaba revisando en cada cambio del sistema.

**Piezas nuevas:**
- Paleta "de ruta" (`--route-navy`/`--route-cyan`/`--route-teal`) — capa expresiva sobre
  la paleta operativa ya existente; acento tricolor del header, perforación de `CaseCard`.
- `.tsi-panel--placa` — variante de doble esquina cortada.
- `.tsi-btn-danger` — acción destructiva declarada, promovida de clase ad-hoc a canónica.
- `CaseCardComponent`, `RouteTrackerComponent`, `ReportTileComponent` (`shared/ui/`) —
  reemplazan fila de tabla genérica, timeline de puntos e ícono-de-lista repetido,
  respectivamente, por la gramática de forma ya definida en §3.1.
- Regla explícita: sin íconos genéricos de "IA" (cerebro, sparkles, robot) como decoración.

**Aplicado en esta pasada:** listado de Accidentes activos (`CaseCard`), Historial de
intentos de Monitoreo de despacho (`RouteTracker`), los siete índices de informes
departamentales (`ReportTile`). El resto de listas/historiales del sistema hereda los
tokens globales (sin tema oscuro, botones, paneles) automáticamente por ser CSS
compartido, pero no se migró pieza por pieza a los tres componentes nuevos — ver
"Pendiente de v9" en `design-system.md` §5.

**Archivos:** `frontend/src/styles.css`, `frontend/src/index.html`,
`frontend/src/app/shared/theme/theme.service.ts` (eliminado, con su spec),
`frontend/src/app/shared/layout/app-shell.component.ts`,
`frontend/src/app/shared/ui/map/{map-tile,location-picker-map.component,read-only-route-map.component}.ts`,
`frontend/src/app/shared/ui/icon/tabler-icon.component.ts`,
`frontend/src/app/modules/ventas-crm/pages/catalogo-planes/*`,
`frontend/src/app/modules/seguimiento/pages/mapa-seguimiento/mapa-seguimiento.page.ts`,
`frontend/src/app/shared/ui/{case-card,route-tracker,report-tile}/*` (nuevos),
`frontend/src/app/modules/accidentes/pages/lista-accidentes/*`,
`frontend/src/app/modules/despacho/pages/monitoreo-despacho/*`,
los siete `*/informes/pages/indice/indice-informes.page.ts`,
`.specify/docs/design/design-system.md`.

---

## 2026-08-27 — [B27] Generación y sincronización de credenciales activas para actores tácticos y estratégicos

**Causa:** El script `database/siembra_roles_tacticos.py` asociaba roles a usuarios existentes en `Dim_Usuarios` pero omitía generar sus registros correspondientes en `Dim_Credencial`. Al intentar autenticarse en el login (`/api/v1/auth/login`), el servicio `AuthService` devolvía error `401 Unauthorized` al no encontrar credenciales activas registradas para dichos usuarios.

**Efecto verificado:**
- Se actualizó `database/siembra_roles_tacticos.py` para asegurar que todo actor táctico y el rol transversal `Gerente` tengan su credencial activa generada y sincronizada en `Dim_Credencial`.
- Se configuró la clave demo estándar (`password123`).
- Se integró el paso de siembra en `database/regenera_todo.py`.
- Verificado exitosamente con respuesta `200 OK` y emisión de tokens JWT para los usuarios tácticos y estratégicos (`director.operaciones@demo.tsi.com`, `gerente@demo.tsi.com`, etc.).

**Archivos:** `database/siembra_roles_tacticos.py`, `database/regenera_todo.py`.

---

## 2026-08-26 — Modal de confirmación para cancelación de suscripción en `MiSuscripcionPage`

**Causa:** Requerimiento de UX para simplificar la vista principal de la suscripción, transformando el formulario estático de cancelación en un botón de acción destructiva que abre un diálogo modal accesible con confirmación y captura de motivo.

**Efecto verificado:**
- Se integró el botón "Cancelar suscripción" (`tsi-btn border-alert-critical`) en la barra de acciones de la suscripción.
- Se implementó el modal accesible (`role="dialog"`, `aria-modal="true"`, cierre con `Escape` y backdrop) alineado a la paleta y clases canónicas (`.tsi-panel--elevado`, `.tsi-textarea`, `.tsi-btn-ghost`, botón crítico).
- Se cierra y recarga la vista al completar la cancelación.

**Archivos:** `frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.ts`, `frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.html`.

---

## 2026-08-26 — Corrección de solapamiento visual en `.tsi-panel--elevado` (texto y controles tapados)

**Causa:** El pseudo-elemento `::after` de `.tsi-panel--elevado` (usado para pintar el fondo recortado `--bg-surface` bajo `drop-shadow`) se posicionaba en el mismo nivel de apilamiento pero posterior en el árbol que los hijos directos del panel, tapando todo el contenido interno (títulos, valores, badges, botones y formularios) con una caja blanca sólida que parecía un estado de carga indefinido.

**Efecto verificado:**
- Se configuró `.tsi-panel > *` con `position: relative; z-index: 1;` para garantizar que todo el contenido renderice por encima de `::before` y `::after`.
- Se añadió `pointer-events: none;` a los pseudo-elementos decorativos de borde y superficie de `.tsi-panel` y `.tsi-panel--elevado`.
- Las tarjetas de *Mi suscripción* y demás pantallas que usan `.tsi-panel--elevado` vuelven a mostrar sus datos, badges y acciones interactivas con total claridad.

**Archivos:** `frontend/src/styles.css`.

---

## 2026-08-26 — Eliminación de barra de pestañas (sub-nav) en Suscripciones y Facturación

**Causa:** Petición de unificación de la experiencia de navegación del usuario para eliminar la barra superior de sub-navegación por pestañas ("Mi suscripción", "Métodos de pago", "Facturas", "Cambio de plan", "Catálogo") en `BillingShellPage`, consolidando toda la navegación de estas secciones exclusivamente en el menú lateral (sidebar).

**Efecto verificado:**
- Se eliminó el bloque `<nav>` de pestañas en `billing-shell.page.html`.
- Se limpió el componente `BillingShellPage` en `billing-shell.page.ts` de la lógica de tabs y enlaces duplicados.
- Se aseguró que todas las secciones del módulo (incluyendo "Cambio de plan") cuenten con su enlace correspondiente en `NAV_LINKS` (`nav-links.ts`) para los roles autorizados.

**Archivos:** `frontend/src/app/modules/suscripciones/pages/billing-shell/billing-shell.page.html`, `frontend/src/app/modules/suscripciones/pages/billing-shell/billing-shell.page.ts`, `frontend/src/app/shared/layout/nav-links.ts`.

---

## 2026-08-25 — design-system v8: §1 invierte la filosofía y §4 estrena pareja tipográfica

**Se redacta al final a propósito.** Estas dos secciones se reescriben *después* de
construir la identidad, a partir de lo que se decidió en pantalla. Es lo contrario del
flujo normal del proyecto, y fue una decisión explícita: la dirección visual no se podía
cerrar en abstracto, había que verla.

**§1 — la forma pasa a ser protagonista.** Hasta la v7 el documento pedía sobriedad: la
redondez debía ser "un detalle de coherencia, no una decisión estética protagonista". Esa
regla, aplicada al pie de la letra, produjo un sistema **coherente pero anónimo** — con la
paleta del logo y sin que nada recordara al logo. Era la propia filosofía la que frenaba
el cambio, no un olvido de implementación.

La sección nueva declara el objetivo real —que alguien reconozca TSI sin ver el logo ni
leer el nombre— y lista las cuatro traducciones del isotipo con su sitio: el riel, el
nodo, la esquina cortada y la superficie de convergencia. Conserva **dos límites**, que son
los que separan identidad de ruido: las primitivas van solo donde ya hay estructura, y la
severidad nunca la pisa la marca. Y deja explícito dónde la sobriedad sigue mandando —
celdas, labels y formularios, donde manda la legibilidad bajo estrés.

**§4 — Archivo Expanded / Inter.** Dos familias con papeles separados: la display da
carácter, la de texto da legibilidad. Se documenta por qué Expanded y no Archivo a secas —
la versión normal se probó primero y no se distinguía de Inter, porque ambas son grotescas
neo; lo que se percibe sin ojo entrenado es el ancho (495px contra 392 en el mismo
titular). Se fija la regla de reparto en una línea: si se lee de un vistazo es display, si
se lee con atención es Inter. Y se documentan los placeholders como ejemplos concretos, no
instrucciones.

**Huecos cerrados de paso:** §3.1 no listaba la esquina cortada ni las vías del sidebar
(se construyeron después de escribirla); §5 no documentaba `.tsi-panel` ni sus tres
variantes ni la esquina del botón; y la sección de iconografía seguía citando una escala de
radios de "6-12px" que dejó de existir en v7.2.

**Archivos:** `.specify/docs/design/design-system.md` §1, §3.1, §4, §5.

---

## 2026-08-24 — El cian y el hexágono dejan de ser papel (design-system v7.4)

**Causa:** auditando lo desplegado apareció lo incómodo — `--accent-flow` tenía **cero
consumidores** en toda la UI. Existía como token y con trabajo asignado en §3.1, pero
ningún componente lo usaba; el SVG del panel de marca usa el hex crudo. Es exactamente la
crítica que se le hizo a la propuesta de paleta original ("el cian quedó como referencia de
matiz y ahí murió") repetida en el propio sistema. El nodo hexagonal solo aparecía en
estados vacíos, y los pines de mapa —descritos en §3.1 como "la decisión con más retorno"—
seguían siendo la gota genérica.

**Efecto verificado:**

- Nuevo `shared/ui/map/map-pins.ts` con la implementación única de los pines. Estaban
  duplicados casi letra por letra entre `read-only-route-map.component.ts` y
  `mapa-seguimiento.page.ts`, más una tercera variante en `location-picker-map.component.ts`.
- **El pin pasa a ser el nodo hexagonal de §3.1.** La punta inferior sigue siendo el punto
  de anclaje, así que no se pierde precisión respecto a la gota. El color y el ícono de
  dentro siguen siendo los tokens semánticos de severidad: la forma es de marca, el color es
  información.
- **El marcador de unidad se mantiene circular a propósito.** El hexágono es el nodo (un
  punto fijo) y la unidad es lo que se mueve hacia él por las vías; darles la misma forma
  borraría esa lectura.
- **La ruta hacia un caso activo se dibuja como el riel**: vía gruesa en `accent-flow` con
  la divisoria interior encima. Es la construcción del isotipo sobre un mapa real, y le da
  al cian su primer trabajo de verdad: flujo en curso, nunca severidad.

**Detalle de implementación que no era obvio:** el riel son dos polilíneas superpuestas, y
el mapa de seguimiento reajusta el extremo de la ruta en vivo con `setLatLngs()` sin
recalcularla. Guardarlas como `L.LayerGroup` habría perdido ese método, así que la caché de
ruta guarda las dos polilíneas por separado y mueve ambas a la vez.

**Contradicción propia corregida:** §3.1 reclamaba el "punto de estado en vivo" para el
cian, pero §5 define ese dot como verde/ámbar/gris según el estado de conexión. Ese punto es
semántico, no de marca. §5 tiene razón y §3.1 deja de reclamarlo.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

**Verificado en navegador** (`sofia.castro.operador`, rol Operador, en
`/accidentes/registro`): el mapa renderiza el pin con el path del hexágono
(`M12 0 L24 8 L24 24 L12 32 L0 24 L0 8 Z`) y cero gotas antiguas.

**Pendiente y consciente:** los ring charts que §5 describe y a los que §3.1 asigna el arco
"en proceso" **no existen en el código**. Es una brecha spec-vs-realidad que hay que decidir:
construirlos o quitarlos del documento.

---

## 2026-08-24 — El panel de marca no se estiraba: el host del componente iba sin estilo

**Regresión propia, introducida al extraer `app-brand-panel`.** En login y registro el panel
no llenaba el alto de la columna: la marca, el titular y el indicador de estado quedaban
apelotonados arriba y el patrón salía desproporcionado y recortado.

**Causa:** el elemento que entra en la rejilla de la pantalla es el host
`<app-brand-panel>`, no el `<section>` que yo había dejado dentro del template. El host
quedaba sin estilos, así que la sección interna tenía altura automática — no se estiraba a
la fila — y `justify-between` no tenía espacio que repartir. Los estilos pasan al host vía
`host: { class: … }` y desaparece el envoltorio.

**Segundo defecto, visible solo una vez arreglado el alto:** las tres vías terminaban en el
aire dentro del panel en vez de salirse por los bordes. Con `preserveAspectRatio` por
defecto (meet) el viewBox no cubre todo el ancho del panel — en login, 720 de 1040px — así
que un tramo que acabe en el borde del viewBox queda *dentro* del panel y se ve el remate
redondeado del trazo colgando. Los tramos de entrada ahora arrancan muy por fuera del
viewBox; el SVG recorta a su viewport, no al viewBox, así que el sobrante simplemente se
sale. (El `preserveAspectRatio="slice"` que llevaba antes tapaba esto, pero a cambio
ampliaba el motivo 3x y lo recortaba.)

**Verificado en navegador** a 1600x900: login con panel de 1040x900 llenando la fila,
columnas 65/35 exactas, y los tres tramos arrancando en x=-740, x=1780 e y=-720 — los tres
fuera del panel, cero remates colgando. Registro igual, con el panel a 963px de alto
siguiendo al formulario. En tablet el panel cae a `display: none` y el formulario ocupa el
ancho completo, como manda `hidden lg:flex`.

**Suites:** `ng test` completo, 1425 passed.

---

## 2026-08-24 — Departamentos 6 y 7: el resto del sistema, y cierre de la deuda de radios

**Efecto verificado:** 204 elementos migrados a las clases canónicas de §5 (82 en
Cuentas-clientes + Accidentes, 122 en Partners, Red Operativa, Estratégico, Emergencias y
Ventas-CRM interno) y el resto de cards a `--radius-md`.

**Cierre de la escala de radios.** Se barrieron también los 10 `rounded-lg` que quedaban
fuera de `modules/` (`detalle-prospecto`, los dos hosts de diálogo, los componentes de
informes y el mapa de solo lectura) y los 16 `rounded-[10px]` — valores arbitrarios que
coincidían con `--radius-md` pero se saltaban el token, que es justo lo que §5 prohíbe.

**Estado final de la deuda que abrió este trabajo:**

| Métrica | Al empezar | Ahora |
|---|---|---|
| `rounded-lg` fuera de la escala | 228 | 0 |
| Radios arbitrarios (`rounded-[…]`) | 16 | 0 |
| Hex crudos en plantillas | 12 | 0 |
| `!important` sobre clases canónicas | 5 | 0 |

Adopción: `.tsi-btn` 401, `.tsi-badge` 63, `.tsi-input` 106, `.tsi-select` 70,
`.tsi-textarea` 13, `.tsi-hit-target` 12, `.tsi-node` 7, `.tsi-rail` 1.

**Última ambigüedad del documento cerrada:** §5 describía el modal de Alert con "esquinas
10-12px", que es exactamente el rango que la escala de tres pasos vino a eliminar. Pasa a
nombrar el token: un modal `max-w-md` es un contenedor mediano (`--radius-md`), no un panel
grande.

**Corrección de un diagnóstico anterior:** en el inventario inicial se señaló
`preferencias` y `transferencia` como "las de peor deuda del repo". Era falso, y el error
estaba en la métrica: se contaban menciones de clases canónicas por archivo, así que las
páginas pequeñas puntuaban bajo por ser pequeñas, no por estar sin migrar. Ambas tienen
28-32 líneas y ya usaban `.tsi-select` y `.tsi-btn`.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

---

## 2026-08-24 — Departamento 5: Soporte-cliente y Seguimiento

**Punto de partida distinto al de los anteriores:** Soporte-cliente ya usaba en buena parte
las clases canónicas de §5. El trabajo aquí no fue migrar, sino cerrar los tres huecos que
quedaban.

**Efecto verificado:** 21 elementos migrados y 40 cards de `rounded-lg` a `rounded-md`
entre los dos módulos.

**Tres `<textarea>` estaban parcheados con `!important`.** Llevaban
`class="tsi-input !h-auto min-h-24 py-2.5"` — alguien se topó exactamente con el problema
que motivó `.tsi-textarea` (el `height: 2.75rem` de `.tsi-input` colapsa un textarea a una
línea) y lo resolvió sobrescribiendo la clase canónica desde la plantilla. Ahora usan
`.tsi-textarea` y desaparecen los `!important`. Verificado en vivo: el textarea de
`mis-tickets` mide 96px de alto real, con el radio y el foco del sistema.
Estaban en `mis-tickets`, `detalle-ticket` y — fuera de este departamento —
`cuentas-clientes/gestion-cuenta/baja`, que se corrigió también por ser el mismo defecto.

**"Tomar" y "Resolver" de la cola de tickets estaban por debajo del mínimo de Fitts.**
Llevaban `!min-h-9` (36px) para caber en la fila de badges. La caja compacta es una
decisión de layout razonable; el área de toque no puede encogerse con ella, y §5 pide 44px
justamente en acciones críticas — tomar o resolver un ticket lo son. Se les añade
`.tsi-hit-target`, que mantiene el aspecto compacto y restaura el objetivo de 44px.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

**Verificado en navegador** (`lucia.vera.soporte`, rol de agente): en `/soporte-cliente/cola`
los tres botones con área extendida miden 36px de caja y 44px de área de toque, **sin
ningún par solapado** — que es la condición de uso que §5 impone a `.tsi-hit-target`. Cero
`rounded-lg` residuales y cero `!h-auto` en todo el repo.

**Deuda restante de radios: 188** (era 228). Partners 78, Cuentas-clientes 29, Estratégico
24, Accidentes 20, Ventas-CRM interno 16, Red Operativa 14, Emergencias 7.

---

## 2026-08-24 — NG04014: una ruta rompía el módulo de Suscripciones entero

**Bug preexistente, ajeno al trabajo de diseño.** Apareció al intentar verificar las
pantallas de Suscripciones en el navegador: cualquier ruta bajo `/suscripciones`
renderizaba una página en blanco y la consola daba `NG04014: Invalid configuration of
route 'suscripciones/…'`.

**Causa:** la última ruta hija de `SUSCRIPCIONES_ROUTES` era

```ts
{ path: '', pathMatch: 'full', canActivate: [suscripcionesHomeRedirect] },
```

Una ruta con solo `canActivate` no tiene nada que renderizar. Angular no la ignora: rechaza
**toda la configuración del módulo**, no solo esa entrada, así que las 10 pantallas de
Suscripciones estaban caídas en runtime.

**Efecto verificado:** se le añade `children: []`, que satisface al validador sin cambiar
el comportamiento — `suscripcionesHomeRedirect` redirige devolviendo un `UrlTree`, no
renderizando. `/suscripciones/catalogo-planes` y `/suscripciones/aprobaciones-downgrade`
vuelven a cargar, con el shell y sin errores de consola.

**Por qué la suite no lo cazaba:** los 1425 tests unitarios no montan la configuración de
rutas de la aplicación, así que un `Routes` inválido pasa verde. `ng build` tampoco lo ve:
es una validación de runtime, no de tipos. Es el mismo hueco que ya está anotado para las
plantillas (`tsc --noEmit` no las valida) — aquí el hueco es el router.

**Archivo:** `frontend/src/app/modules/suscripciones/suscripciones.routes.ts`.
Se comprobó que es la única ruta del repo con ese patrón.

---

## 2026-08-24 — Área de toque de los botones de solo ícono

**Causa:** 10 botones de solo ícono medían 28-36px, por debajo del mínimo de 44px que §5
exige por Ley de Fitts. Se habían dejado fuera del barrido del departamento 3 por miedo a
romper el layout de las barras donde viven.

**Efecto verificado:** nueva utilidad `.tsi-hit-target`, que extiende el área de toque a
44x44 con un pseudo-elemento centrado, **sin ocupar espacio en el layout**. Es la técnica
que el propio §5 ya implicaba para la columna de acciones de las tablas: lo que debe medir
44 es el objetivo del dedo, no el dibujo. Aplicada a los 10 (5 en el header del shell, 3 en
la galería de evidencias, 1 en el visor, 1 en el mapa de seguimiento).

**Condición de uso documentada en §5:** no puede haber dos `.tsi-hit-target` con centros a
menos de 44px, porque sus áreas se solaparían y la última en el DOM taparía a la anterior.
Comprobado en vivo en el header, que es el caso más denso: cajas de 36px con `gap-3`
dejan los centros a 48px, y las áreas de 44 no llegan a tocarse.

---

## 2026-08-24 — Departamento 4: Suscripciones

**Efecto verificado:** 47 elementos migrados a las clases canónicas de §5 y 19 cards de
`rounded-lg` a `rounded-md`, en las 10 pantallas del módulo. Mismo barrido por tipo de
elemento que el departamento 3.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

**Verificado en navegador** (`carlos.mendoza.admin`, rol Administrador): botones a 8px de
radio y 44px de alto, cero `rounded-lg` residuales, ningún `<select>` desbordando su
columna, y el riel de nav activa y el nodo hexagonal presentes en el chrome.

**Nota sobre finales de línea:** los scripts del barrido reescriben los archivos con LF.
En los archivos donde no había cambios de contenido (varios `.routes.ts` que se pasaron al
barrido sin coincidencias) eso deja un `M` en `git status` con diff de 0 líneas. Git
normaliza a LF al commitear, así que el contenido versionado no cambia.

---

## 2026-08-24 — Departamento 3: Despacho, Evidencia-Unidad y los estados de listado compartidos

**Causa:** las 6 pantallas de Despacho y Evidencia-Unidad tenían **cero** uso de las
clases canónicas de §5: cada botón, input y select estaba repintado a mano, con 38
variantes distintas de la misma cosa. Es el núcleo operativo del sistema, donde la
coherencia importa más porque el operador lee bajo presión.

**Efecto verificado:** 55 elementos migrados a `.tsi-btn` / `.tsi-input` /
`.tsi-select` / `.tsi-textarea`, y 17 cards de `rounded-lg` (12px) a `rounded-md`
(10px). El barrido se hizo **por tipo de elemento, no por cadena de clases**: la misma
cadena aparecía en `<input>` y en `<select>` de estas páginas, y cada uno necesita una
clase distinta.

**Nueva primitiva `.tsi-textarea`.** `.tsi-input` fija `height: 2.75rem`, así que
aplicarla a un `<textarea>` lo colapsa a una línea. La variante comparte borde, radio,
fondo y anillo de foco, pero cambia el alto fijo por `min-height` del mismo valor.
Documentada en §5.

**Los estados de listado compartidos también entraron, y no eran de este departamento.**
Verificando `/evidencia-unidad/flota` apareció un `rounded-lg` residual y un botón
"Reintentar" que no era canónico. Venían de `shared/ui/list-states/`, que usan *todos*
los módulos — deberían haber ido en la base. Se corrigieron aquí porque benefician a
los departamentos que faltan:

- `app-list-empty-state` y `app-list-error-state`: card a `rounded-md`, botón canónico,
  y el ícono pasa al nodo hexagonal de §3.1 — que es exactamente el caso de uso que esa
  sección le asigna.
- `LIST_TABLE_CLASS` y `LIST_MOBILE_CARD_CLASS` a `rounded-md`.

**Bug de API compartida corregido:** `LIST_FILTER_CONTROL_CLASS` era una sola constante
aplicada tanto a `<input>` como a `<select>` en 5 componentes. Con las clases canónicas
eso deja de ser válido: `.tsi-select` aporta `appearance: none` y el chevron por tema,
que un input no debe llevar. Se separa en `LIST_FILTER_INPUT_CLASS` y
`LIST_FILTER_SELECT_CLASS`; la constante vieja queda como alias del input para no romper
importaciones. 9 `<select>` repartidos por Partners, Red Operativa, Ventas-CRM e Informes
pasan a la clase correcta.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

**Verificado en navegador** (usuario `julio.herrera.despacho`, rol Despacho): botones
canónicos a 8px de radio y 44px de alto mínimo — el mínimo de Fitts que §5 exige y que
varias de las variantes a mano no cumplían —, cards a 10px de forma uniforme, cero
`rounded-lg` residuales y el nodo hexagonal recortando correctamente.

**Límite de esta verificación:** el backend Docker devuelve 403 para los endpoints de
despacho con los usuarios demo disponibles, así que solo se pudieron ver los estados de
error de esas pantallas, no las poblacionadas. La corrección es mecánica y está cubierta
por la suite, pero conviene una pasada visual cuando haya datos.

**Fuera del barrido, a propósito:** los botones de solo ícono de estas páginas miden
28-36px, por debajo del mínimo de 44px de §5. `.tsi-btn-icon` los llevaría a 44px, lo
que cambia el layout de las barras donde viven — es un cambio de diseño, no de estilo, y
merece su propia decisión.

**Deuda restante de radios**, para dimensionar lo que falta: Partners 78, Suscripciones
38, Cuentas-clientes 29, Soporte-cliente 28, Estratégico 24, Accidentes 20, Ventas-CRM
interno 16, Red Operativa 14, Seguimiento 12, Emergencias 7.

---

## 2026-08-24 — Departamento 1: Auth y portal público de Ventas-CRM

**Causa:** el panel de marca de las pantallas públicas estaba duplicado literal entre
`login.page.html` y `registro-publico.page.html` — mismo SVG, mismos hex crudos
(`#14161f`, `#ffffff`), copiados a mano. Eran los 12 últimos hex hardcodeados en
plantillas del sistema. Además el patrón de líneas no decía nada del logo: dos trazos
sueltos y tres puntos, decoración genérica de "red".

**Efecto verificado** (dev server :4300 contra backend Docker, ambos temas):

- Nuevo `app-brand-panel` (`shared/brand/brand-panel.component.ts`) con el panel
  completo parametrizado por `eyebrow` / `headline` / `body` / `status`. El fondo deja
  el hex fijo y pasa a `.tsi-node-surface`, así que ahora sigue el tema.
- El patrón pasa a ser el isotipo de verdad: **tres vías que convergen en el hexágono**,
  cada una dibujada dos veces — trazo grueso en cian y divisoria fina encima, la misma
  construcción del logo. Es el rol que §3.1 le da al cian sobre esa superficie: trazo,
  no relleno.
- `catalogo-planes`, `registro-publico`, `login`, `access-denied` y `password-reset`
  pasan a las clases canónicas de §5 (`.tsi-btn`, `.tsi-input`, `.tsi-select`) en vez de
  repintar cada control a mano. Radios alineados a la escala: cards a `rounded-md`
  (10px), botones y badges a `rounded-sm` (8px).
- `catalogo-planes`: los estados de error y vacío no tenían ícono, que §5 exige. El
  vacío usa el nodo hexagonal de §3.1; el de error, `alert-octagon`.

**Bug de tema encontrado y corregido:** los dos `<select>` de `registro-publico` traían
el chevron como `style` inline con el gris `#6b7280` escrito a mano — un color que no
es de la paleta y que no cambia con el tema, así que en modo oscuro quedaba
prácticamente invisible sobre `bg-page`. `.tsi-select` ya trae un chevron por tema;
verificado en vivo que ahora resuelve a `#5a5e70` en claro y `#8a8da0` en oscuro.

**Hex crudos en plantillas: 0.** Era 12 al empezar el departamento.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio.

**Verificado en navegador:** panel con el degradado de convergencia en ambos temas
(claro `#001A38→#00558F`, oscuro `#0A0F1C→#00558F`), 8 paths (4 vías × 2 capas),
cards a 10px, botones y badges a 8px, cero `rounded-lg` y cero radios arbitrarios en
las tres pantallas públicas, sin errores de consola.

**No incluido (siguiente tanda):** las páginas *internas* de Ventas-CRM
(`gestion/pantalla-z`, `pipeline-board`, `detalle-prospecto`, `entrada-directa`,
`informes/indice`) siguen con cards en `rounded-lg` (12px donde la escala pide 10px).
Pertenecen al módulo interno, no al portal público.

---

## 2026-08-24 — El riel llega al shell y a la navegación

**Causa:** las primitivas de §3.1 quedaron definidas pero sin aplicar. El shell es
el primer sitio donde deben materializarse porque es el único archivo que toca las
~55 vistas del sistema a la vez.

**Efecto verificado** (dev server en :4300 contra el backend Docker, sesión
`carlos.mendoza.admin@demo.tsi.com`, ambos temas):

- El item activo del sidebar deja el `border-l-4` plano y pasa al riel `.tsi-rail`.
  El hueco de 5px se reserva también en los items inactivos, para que la etiqueta no
  salte al navegar. El riel lleva margen vertical para que el radio del item no le
  corte la divisoria.
- Estado vacío del sidebar ("Tu rol no tiene módulos…"): pasa de un `<p>` suelto al
  nodo hexagonal `.tsi-node` con ícono, que es el contenedor de ícono que §5 pide
  para estados vacíos.
- Radios alineados a la escala nueva: los controles del header (menú, tema, región,
  campana, cerrar sesión) bajan de `rounded-md` a `rounded-sm`, que es el paso de la
  escala que corresponde a botones. El chip de roles deja `rounded-full` — §5 exige
  que los chips de estado **no** sean full-round; el avatar sí lo conserva, que es la
  única excepción declarada.

**El riel mide 5px, no 4 — y el motivo importa.** La primera versión usaba 4px con
reparto 1.5/1/1.5. Medido en navegador a `devicePixelRatio: 1`, esa divisoria caía
entre los píxeles 13.5 y 14.5: se repartía al 50% entre dos píxeles y se pintaba como
un borrón gris en vez de una línea, perdiendo justo lo que hace reconocible a la
primitiva. Con 5px el reparto es 2/1/2 y el groove cae sobre un píxel entero
(verificado: 14→15). La regla queda escrita en §3.1: **ancho impar, groove de 1px**.

**Anillo de foco verificado en vivo:** `.tsi-input:focus` resuelve a navy `#002B5B` al
15% y borde navy, siguiendo el tema. Es la comprobación de que el `#2E6FF2` que la
entrada de v7 daba por eliminado está realmente muerto.

**Archivos:** `frontend/src/app/shared/layout/app-shell.component.ts`,
`frontend/src/styles.css`, `.specify/docs/design/design-system.md` §3.1, §5.

**Suites:** `ng test` completo, 1425 passed. `ng build` limpio (los avisos de
`TablerIconComponent` sin usar y los de `DetalleAccidentePage` son preexistentes y de
módulos no tocados aquí).

**Deuda detectada, no corregida aquí:** `rounded-md` pasó de 8px a 10px al fijar la
escala, así que los ~596 usos repartidos por las páginas ahora valen 10px. Para los
contenedores es correcto; para los botones ad hoc de cada módulo el paso correcto es
`rounded-sm` (8px). Los botones canónicos (`.tsi-btn`) ya estaban en 8px y no se ven
afectados. La corrección va en el barrido por departamento. Página de Prospectos
verificada como muestra: usa `<select>` planos en vez de `.tsi-select`, misma deuda.

---

## 2026-08-24 — Lenguaje de forma Nodo Integral (design-system v7.2)

**Causa:** la identidad Nodo Integral se había resuelto solo como paleta. Navy + cian
es la combinación de buena parte del software institucional: sin geometría propia, el
sistema seguía leyéndose genérico. La §3 describía el isotipo (tres vías con divisoria
interior convergiendo en un hexágono) pero nada de esa forma existía en la UI, y el
cian quedaba declarado como "referencia de matiz" sin ningún trabajo asignado.

**Efecto verificado:**

- Nueva §3.1 con tres primitivas derivadas del isotipo: `.tsi-rail` (barra de 4px con
  divisoria de 1px por dentro — nav activa, spine de sección), `.tsi-node` (recorte
  hexagonal — contenedor de ícono en vacíos, pines de mapa) y `.tsi-node-surface`
  (degradado de convergencia — solo chrome de marca). Las tres bajo la regla de §1:
  solo donde ya hay estructura, nunca como ornamentación suelta.
- El cian pasa a token con rol definido: `--accent-flow` = `#0090C8` en claro (3.6:1
  sobre `bg-surface`, cumple el mínimo 3:1 de componente no textual) y `#00A8E8` en
  oscuro (6.1:1). Es trazo e indicador, nunca relleno con texto encima: el cian crudo
  da 2.7:1 tanto bajo texto blanco como sobre blanco.
- `--gradient-node` se detiene en `#00558F` en vez de llegar al cian del logo: con
  texto blanco encima, el peor punto del degradado queda en 7.8:1 en vez de 2.7:1.
- Ring charts: el arco "en proceso" pasa de `accent-hover` a `accent-flow`.
  `accent-hover` es estado de interacción, no un segundo color de marca.

**Contradicción de radios corregida:** §5 fijaba cards en 8-10px y §5 "Layout general"
las fijaba en 12-16px, en el mismo documento. La escala se reduce a tres tokens sin
solapamiento (`--radius-sm` 8px / `--radius-md` 10px / `--radius-lg` 12px) y el layout
pasa a `--radius-md`; 16px caía de lleno en la "suavidad excesiva" que §1 descarta.

**Deuda de v7 cerrada:** la entrada de v7 daba por hecho que los `rgba(46,111,242,…)`
del azul eléctrico ya habían pasado a `color-mix` sobre el token. No era así: seguían
vivos en `styles.css` en el anillo de foco de `.tsi-input`/`.tsi-select` y en el hover
de `.tsi-btn-ghost`, ignorando el tema. Ahora usan `--accent-ring` y `--accent-soft`.

**Archivos:** `frontend/src/styles.css`, `.specify/docs/design/design-system.md`
§3.1 (nueva), §5.

**Pendiente (no incluido aquí):** las primitivas están definidas pero aún no aplicadas
a pantallas. El despliegue va por etapas: shell + navegación primero (toca todas las
vistas), luego departamento por departamento.

---

## 2026-08-24 — D2: el toast de éxito se leía como un chip ajeno

**Causa:** `app-toast-host` pintaba una card `bg-surface` con el texto/ícono teñidos de verde y una X tipográfica. Tras la paleta Nodo Integral (navy/cian), ese bloque flotante no comparte ni fondo ni geometría con el resto del chrome.

**Efecto verificado:** el toast de éxito usa `exito-bg` + borde izquierdo semántico + ícono Tabler; el mensaje queda en `text-primary`. En oscuro se separa del `bg-page` con `border-default` y sombra negra (la sombra clara anterior era invisible). El host ya no cubre un rectángulo de 400px que intercepta clics sobre el historial a la derecha (`pointer-events` solo en el toast).

**Archivos:** `frontend/src/app/shared/notifications/toast-host.component.ts`, `frontend/src/styles.css`, `.specify/docs/design/design-system.md` §5.

---

## 2026-08-24 — Paleta Nodo Integral (design-system v7)

El acento de UI deja el azul eléctrico genérico (`#2E6FF2`) y se deriva del logo
Nodo Integral (navy `#002B5B` / cian `#00A8E8`). Los hex del isotipo no se copian
crudos: en claro el primario es el navy; en oscuro un cian oscurecido (`#007AAF`)
para que el botón con texto blanco cumpla contraste y no se funda con `bg-surface`.

Fuente de verdad: `.specify/docs/design/design-system.md` §1, §3, §5, §6.
Tokens en `frontend/src/styles.css`. Los `rgba(46,111,242,…)` que ignoraban el
tema pasan a `color-mix` / `ring-accent-primary/15` sobre el token.

---

## 2026-08-23 — C16: el plan global se queda sin reglas pendientes

Cierre de `PG-RES-005` y `PG-UI-006`, las dos últimas. El plan queda en **34 cubiertas, 23
parciales, 0 pendientes**.

**La cadena crítica bajo carga, medida por primera vez (`PG-RES-005`).** 30 registros con 10
peticiones concurrentes contra el stack en marcha, con autenticación real.

✅ **Sin pérdida de eventos:** los 30 accidentes aceptados con `201` eran consultables tras la
ingesta. Ese era el criterio que importaba — un `201` es una promesa, y un reporte confirmado que
después no existe la rompe sin que nadie reciba un error.

❌ **P95 = 708 ms frente a los 500 ms de `testing.md`.** El diagnóstico costó separarlo en tres:
desde el host daban 1477 ms, pero **~600 ms eran el puente de red de Docker Desktop en Windows**,
no la aplicación; desde dentro del contenedor, 857 ms; y con gunicorn en vez de `manage.py
runserver` —el servidor de desarrollo con el que sirve hoy el contenedor— 708 ms. Sigue
incumpliendo, por menos. La prueba queda en `xfail(strict=True)`: no se ignora, y avisa en cuanto
empiece a cumplirse. Decisión registrada.

**La regla de accesibilidad se apoyaba en algo que no existe (`PG-UI-006`).** Decía «verificable
con axe en la suite E2E», y el proyecto no tiene suite E2E: ni Playwright ni Cypress. Llevaba
desde el principio sin poder cumplirse y el motivo no estaba escrito en ninguna parte.

Se comprueba ahora con `axe-core` sobre el DOM que Angular renderiza en Karma. **Defecto real
encontrado:** el marcador arrastrable del mapa de registro no tenía nombre accesible
(`aria-command-name`, *serious*) — Leaflet lo renderiza focusable e interactivo, así que un lector
de pantalla anunciaba que había un control sin poder decir que era la ubicación del accidente ni
que se podía mover. Corregido con `alt` y `title`.

Queda `⚠️ Parcial` a propósito: este enfoque no ve el orden de tabulación entre pantallas, el foco
tras navegar, ni el contraste con los estilos globales cargados. Está declarado donde vive el
código, para que nadie lea «accesibilidad ✅» y suponga más de lo comprobado.

**De paso, el entorno.** El contenedor de Django se reconstruyó para poder medir —corría código
anterior a los cambios del día, y `/api/v1/salud` devolvía 404 aunque la ruta ya existía—. El
gunicorn instalado para comparar se desinstaló y el contenedor se recreó para no dejar rastro.
Quedan ~65 accidentes de prueba en la base local, localizables por su descripción.

**Verificación.** Frontend: **1423 SUCCESS**. La prueba de carga y la de accesibilidad llevan cada
una su control de no-vacuidad, porque tres veces esta misma sesión una suite pasó en verde sin
comprobar nada.

## 2026-08-23 — C15: cinco reglas del plan global, y el defecto que solo aparece con dos operadores

Cierre de `PG-NEG-001`, `PG-NEG-002`, `PG-CFG-005`, `PG-RES-006` y `PG-UI-003`/`PG-UI-005`.
El plan pasa de 28/21/8 a **34 cubiertas, 21 parciales, 2 pendientes**, y ninguna regla
bloqueante queda en ❌.

**Una ambulancia asignada dos veces, sin un solo error (`PG-NEG-002`).** `asignar()` comprobaba
la disponibilidad leyendo de Pinot y luego escribía vía Kafka. Con dos operadores simultáneos se
crearon **dos despachos activos para la misma unidad y ambos vieron confirmación**. La ventana no
mide milisegundos entre hilos: mide lo que tarda la ingesta, porque la comprobación de la segunda
petición no puede ver el despacho que la primera acaba de crear.

Arreglado con `core/seguridad/reserva_unidad.py`: comprobación y escritura pasan a ocurrir dentro
de una reserva tomada con `cache.add()` —comprobar-e-insertar atómico, la misma llamada en LocMem
que en Redis—. ⚠️ Sin `CACHES` configurado la reserva es **por proceso**: con varios workers la
ventana se reduce, no desaparece. Registrado como decisión de infraestructura pendiente.

**La prueba pasó en verde tres veces sin probar nada.** Los accidentes no existían; luego la
unidad elegida ya tenía despacho activo en la siembra; luego el estado por defecto de una unidad
sin historial resultó ser «Fuera de servicio». Cada caso hacía que las dos llamadas fallaran antes
de llegar a la carrera. La prueba lleva ahora asertos que fallan si eso vuelve a ocurrir.

**Un escaneo de secretos que nunca se había ejecutado (`PG-CFG-005`).** `gitleaks` estaba en CI
desde el principio, así que la regla figuraba cubierta. Al correrlo por primera vez sobre los 30
commits salieron 9 hallazgos: los 9 revisados uno a uno, ninguno es un secreto. Se añadió
`.gitleaks.toml` con la excepción razonada fichero a fichero, y `GITLEAKS_CONFIG` al workflow —sin
esa variable el paso queda en rojo permanente, y un escaneo que siempre falla deja de leerse.

**Tres migraciones escribían sin respaldo previo (`PG-RES-006`).** El patrón correcto existía,
copiado a mano en cada script, así que las que se lo saltaron no rompieron nada visible:
simplemente no tenían red. Extraído a `database/_reversion.py`, donde `respaldar()` **relee** el
fichero antes de darlo por bueno y aborta con los datos aún intactos si no cuadra.

⚠️ **La propia prueba tenía un salto silencioso:** su detector de escrituras solo miraba
`publish(`, así que `migra_plan_programado.py` —que escribe con un POST al controller— se saltaba
las tres comprobaciones dándose por solo-lectura. Ahora falla si alguna migración deja de
reconocerse como escritora.

**El frontend no miraba el `401` en ningún sitio (`PG-UI-003`).** Ni una línea. La sesión caducaba
y el usuario se quedaba en una pantalla muerta pulsando botones que ya no hacían nada. El nuevo
`sesionExpiradaInterceptor` limpia la sesión, explica por qué, y redirige con `returnUrl` —pero
**no** llama a `localStorage.clear()`: borra las cinco claves de sesión una a una y conserva el
parte de accidente a medio escribir, que es justo lo que la regla protege.

**El canal SSE de despacho mentía al parecer que funcionaba (`PG-UI-005`).** Ante un error marcaba
`offline` y no reintentaba nunca; y `complete` no estaba manejado, así que un cierre limpio del
upstream —lo que hace nginx con streams largos— dejaba el estado en `live` mostrando el último
dato como si fuera actual. Su única prueba anterior comprobaba que un `Observable` es un
`Observable`.

**Verificación.** Backend: **4909 passed**, 1125 skipped. Frontend: **1418 SUCCESS**. Cada arreglo
se comprobó rompiéndolo a propósito: sin la reserva, la carrera produce dos despachos; con
`localStorage.clear()`, cae el aserto del borrador; sin el manejo de `complete`, cae el del SSE; y
con la allowlist puesta, gitleaks sigue detectando una clave AWS realista.

## 2026-08-23 — C14: las 79 tablas migran a `fecha_actualizacion` como criterio de upsert

**Decisión del responsable** sobre `decisiones-pendientes.md` #52: el upsert debe regirse por
`fecha_actualizacion`, no por fechas de negocio.

**El problema era peor de lo que se había descrito.** El análisis inicial decía que las
correcciones «ganaban por el desempate del motor en vez de por comparación». Al leer la
configuración viva apareció `dropOutOfOrderRecord: false`, que significa algo más fuerte: **la
última fila ingerida gana aunque su valor de comparación sea más antiguo**.

Con `fecha_emision` como criterio, un evento reentregado con retraso —lo normal en Kafka, que
garantiza *al menos una vez*— podía **devolver una fila a un estado anterior sin que nada lo
delatara**. Una factura corregida volvía a su versión previa; una sesión cerrada volvía a abierta.
Que no se hubiera manifestado dependía del orden de llegada, no de ninguna garantía.

**La migración.**

Antes de tocar nada se comprobó lo que la haría inviable: que las 26 tablas **tuvieran**
`fecha_actualizacion` (las 26, tipo `LONG`) y que se poblara con valores válidos (verificado en
Pinot: mínimos entre 2026-02 y 2026-08, ninguno nulo ni cero). Migrar a una columna ausente habría
cambiado un criterio frágil por uno inexistente.

- `database/tablas.json`: 26 entradas, fuente de verdad del aprovisionamiento.
- **Las tablas vivas**, por `PUT /tables/{n}_REALTIME` del controller. Se probó primero en
  `Fact_Factura` y se verificó antes de seguir: config aplicada, 8 filas intactas, segmento
  `CONSUMING`.

**Efecto verificado, sin pérdida ni interrupción:**

```
Fact_Accidente  4258 (antes 4258)    Fact_Session  1160 (antes 1160)
Fact_Despacho   4314 (antes 4314)    Fact_Factura     8 (antes 8)
estados de sesión: 292 cerradas / 858 abiertas / 10 expulsadas — intactos
tablas sin consumidor activo: ninguna
79 de 79 tablas vivas con comparisonColumns = ["fecha_actualizacion"]
```

**Un falso negativo corregido de paso.** La prueba que comprobaba que la columna se puebla miraba
en `kafka_writer.py` y no la encontraba en ninguno: el productor solo publica lo que recibe, y la
marca la ponen los **repositorios**. Buscar en el sitio equivocado habría hecho fallar una
comprobación correcta.

**Archivos tocados.** `database/tablas.json`, `backend/tests/seguridad/test_escritura_operacional.py`
y las 26 configuraciones vivas de Pinot.

**Trazabilidad.** `PG-OPE-005` (✅) · `decisiones-pendientes.md` #52 cerrada.

---

## 2026-08-23 — C13: la infraestructura estaba levantada, y con ella cayeron cinco reglas

**El cambio de contexto.** Docker tenía todo corriendo —Pinot, Kafka, ClickHouse, Airflow—. Las
suites de integración se saltaban porque usan los nombres de red de Docker (`pinot-broker`,
`tactico-clickhouse`) y desde el host están en `localhost`. Con las variables de entorno correctas,
once reglas dejaron de estar bloqueadas.

### Primero: las pruebas de integración estaban mockeadas

`_pinot_en_memoria` tiene `autouse=True` y alcanzaba **también a las suites `integration`**.
`test_reconciliacion_integracion` comparaba el almacén en memoria contra ClickHouse y reportaba
discrepancias inventadas: el «100 en origen» eran las filas que esa misma fixture sembraba.

Una prueba de integración silenciosamente mockeada es el peor de los dos mundos: no prueba la
integración **y además miente sobre lo que encontró**. Afectaba igual a `test_inyeccion_integracion`
(C8), que por tanto tampoco probaba nada.

### `PG-ANA-001` → ✅ · 22 de 25 cuadran exactos

Contra motores reales, incluidas las sumas de heridos, víctimas y montos. Los 3 restantes son
desfase de carga y **avisan en vez de fallar**: no hay nada que arreglar en la transformación, hay
un DAG que reanudar.

Corregido un mapeo propio: `hecho_evidencia` guarda **fotos y notas en la misma tabla** y se
cuadraba solo contra `Dim_EvidenciaFoto`, dando «sobran 49» — que parece un duplicado y era otra
cosa dentro. Partido en dos correspondencias por tipo.

### `PG-ANA-002` → ⚠️ · y una corrección de diagnóstico

Primera medida: 17 tablas desactualizadas. **Era falso.** Medía por `fecha`, que es la fecha de
**negocio** y puede estar en el futuro — `hecho_suscripcion` tiene contratos que empiezan en meses,
así que daba «−100 días de antigüedad» y pasaba el control sin haberse cargado nunca.

Existe `cargado_en` en todas las tablas: el instante real de la corrida. Medido bien, las tablas
atrasadas son **5, no 17**: `hecho_despacho`, `hecho_estado_unidad`, `hecho_ping_unidad`,
`hecho_baja_unidad` y `hecho_validacion_region`, entre 7 y 8 días.

### `PG-OPE-001` y `PG-OPE-002` → ✅

Se consulta `consumingSegmentsInfo` del controller: estado `CONSUMING`, servidores que responden,
offsets consumidos frente al tópico y retraso temporal. **Todo correcto** en la instancia actual.

La reconciliación evento→fila se resuelve **por offsets**, que responde a «¿ha llegado todo?» sin
publicar nada. Un lag creciente es el aviso previo a la pérdida: el consumidor sigue vivo, marca
`CONSUMING`, y cada vez va más atrás.

### `PG-ANA-005` → ✅ · **defecto real corregido**

Las **158 consultas** del catálogo se ejecutan contra ClickHouse real.
`estrategicos/oe5/e5_02_retencion_neta_ingresos.sql` fallaba con «no supertype for types Float64,
Decimal(38,2)»: las dos ramas de un `if()` tenían tipos incompatibles. **Ese informe devolvía 500 la
primera vez que alguien lo abriera**, y ninguna prueba rápida podía verlo.

Corregido convirtiendo la división a `Float64` — el NRR es un ratio, no un importe, así que es su
tipo natural.

⛔ **Se retiró un análisis estático de alias** escrito para esta misma regla. Marcaba ocho consultas
correctas (`ifNull(p.columna, 0) AS columna`, `argMax(idplan, fecha) AS idplan`) que se ejecutan sin
error. Una prueba que señala código correcto se desactiva en cuanto estorba, y con ella se pierde
la que sí protege.

**Dos falsos positivos más del arnés, corregidos antes de reportarlos:** `{mes:String}` viaja como
«YYYY-MM» y `{granularidad:String}` como «mes»; con valores genéricos el motor rechazaba por el
**valor**, no por la consulta.

**Archivos tocados.**

- `backend/core/seguridad/reconciliacion.py` — claves y medidas por lado, `filtro_analitico`,
  frescura por `cargado_en`.
- `backend/tests/seguridad/conftest.py` — el mock no alcanza a `integration`.
- `backend/tests/seguridad/test_frescura_analitica.py`, `test_ingesta_pinot.py`,
  `test_consultas_clickhouse.py` *(nuevos)*.
- `dags/lib/consultas/estrategicos/oe5/e5_02_retencion_neta_ingresos.sql` — el defecto de tipos.
- `.github/workflows/integracion.yml`.

**Trazabilidad.** `PG-ANA-001`, `PG-OPE-001`, `PG-OPE-002`, `PG-ANA-005` → ✅; `PG-ANA-002` → ⚠️.
Plan: **21 ✅ · 19 ⚠️ · 17 ❌**; bloqueantes abiertas de 13 a **10**.

---

## 2026-08-23 — C12: cuadre analítica ↔ operacional (PG-ANA-001)

La regla más importante de la capa analítica: la única que detecta **un informe plausible pero
falso**. ClickHouse es derivada; si un DAG carga de menos, la consulta responde igual de rápido, el
informe se pinta igual de bien y los números son otros. Nadie recibe un error — alguien firma un
documento.

**Lo construido.** `core/seguridad/reconciliacion.py` declara las **20 tablas de hechos** con su
origen en Pinot y genera el SQL de ambos lados. El cuadre compara claves distintas y sumas de
medidas sobre una ventana de 30 días, que es el grano de partición de los DAGs.

### El trabajo real estuvo en los nombres, no en la lógica

La primera versión tenía **un solo campo `clave`**, dando por hecho que ambos lados la llamarían
igual. No es así:

| Analítica (ClickHouse) | Operacional (Pinot) |
|---|---|
| `hecho_sesion.idsesion` | `Fact_Session.idsession` |
| `hecho_llamada_api.idlog` | `Fact_LogLlamadaAPI.idlogllamadaapi` |
| `hecho_onboarding.idonboarding` | `Fact_Onboarding.id_onboarding` |
| `num_vehiculos` | `numvehiculos` |

Con un solo nombre, el cuadre habría fallado por **una columna mal escrita en vez de por un dato
mal cargado**, y nadie distingue una cosa de la otra leyendo el fallo. Se corrigió a clave y medida
**por lado**, y los 20 pares salen de cruzar `dags/lib/ddl.py` con `database/esquemas.json` — no de
adivinar.

Una prueba valida los 20 contra los esquemas reales, y encontró seis medidas mal declaradas antes
de que llegaran a ejecutarse.

### Dos asertos, no uno

El **conteo** detecta filas que faltan o sobran. Las **sumas** detectan el caso que el conteo no
ve: están todas las filas con los valores cambiados. El informe da el número correcto de accidentes
y el número equivocado de heridos, y eso se entrega a aseguradoras.

### Antienvejecimiento

- Una prueba compara `CORRESPONDENCIAS` con las `hecho_*` de `ddl.py`: **una tabla nueva sin cuadre
  queda señalada**. Al escribirla marcó 17 de 20 sin declarar, que era el estado real.
- La suite de integración incluye un control que **falla si ninguna tabla tiene datos**: sin él,
  con los almacenes vacíos cada cuadre se saltaría y el informe diría verde sin comparar nada.
- Otra prueba comprueba que la ventana de 30 días es la misma en epoch-ms y en `Date`. Un día de
  desfase basta para que un mes con carga diaria no cuadre nunca, y se buscaría un fallo en el ETL
  que no existe.

**Efecto verificado.** Suite rápida de seguridad: **681 passed**. La de integración se salta con
mensaje explícito sin los motores levantados, en vez de pasar en vacío.

**Archivos tocados.**

- `backend/core/seguridad/reconciliacion.py` *(nuevo)* — 20 correspondencias y generación de SQL.
- `backend/tests/seguridad/test_reconciliacion.py` *(nuevo)* — 13 pruebas rápidas.
- `backend/tests/seguridad/test_reconciliacion_integracion.py` *(nuevo)* — el cuadre real.
- `.github/workflows/integracion.yml` — levanta el stack `tactico` y ejecuta el cuadre.

⚠️ **Estado honesto: ⚠️ Parcial, no ✅.** El cuadre está **construido, no ejecutado**. Hasta que
corra con ambos motores y los DAGs cargados, no ha comparado un solo número real.

**Trazabilidad.** `PG-ANA-001` → ⚠️ Parcial. Plan: 17 ✅ · 20 ⚠️ · 20 ❌.

---

## 2026-08-23 — C11: las cuatro reglas baratas, y una compuerta de cobertura al 90 %

Cuatro reglas que no requerían infraestructura ni decisiones. Suben las cubiertas de 13 a 17.

### `PG-OPE-007` — Pinot es de solo lectura (✅)

Análisis estático, **no prueba de comportamiento**, y la elección importa: un `INSERT` contra
Pinot no falla de forma observable en una suite con mocks —el doble acepta cualquier SQL, como
demostró C8—. Lo comprobable es que la sentencia **no esté escrita en el árbol**.

Resultado: **ninguna violación**. El sistema respeta el canal único de Kafka.

Una sola excepción, enumerada a mano: `core/pinot/secuencia.py` escribe contra un **SQLite local**
porque Pinot no sabe entregar identificadores únicos bajo concurrencia. Hay una prueba que verifica
que **sigue siendo SQLite**: una exclusión que ya no se comprueba es peor que no tener regla,
porque aparenta cobertura.

⚠️ La primera versión del patrón daba **falsos positivos** —capturaba docstrings que empiezan por
«Create a signed token…»—. Se afinó exigiendo la sintaxis completa (`INSERT INTO`, `DELETE FROM`,
`UPDATE … SET`). No es cosmético: una prueba con falsos positivos se desactiva en cuanto estorba,
y entonces deja de proteger.

### `PG-CI-002` — Cobertura como compuerta (✅)

Medida real: **93 %**. La compuerta se fija en **90**, no en el 80 de `testing.md`, a propósito:
al 80 se podrían perder trece puntos en silencio, que es justo lo que la regla quiere impedir. El
plan puede ser más estricto que la autoridad si lo justifica (§0.1), y queda justificado en el
propio workflow.

### `PG-DOC-002` — Coherencia documental (✅)

`infrastructure.md` §3 rotulaba a Pinot como «Base de datos analítica», contradiciendo a su propio
§1 y confundiéndolo con ClickHouse — que sí lo es y **ni siquiera aparecía en la tabla del stack**.
Corregido, y añadida la fila de ClickHouse marcada como derivada.

`testing.md` daba el E2E por «futuro» con Cypress, cuando el repositorio usa **Playwright** con 4
suites desde hace tiempo. Corregidos la pirámide, la tabla de herramientas y los comandos.

Ambas correcciones dejan anotado **qué decía antes**: una deriva silenciosamente arreglada se
repite, porque nadie sabe que existió.

### `PG-DOC-001` — El plan no puede mentir sobre sí mismo (✅)

Seis pruebas sobre el propio `spec.md`: que toda regla tenga los cuatro campos, que ningún ID se
repita, que **una regla ✅ apunte a una prueba que existe**, que el recuento de la tabla coincida
con las reglas, que la trazabilidad no divergía, y que toda bloqueante abierta diga qué le falta.

La motivación es concreta: la tabla de cobertura ya se desvió dos veces del contenido durante esta
misma jornada. Es el fallo que el plan denuncia en el sistema —afirmar cobertura sin comprobarla—
cometido dentro del propio plan.

**Y funcionó de inmediato:** al marcar las cuatro reglas como ✅, la prueba falló señalando que la
tabla decía 13 y las reglas eran 17. Se corrigió recontando desde el documento.

**Efecto verificado.** Las cuatro pruebas detectan lo que dicen: se introdujo un `INSERT` contra
Pinot y `test_pinot_solo_lectura` lo señaló.

**Archivos tocados.**

- `backend/tests/seguridad/test_pinot_solo_lectura.py`, `test_coherencia_plan.py` *(nuevos)*.
- `.github/workflows/ci.yml` — `--cov-fail-under=90`.
- `.specify/docs/infra/infrastructure.md`, `.specify/docs/architecture/testing.md`.

**Trazabilidad.** `PG-OPE-007`, `PG-CI-002`, `PG-DOC-001`, `PG-DOC-002` → ✅.
Plan global: **17 ✅ · 19 ⚠️ · 21 ❌**; bloqueantes abiertas de 14 a **13**.

---

## 2026-08-23 — C10: degradación selectiva ante caída del almacén de sesión

**Confirmada por el responsable** la lista de 9 rutas de `research.md` §R5.1. Cierra `PG-SEC-003`.

**El problema.** Validar una sesión son dos pasos con propiedades distintas:
`verify_access_token` es criptografía pura sin E/S y funciona con el almacén caído; solo
`is_active` depende de infraestructura. El código anterior las trataba igual —ambas terminaban en
excepción— y por tanto era **fail-closed universal**: una caída de Redis dejaba fuera también a la
cadena crítica. Nadie despachaba una ambulancia mientras Redis no respondiera.

**La regla implementada:**

| Situación | Fuera de la cadena | En la cadena |
|---|---|---|
| Sesión revocada (`is_active` → `False`) | `401` | **`401` también** |
| No se puede comprobar (`is_active` lanza) | `401` | Degradar y continuar |

⚠️ **La distinción que hace que esto sea seguro:** «revocada» y «no puedo comprobar si está
revocada» son cosas distintas. Degradar ante una caída es una concesión al Principio IX; dejar
entrar a quien se le retiró el acceso **a propósito** no lo es — ahí no hay dilema de seguridad
física, solo un acceso revocado. Una nueva excepción `AlmacenSesionNoDisponible` separa ambos casos.

**Lo que se sacrifica, dicho explícitamente:** durante una caída, un token robado y revocado hace
minutos sigue sirviendo **en esas nueve rutas** hasta expirar. Ventana acotada por la vigencia del
token, y queda **registrada en WARNING**: sin esa línea, el periodo en que se admitieron sesiones
sin verificar no constaría en ninguna parte y no sería auditable después.

**Dónde vive la decisión.** La cadena crítica se resuelve en `JWTSessionAuthentication`, el único
punto que conoce la ruta; el servicio recibe la decisión ya tomada en vez de importar el enrutador
para inspeccionarla.

**Efecto verificado — las dos mitades, por separado.**

- Desactivando la degradación: falla `test_con_el_almacen_caido_la_cadena_critica_sigue_operativa`.
- Degradando **también** las sesiones revocadas (el error clásico al implementar esto): falla
  `test_una_sesion_revocada_se_deniega_TAMBIEN_en_la_cadena_critica`.

Ambas comprobaciones importan: la primera verifica que la excepción existe, la segunda que **no se
ha ensanchado**. 20 pruebas en total.

**Antienvejecimiento.** `test_la_lista_de_la_cadena_critica_no_crece_sin_que_nadie_lo_note` fija el
número en 9. Cada ruta añadida amplía la ventana de riesgo, y cada añadido parece razonable por
separado — sin el aserto, la excepción se ensancharía poco a poco sin revisión.

**Archivos tocados.**

- `backend/core/seguridad/cadena_critica.py` *(nuevo)* — las 9 rutas y el criterio.
- `backend/apps/cuentas_clientes/services/session_validation_service.py` — `degradable`,
  `AlmacenSesionNoDisponible`, registro en WARNING.
- `backend/apps/cuentas_clientes/authentication.py` — resuelve la cadena por `request.path`.
- `backend/tests/seguridad/test_integridad_jwt.py` — la prueba de línea base **dividida en cinco**,
  como quedó anotado en C6 que debía hacerse.

**Trazabilidad.** `PG-SEC-003` → ✅. `decisiones-pendientes.md` #52 (la de T031) cerrada.

---

## 2026-08-23 — C9: las cuatro reglas P2 de seguridad, cerradas

**Contexto.** US6–US9 de `Endurecimiento-Seguridad`: límite de tasa, subida de archivos,
cabeceras/CSP y aislamiento de la demo. Cierra el bloque `PG-SEC-*` salvo lo que depende de
infraestructura real o de una decisión pendiente.

### `PG-SEC-004` — Límite de tasa (✅)

Había **cinco** throttles declarados y **ninguno con prueba**. Un throttle sin verificar es peor
que no tenerlo: figura en la configuración, se cuenta como control existente al evaluar el riesgo,
y nadie comprueba que DRF lo aplique.

11 pruebas. Se comprobó de verdad que superar el cupo devuelve `429` (15 peticiones contra un cupo
de 10/min). La suite se parametriza sobre el registro real, y una prueba recorre `apps/` buscando
subclases de `SimpleRateThrottle` para que un throttle nuevo sin prueba **rompa la suite**.

Se incluye una prueba que impide «arreglar» el sistema añadiendo un `429` por cuota **mensual** de
partner: `RN-APM-002` dice que el cupo mensual no bloquea, se factura. Sería romper una regla de
negocio deliberada creyendo reforzar la seguridad.

### `PG-SEC-006` — Subida de archivos (✅) — **vulnerabilidad corregida**

`SubirEvidenciaFotoView` tomaba el tipo de `archivo.content_type`, una cabecera **que envía el
cliente**. Validar con ella es preguntarle al fichero si es peligroso: un ejecutable renombrado a
`.jpg` y anunciado como `image/jpeg` entraba sin más.

Nuevo `core/seguridad/validacion_archivos.py` con `puremagic`: valida por **bytes mágicos**, aplica
el techo de tamaño antes que el formato, y sanea el nombre. 20 pruebas.

El mensaje de error **no dice qué tipo se detectó** (contrato C5): «se esperaba una imagen» basta
para el usuario legítimo; «se detectó un ejecutable PE» le confirma al atacante que la detección
funciona y por dónde va.

### `PG-SEC-008` — Cabeceras y CSP (✅)

`frontend/nginx.conf` **no declaraba ninguna cabecera de seguridad**: Django las enviaba en `/api/`
y la aplicación Angular quedaba descubierta. Es el error natural, porque al probar la API se ve
todo correcto.

Añadidas las tres que no dependen de HTTPS más una CSP con `script-src 'self'` —sin
`unsafe-inline`, que es donde la directiva protege de verdad— y `frame-ancestors 'none'`.

⚠️ **Todas con `always`.** Sin ese modificador nginx omite `add_header` en 4xx y 5xx: el navegador
la recibe en el camino feliz, una revisión manual la ve, y desaparece justo en las respuestas que
un atacante provoca a propósito. Hay una prueba dedicada a ese modificador.

### `PG-SEC-010` — Aislamiento de la demo (✅)

Un token de demo lo obtiene **cualquier visitante** que rellene el formulario de prospecto, sin que
nadie apruebe nada. 9 pruebas confirman que no abre ningún endpoint de negocio, que no lleva
`roles` ni `session_id` con los que autorizar, y que las dos familias usan algoritmos y secretos
distintos — así que filtrar el secreto de la demo no permite firmar credenciales del sistema.

### T069/T070 — el pipeline

- `ci.yml`: la suite de seguridad corre en el job `configuracion`, **no** en `backend`, para que un
  fallo de seguridad se distinga de uno funcional de un vistazo. Mezclarlos hace que el segundo
  tape al primero.
- `integracion.yml`: `test_inyeccion_integracion.py` contra motores reales.
- **SC-002 verificado a mano**: añadiendo un endpoint con identificador, la suite **falla**.

**Efecto verificado.** Suite de seguridad: **596 → 652 passed**. `apps/accidentes` tras conectar la
validación de subidas: 367 passed.

**Archivos tocados.**

- `backend/core/seguridad/validacion_archivos.py` *(nuevo)*.
- `backend/apps/accidentes/views/evidencia_views.py` — validación por bytes.
- `frontend/nginx.conf` — cabeceras y CSP.
- `backend/tests/seguridad/test_throttles.py`, `test_subida_archivos.py`, `test_cabeceras.py`,
  `test_aislamiento_demo.py` *(nuevos)* — 56 pruebas.
- `.github/workflows/ci.yml`, `integracion.yml`.

**Trazabilidad.** `PG-SEC-004`, `PG-SEC-006`, `PG-SEC-008`, `PG-SEC-010` → ✅.

---

## 2026-08-23 — C8: la suite de inyección no detectaba inyecciones

**Contexto.** US4 de `Endurecimiento-Seguridad` (`PG-SEC-005`). La superficie de mayor riesgo del
sistema: informes con filtros dinámicos y `ORDER BY` variable, donde la parametrización estándar
no aplica.

### Lo que el código ya hacía bien

Revisión de `core/repositories/**` y `core/clickhouse/client.py`:

- Los `WHERE` usan parámetros con nombre (`%(campo)s`) y un diccionario aparte.
- ClickHouse liga **del lado del servidor** con tipos declarados (`{desde:Date}` → `param_desde`),
  la forma más segura de las disponibles.
- El `ORDER BY` se compone de nombres de columna que son **constantes de código** más un
  `ASC`/`DESC` derivado de un booleano: `parse_dir` solo admite `asc` o `desc` y devuelve un
  `NamedTuple`, así que ninguna cadena del usuario alcanza la sentencia.

**Ninguna vulnerabilidad de inyección encontrada.**

### El hallazgo: la suite que lo comprobaba no comprobaba nada

Escrita la suite rápida —62 parámetros × 8 cargas × 70 endpoints, unas 34.700 peticiones— dio
**499 passed**. Para verificar que detecta lo que dice, se introdujo una vulnerabilidad real: que
`parse_dir` metiera la entrada cruda en el `ORDER BY`, que es el descuido exacto que cometería un
desarrollador con prisa.

**Las 497 pruebas siguieron en verde.**

La causa: el doble de Pinot de `conftest.py` **no analiza SQL**, hace coincidencia de patrones
sobre la cadena. Acepta igual una consulta correcta que una inyectada, así que ninguna carga puede
tener efecto observable.

> Lo irónico es que `research.md` §R7 y la tarea T048 ya lo decían por escrito —«un mock acepta
> cualquier SQL; solo el motor real revela si la carga alteró la sentencia»— y aun así la suite se
> construyó contra mocks. Escribir la advertencia no basta: hay que **comprobar que la prueba falla
> cuando debe**.

### Un segundo fallo, del mismo tipo

Los nombres de los parámetros de filtro estaban **adivinados**. La suite probaba `orden` cuando el
real es `dir`, y por tanto tocaba parámetros que ningún endpoint lee. Se sustituyeron por los **62
extraídos del código** con `grep query_params.get(`. Adivinar nombres es la forma silenciosa de no
probar nada: la suite pasa, el informe dice «cubierto», y la superficie sigue intacta.

### Corrección

1. `test_inyeccion.py` **declara su límite en la cabecera**: comprueba robustez y discreción —que
   nada devuelva `500` ni mensajes del motor—, **no** ausencia de inyección.
2. `test_inyeccion_integracion.py` *(nuevo)*, marcado `integration`: contra Pinot real, comparando
   el **conjunto devuelto** frente a la consulta legítima. Si la carga se interpretara como SQL, el
   número de filas cambiaría.

**Efecto verificado.** Suite rápida de seguridad: **596 passed**. La de integración se salta con
mensaje explícito si Pinot no está levantado, en vez de pasar en vacío.

**Archivos tocados.**

- `backend/tests/seguridad/test_inyeccion.py` *(nuevo)* — 499 pruebas, con su límite declarado.
- `backend/tests/seguridad/test_inyeccion_integracion.py` *(nuevo)* — 6 pruebas `integration`.

**Trazabilidad.** `PG-SEC-005` (⚠️ Parcial: la verificación real espera a `integracion.yml`).

---

## 2026-08-23 — C7: `POST /usuarios` reventaba con 500 ante un cuerpo incompleto

**Contexto.** US5 de `Endurecimiento-Seguridad` (`PG-SEC-007`, datos sensibles en logs y
respuestas). Lo buscado era una fuga de información; lo encontrado fue el camino que la haría
posible.

**Causa.** `UserListCreateView.post` pasaba `request.data` **en crudo** a
`UserManagementService.create_user`, que hacía `data["gmail"]` sin comprobar nada. Un cuerpo sin
ese campo lanzaba `KeyError` → **500**.

El `500` importa más de lo que parece: es **el único camino que no pasa por
`custom_exception_handler`**, porque `drf_exception_handler` devuelve `None` para las excepciones
que no son de DRF. Es decir, la única respuesta del sistema sobre la que no hay ninguna garantía de
qué muestra. Con `DEBUG=true` —el valor por defecto hasta el arreglo C1 de esta misma jornada—
habría enseñado el traceback completo.

**Corrección.** Validación de campos obligatorios (`nombres`, `apellidos`, `gmail`) en el
**servicio**, no en la vista, para que cualquier otro llamador quede cubierto. Error propio
`DatosInvalidosError` → **400**.

La distinción entre `DatosInvalidosError` (400) y `UserManagementError` (409) es deliberada:
«falta el correo» y «el correo ya está registrado» son cosas distintas. Meterlas en la misma
excepción habría devuelto 409 a un cuerpo malformado, que es engañoso para el cliente.

**Efecto verificado.** `apps/cuentas_clientes` + suite de seguridad: **801 passed**. Retirando la
validación, 4 pruebas vuelven a fallar. Las tres cargas que antes daban `500` ahora dan `400`.

**Lo que la suite confirmó que ya estaba bien.** Los logs **no** escriben datos personales, tokens
ni coordenadas de accidentes en claro, y las respuestas de error no revelan traceback, nombres de
tabla ni SQL. No hizo falta el filtro de enmascarado que el plan preveía (T042): se verificó que no
es necesario en vez de añadirlo por si acaso.

**Archivos tocados.**

- `backend/apps/cuentas_clientes/services/user_management_service.py` — `DatosInvalidosError` y
  validación de obligatorios.
- `backend/apps/cuentas_clientes/views/user_role_views.py` — traducción a 400.
- `backend/tests/seguridad/test_datos_sensibles.py` *(nuevo)* — 11 pruebas.

⚠️ **Deuda declarada.** La validación cubre `POST /usuarios`. **No se auditaron los demás endpoints
de escritura**, y el patrón —`request.data` en crudo hacia un servicio que indexa por clave— puede
repetirse. Es trabajo de `PG-API-004`, que sigue ❌ Pendiente.

**Trazabilidad.** `PG-SEC-007` (⚠️ Parcial) y `PG-API-004` de `specs/Global/PlanPruebas/spec.md`.

---

## 2026-08-23 — C6: el JWT resiste, pero las pruebas no medían el mérito propio

**Contexto.** US3 de `specs/Global/Endurecimiento-Seguridad/` (`PG-SEC-003`, integridad del JWT).
Hasta ahora se probaba que un token **válido** funciona —la mitad fácil, la que no tiene riesgo—.
Faltaba comprobar que los inválidos **no** funcionan.

**Resultado: el sistema aguanta.** Las seis variantes adversariales (firma alterada, `alg: none`,
algoritmo distinto de RS256, expirado, claims manipulados, emisor ajeno) reciben `401`, y una
sesión revocada tampoco entra aunque su token siga criptográficamente impecable. Ninguna corrección
de código fue necesaria: 14 pruebas nuevas, 0 vulnerabilidades.

### El hallazgo está en las pruebas, no en el sistema

Al comprobar que la suite detecta lo que dice detectar —debilitando `verify_access_token` para
admitir `HS256` y `none`— **las 12 primeras seguían en verde**.

El motivo: **PyJWT se defiende solo**. Se niega a usar una clave asimétrica como secreto HMAC,
también del lado de la verificación, así que la confusión de algoritmo falla por la biblioteca y no
por la configuración del proyecto. El ataque no funciona, pero **no por nada que haga TSI**: un
cambio de biblioteca, una versión anterior o una clave simétrica reabrirían la puerta **sin que
ninguna prueba se quejara**.

Se añadieron dos pruebas sobre la configuración propia —lo único bajo control del proyecto— que sí
fallan al debilitarla:

- que `verify_access_token` restrinja `algorithms` a `settings.JWT_ALGORITHM`;
- que un token de otro algoritmo se rechace **por el algoritmo** (`InvalidAlgorithmError`) y no por
  una firma inválida casual, que también daría `401` pero por accidente.

> Es la tercera vez en la sesión que una suite verde resulta no estar midiendo nada (ver C3 y C5).
> El patrón común: **verificar que la prueba falla cuando debe** es más informativo que verla pasar.

### T031 — la disyuntiva fail-closed / fail-open también era falsa

`SessionValidationService.validate_token_and_session` son **dos pasos con propiedades distintas**:
`verify_access_token` es criptografía pura sin E/S y funciona con el almacén caído; solo
`session_repo.is_active` depende de infraestructura. Plantearlo como «denegar todo o admitir todo»
daba por perdida la autenticación entera cuando solo se pierde **la comprobación de revocación**.

Decisión propuesta: **degradación selectiva**. Una sesión revocada se deniega **siempre**, cadena
crítica incluida. Un almacén *inaccesible* deniega fuera de la cadena crítica y degrada al paso
criptográfico dentro de ella. Con criterio estricto —«su denegación retrasa la llegada de ayuda a
una persona»— la lista es de **9 rutas**, no de las 46 del módulo de emergencias.

⚠️ **No implementada:** toca la cadena crítica y la constitución exige justificación explícita de
Safety (Principio IX) y Reliability (II) antes. Pendiente de confirmación del responsable
(T036–T038). Detalle en `research.md` §R5.1.

**Efecto verificado.** `pytest -m "not integration"`: **4239 passed, 0 failed** (venía de 4226).
Suite de seguridad: 87 passed.

**Archivos tocados.**

- `backend/tests/seguridad/test_integridad_jwt.py` *(nuevo)* — 14 pruebas.
- `specs/Global/Endurecimiento-Seguridad/research.md` — §R5.1 con la decisión y las 9 rutas.

**Deuda declarada.** La prueba `test_con_el_almacen_caido_hoy_se_deniega` documenta el
comportamiento **actual** (fail-closed universal) como línea base. Al implementar la degradación
debe **dividirse en dos** —`401` fuera de la cadena, acceso dentro— y no modificarse: cambiarla sin
más borraría la verificación de que el resto del sistema sigue cerrado.

**Trazabilidad.** `PG-SEC-003` (⚠️ Parcial) de `specs/Global/PlanPruebas/spec.md`.

---

## 2026-08-23 — C5: la suite de aislamiento encuentra dos oráculos más, uno fuera de Partners

**Contexto.** Implementación de US1 de `specs/Global/Endurecimiento-Seguridad/` (`PG-SEC-001`).
El objetivo era construir la suite transversal de aislamiento multi-tenant sobre el inventario de
rutas, no sobre una lista escrita a mano.

### Primero, un fallo de la propia suite

La primera ejecución reportó **82 passed** y parecía buena noticia. No lo era: el actor era un
`PartnerIntegracion`, rol que **no alcanza la mayoría de los 92 endpoints con identificador**.
Recibía `403` en 29 de 31 rutas, pero por **autorización vertical, no por tenencia**. La suite
pasaba en verde sin haber ejercitado el aislamiento ni una vez.

Un `403` por rol y un `403` por tenencia son idénticos desde fuera, y solo el segundo dice algo
sobre IDOR. Corregido con **detección de vacuidad**: antes de afirmar nada, la suite comprueba si
el actor alcanza su **propio** recurso en esa ruta; si tampoco, marca `NO EJERCITADA`. Y emite un
informe de cobertura real al terminar, para que el número verde no se confunda con protección.

De «82 passed» a «2 de 92 ejercitadas» — el punto de partida honesto. Tras sembrar dos tenants y
añadir cinco actores por materia (T078), **13 de 155**.

### Las dos vulnerabilidades

**V1 — `GET /api/v1/soporte/tickets/{id_reclamo}`.** Módulo que nadie había revisado; es la prueba
de que el enfoque transversal funciona. `403` = el ticket existe pero es de otro cliente,
`404` = no existe. Un cliente iterando ids deduce qué tickets existen en todo el sistema sin ver
ninguno.

**V2 — `GET /api/v1/partners/{idpartner}`.** Vista que la corrección manual de C4 no alcanzó: allí
se arreglaron `estado_acceso_views` y `metricas_views`. Aquí el `404` venía del **servicio**
(`ConsultaPartnerService`), la variante que T018 predijo. Tuvo **dos capas**: al igualar los
códigos a `403`, el **cuerpo** seguía delatando (`code: propiedad_partner` frente a
`acceso_denegado`). La segunda solo apareció al arreglar la primera.

> **Lección:** igualar el código HTTP no basta. Mientras el cuerpo difiera, el oráculo sigue
> abierto. El motivo real vive ahora en el registro de auditoría, no en la respuesta.

**Efecto verificado.** Suite de seguridad: 73 passed, 0 fallos. `apps/partners` + `apps/soporte_cliente`:
948 passed. Ambas vulnerabilidades vuelven a fallar si se revierte la corrección.

**Archivos tocados.**

- `backend/core/seguridad/inventario_rutas.py` *(nuevo)* — recorrido del `URLResolver`: 234 rutas,
  92 con identificador.
- `backend/core/seguridad/denegacion.py` *(nuevo)* — `resolver_o_denegar` y `respuesta_no_visible`,
  la decisión única que impide que las dos ramas diverjan al editarse por separado.
- `backend/apps/soporte_cliente/views.py` — V1.
- `backend/apps/partners/views/partner_views.py` — V2.
- `backend/tests/seguridad/` *(nuevo)* — suite, fixtures de dos tenants, cinco actores por materia
  y `HALLAZGOS.md`.
- `backend/requirements.txt`, `backend/pytest.ini` — `puremagic` y marker `seguridad`.

⚠️ **Deuda declarada.** 142 de 155 combinaciones siguen **sin ejercitar**: son superficie *sin
examinar*, no superficie limpia. Requieren sembrar accidentes, despacho y red operativa. Anotado
como continuación de T078.

**Trazabilidad.** `PG-SEC-001` (sigue ⚠️ Parcial) de `specs/Global/PlanPruebas/spec.md`.

---

## 2026-08-23 — C4: un partner podía enumerar el padrón de partners ajenos

**Causa.** Las vistas de `apps/partners/views/` resolvían el partner y cortaban con
`404 Partner no encontrado` **antes** de comprobar la propiedad; solo después devolvían `403` si
resultaba ajeno. Para un Partner de integración eso es un oráculo de enumeración: iterando
`idpartner` distingue «no existe» (404) de «existe y no es tuyo» (403), y con eso deduce cuántos
partners hay y en qué rangos de id — es decir, qué competidores son clientes de TSI — sin llegar a
ver un solo dato.

⛔ **`verificar_propiedad` no era la culpable**, pese a lo que sugería una primera lectura: unifica
ambos casos a `403`. El oráculo lo creaba el corte previo de la vista.

**La disyuntiva 403-vs-404 era falsa.** El comentario que había en `metricas_views.py` —«que el
partner no exista no es un problema de permisos»— tenía razón en su eje, y el requisito de
seguridad tenía razón en el suyo. Es el conflicto Seguridad ↔ Idoneidad Funcional del mecanismo de
desempate de la constitución, y aquí no hace falta sacrificar ninguno porque **depende de quién
pregunta**:

- **Gestor** (Administrador, Desarrollador de APIs): opera sobre cualquier partner, así que un
  `404` no le revela nada que no pueda consultar. Conserva el diagnóstico preciso.
- **No gestor**: «no existe» y «no es tuyo» devuelven la misma respuesta con el mismo cuerpo.

**Fuga adicional encontrada de paso.** Los mensajes diferían («Partner no encontrado» vs «El
partner no pertenece al cliente autenticado») y las vistas vuelcan `str(exc)` en `detail`: un texto
distinto filtra la existencia por el cuerpo **aunque el código HTTP sea 403 en ambos casos**.
Unificados en `DENEGACION_UNIFICADA`.

**Efecto verificado.** 11 pruebas nuevas; reintroduciendo la vulnerabilidad fallan 6. Las 744
pruebas de `apps/partners/` siguen pasando. **Sin romper contratos**: `403` y `404` ya estaban
declarados en los OpenAPI; solo cambia cuál recibe un no gestor ante un id inexistente.

**Archivos tocados.**

- `backend/apps/partners/permissions.py` — `resolver_partner_visible()`, `PartnerInexistenteError`,
  `DENEGACION_UNIFICADA`; mensajes unificados en `verificar_propiedad`.
- `backend/apps/partners/views/estado_acceso_views.py`, `metricas_views.py` — usan el helper.
- `backend/apps/partners/tests/unit/test_no_enumeracion_partners.py` *(nuevo)*.

⚠️ **Deuda declarada.** (1) El camino «no existe» retorna antes de consultar el cliente, así que
responde más rápido: queda un canal temporal de menor ancho de banda. (2) Siete servicios
(`consulta_partner_service`, `emitir_credencial_service`, `metricas_consumo_service`,
`promocion_produccion_service`, `reactivar_partner_service`, `suspender_partner_service`,
`asignar_plan_acceso_service`) lanzan `not_found` por su cuenta; hay que revisar si un no gestor
puede alcanzarlos con un id ajeno. Ambos flecos son trabajo de US1 de `Endurecimiento-Seguridad`.

**Trazabilidad.** `PG-SEC-001` de `specs/Global/PlanPruebas/spec.md` (avanza a ⚠️ Parcial) ·
`decisiones-pendientes.md` #51 (cerrada).

---

## 2026-08-23 — C3: 42 pruebas de permisos que fallaban por una fixture ausente

**Causa.** `apps/informes_tacticos/tests/api/test_permisos_red_operativa.py` y
`test_emergencias_compuestos_views.py` fallaban 21 veces cada uno, todos con `401` donde el test
esperaba `403` o `404`. La causa no era de permisos: a ambos ficheros les faltaba la fixture

```python
@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot
```

que sí tienen sus vecinos `test_permisos_cuentas.py` y `test_permisos_partners.py`. Sin ella,
`JWTSessionAuthentication` valida la sesión contra un Pinot **real** que en la suite no está
levantado: la petición espera a que venza el timeout de red y la excepción acaba traducida en
`AuthenticationFailed`, es decir un `401`.

El síntoma engaña por partida doble. Parece un fallo de autorización —y llevó a plantear una
decisión de diseño sobre `401` vs `403` que no existía— cuando es de infraestructura de pruebas.
La pista real era el tiempo: 67 s para 26 pruebas, frente a 1,5 s de las que sí tenían la fixture.

**Efecto verificado.** Los dos ficheros pasan de **42 fallos en ~130 s** a **80 passed en 2,45 s**.
Retiradas las dos exclusiones `--deselect` del job `backend` de `.github/workflows/ci.yml`, con lo
que el pipeline queda sin deuda declarada.

**Tres pruebas aparte, marcadas `integration`.** `test_responde_con_la_forma_del_contrato`,
`test_sin_rango_usa_los_ultimos_treinta_dias` y `test_entra_la_autoridad_del_departamento`
consultan un ClickHouse real (`tactico-clickhouse:8123`). Las dos primeras ya llevaban un
`pytest.skip("el modelo analítico no está disponible")` que **nunca llegaba a evaluarse**: la
conexión lanza `ConnectionError` antes de que haya respuesta que inspeccionar. Por la definición
de markers de `testing.md`, una prueba que necesita infraestructura real es de integración.

⚠️ La tercera es un test de **permisos** que solo necesitaba ClickHouse porque el `GET` concedido
sigue camino hasta la consulta. Marcarla `integration` saca esa cobertura de la suite rápida:
recuperarla pide una fixture `mock_clickhouse` equivalente a `mock_pinot`, que hoy no existe.
Anotado en `decisiones-pendientes.md` #50.

**Archivos tocados.**

- `backend/apps/informes_tacticos/tests/api/test_permisos_red_operativa.py` — fixture.
- `backend/apps/informes_tacticos/tests/api/test_emergencias_compuestos_views.py` — fixture y 3
  markers `integration`.
- `.github/workflows/ci.yml` — retiradas ambas exclusiones y el paso informativo asociado.
- `specs/Global/PlanPruebas/traceability.md` *(nuevo)* — trazabilidad de las 57 reglas, generada
  desde el `spec.md` y no escrita a mano.

**Lección trasladable.** Una prueba lenta que falla por red es indistinguible de una prueba que
falla por lógica, y el mensaje de error apunta al sitio equivocado. Conviene sospechar del
**tiempo de ejecución** antes que del aserto. `PG-CI-003` del plan global cubre esto.

**Trazabilidad.** `PG-CI-003` de `specs/Global/PlanPruebas/spec.md`.

---

## 2026-08-23 — C2: el pipeline de CI, y las dos cosas que destapó al encenderlo

**Causa.** `testing.md` daba la integración continua por «(Futuro)» desde su redacción. El
repositorio tiene 674 pruebas de backend y 250 de frontend cuya ejecución dependía de que alguien
se acordara de lanzarlas. Una suite que no corre sola no protege: es documentación de intenciones.

**Qué se montó.**

- `.github/workflows/ci.yml` — 6 jobs. `rapidas` (`pytest -m unit`, ~15 s) en cada push;
  `configuracion`, `estatico`, `backend` con cobertura, `frontend` y `dependencias` en PR y `main`.
- `.github/workflows/integracion.yml` — `pytest -m integration` semanal (lunes 04:00 UTC) con
  Kafka + Pinot reales levantados desde `docker/docker-compose.infraestructura.yml`.

Separados a propósito: la infraestructura tarda minutos en arrancar antes del primer test, y
encadenarla a cada push haría el ciclo de retroalimentación inservible. Cuando esperar el CI
cuesta, se empieza a hacer push sin esperarlo.

**Los dos hallazgos del propio montaje** — que es exactamente para lo que sirve encender una
compuerta que nunca había estado encendida:

1. **`manage.py check --deploy` falló con 5 advertencias de seguridad reales:** `SECURE_HSTS_SECONDS`
   sin declarar, `SECURE_SSL_REDIRECT` apagado, y las cookies de sesión y CSRF sin `Secure`.
   Corregidas en `config/settings.py`, condicionadas a entorno no local — activarlas siempre
   dejaría el login inservible en el servidor de desarrollo, que corre sobre HTTP plano. HSTS se
   declara explícito (1 año) en vez de heredar el default `0`: una política HSTS mal puesta es
   difícil de revertir, porque el navegador la recuerda aunque el servidor deje de enviarla.

2. **42 pruebas fallan**, repartidas por igual entre
   `apps/informes_tacticos/tests/api/test_permisos_red_operativa.py` (21) y
   `test_emergencias_compuestos_views.py` (21). Todas por lo mismo: la petición llega sin
   autenticar y devuelve `401` donde el test espera `403` o `404`. **Preexistentes** — verificado
   con `git stash` sobre los dos ficheros: fallan igual sin los cambios de este día.

   Que sean exactamente 21 y 21 con el mismo síntoma apunta a **una causa compartida** —
   probablemente el helper que construye el cliente autenticado en esa app— y no a 42 defectos
   sueltos. Resolverlo requiere además decidir si un rol autenticado sin acceso debe recibir 401 o
   403, decisión que no corresponde tomar dentro de «montar el pipeline»: ver
   `decisiones-pendientes.md` **#50**. Excluidas del gate con **caducidad 2026-09-23**, con un paso
   informativo no bloqueante que las sigue ejecutando en cada run.

**Efecto verificado.** `check --deploy` con entorno de producción pasa limpio
(`no issues (0 silenced)`); `manage.py check` local sigue sin cambios; `pytest -m unit` da
206 passed en 15 s; las guardas de configuración, 22 passed. Ambos workflows validados como YAML.

**Archivos tocados.**

- `.github/workflows/ci.yml`, `.github/workflows/integracion.yml` *(nuevos)*.
- `backend/config/settings.py` — bloque de cabeceras y cookies de seguridad (PG-SEC-008).
- `backend/tests/test_configuracion_segura.py` — 2 pruebas más (22 en total).
- `decisiones-pendientes.md` — entrada #50.

**Deuda declarada en el propio workflow.** Ruff, ESLint y Prettier corren con `|| true`: no se han
pasado nunca sobre este árbol y hacerlos bloqueantes de golpe dejaría el pipeline en rojo desde el
primer run, que es la forma más rápida de que se ignore. Retirar los `|| true` cuando el árbol
esté limpio (`PG-CI-004`).

**Trazabilidad.** `PG-CI-001`, `PG-CFG-004`, `PG-SEC-009` (✅); `PG-SEC-008`, `PG-CI-004`
(⚠️ parcial) de `specs/Global/PlanPruebas/spec.md`.

---

## 2026-08-23 — C1: los secretos de despliegue no tenían guarda, solo buenas intenciones

**Causa.** Cada credencial de `config/settings.py` se lee con `os.environ.get(VAR, default)` y
el default es cómodo para desarrollo. Si un despliegue olvidaba exportar la variable, el sistema
**arrancaba igual**: `DJANGO_SECRET_KEY` con `django-insecure-dev-only-change-in-production`
(cualquiera con acceso al repositorio podía firmar sesiones válidas) y `CLICKHOUSE_PASSWORD`
con `tactico`, la misma contraseña que aparece en el `docker-compose`. No fallaba nada — quedaba
abierto en silencio, que es la peor forma de fallar. `DJANGO_DEBUG`, además, tiene default
`true`: un despliegue sin la variable devuelve el traceback completo con settings y fragmentos
de entorno al navegador en cada excepción.

La guarda ya existía, pero solo para los dos secretos de la demo interactiva
(`apps/ventas_crm/demo_tokens.py:34`). El patrón era bueno; el alcance, no.

**Efecto verificado.** Con `DJANGO_DEBUG=false TSI_ENV=production`, `manage.py check` ahora
aborta enumerando los cuatro secretos sin configurar en un solo mensaje. Con la configuración
local de siempre sigue arrancando sin cambios (`System check identified no issues`). Se comprobó
que la prueba detecta la ausencia de guarda: retirando `CLICKHOUSE_PASSWORD` del registro,
`test_registro_cubre_todos_los_defaults_sensibles_de_settings` falla nombrándolo.

**Archivos tocados.**

- `backend/core/config/secretos.py` *(nuevo)* — registro central `DEFAULTS_INSEGUROS` y las
  guardas `verifica_secretos`, `verifica_debug`, `verifica_hosts`.
- `backend/config/settings.py` — invocación de las tres guardas al final, con los valores ya
  resueltos.
- `backend/tests/test_configuracion_segura.py` *(nuevo)* — 20 pruebas parametrizadas sobre el
  registro, más la prueba antienvejecimiento que analiza `settings.py` y falla si aparece un
  secreto con default sin dar de alta.
- `.gitignore` — `backend/config/keys/` no estaba ignorado (aunque tampoco llegó a versionarse):
  un `git add -A` habría commiteado `jwt_private.pem`, la clave que firma los tokens de sesión.

**Decisión de diseño.** Se conservó el default `true` de `DJANGO_DEBUG` en vez de invertirlo a
`false`. Invertirlo protege solo al despliegue que ya olvidó configurar su entorno, y a cambio
rompe todo arranque local sin `.env`. La guarda por `TSI_ENV` cubre el mismo riesgo sin volver
hostil el desarrollo.

**Trazabilidad.** `PG-CFG-001`, `PG-CFG-002` (✅ Cubierta), `PG-CFG-003` (⚠️ Parcial — falta la
mitad de CORS) y `PG-CFG-005` (parcial) de `specs/Global/PlanPruebas/spec.md` §3.

---

## 2026-08-22 — Tres módulos tácticos de frontend que no tenían spec

Red Operativa, Suscripciones y Facturación, y Ventas y CRM tenían la capa de frontend de
sus informes simples **construida y en uso**, pero sin la carpeta `frontend/` con `spec.md`
y `tasks.md` que sí tienen Emergencias, Soporte, Cuentas y Partners. Nada obligaba a que la
regla de acceso, las exclusiones de dato y los porqués de cada etiqueta estuvieran escritos
en alguna parte, y no lo estaban.

Se redactan las tres, marcadas **`Status: Implemented`** y con las tareas en `[X]`. Son
retro-specs: documentan comportamiento ya construido y verificado durante el repaso click a
click de la capa táctica, no trabajo por hacer. La nota está en la cabecera de cada
`tasks.md` para que nadie las lea como un plan.

Lo que quedó fijado por escrito y antes solo vivía en el código:

- **Red Operativa** — la autoridad está partida en **tres** por materia, y un Proveedor
  entra a `flota` pero **no** a `regiones`: una región no pertenece a ninguna empresa de
  flota. También que `dado_de_alta` no es disponibilidad, y que `estado_geografico` y
  `estado_region` son dos cosas con el mismo sustantivo.
- **Suscripciones** — la separación **finanzas / catálogo** es de materia, no de alcance:
  Estrategia no ve facturas y Finanzas no ve el catálogo de planes. Y la exclusión que más
  importa de toda la capa: **ningún listado publica identificador de pago**, ni siquiera al
  Director Financiero.
- **Ventas y CRM** — `reasignaciones` es supervisión pura y por eso no tiene roles
  acotados: quien está dentro de un movimiento de cartera es parte interesada. Queda escrito
  además que `ejecutivo_anterior` vacío es el **dato correcto** —primeras asignaciones—,
  porque durante el repaso se tomó por un fallo de carga y se descartó.

Las tres declaraban lo que **solo se había verificado en contrato** por falta de datos
sembrados. Eso ya no aplica: ver la entrada siguiente.

**Sin cambios de código.** Esta entrada es documental.

---

## 2026-08-23 — Los 5 fallos que llamé «previos» tres veces, y el embudo que seguía mintiendo

### Los 5 de `test_pinot_client_limit` no eran ambientales

Los di por previos tres veces —y lo eran, en el sentido de que no los causé yo—
pero **eran un defecto real y arreglable**, no ruido. La causa:

`apps/*/tests/performance/test_informes_latencia.py` capturaba
`original = PinotClient.query` **mientras `mock_pinot` estaba activo**, es decir
capturaba el mock, y lo instalaba con `monkeypatch.setattr`. Al deshacerse,
`monkeypatch` reinstalaba **ese mock**. Si su teardown corría después del de
`mock_pinot` —el orden depende de por qué fixture llega cada uno—,
`PinotClient.query` quedaba con el mock puesto **para el resto de la sesión**, y
las pruebas que verifican que el cliente añade `LIMIT` dejaban de ver ninguna
petición HTTP.

Por eso fallaban solo junto a `accidentes`, `partners` y `soporte_cliente`, y
solo a veces. Sustituido por `with patch.object(...)`, que sale al terminar el
cuerpo de la prueba, antes que cualquier fixture. **Ya no se deselecciona nada.**

### El embudo de abandono seguía dando 100 %

Declarar las etapas pendientes no bastaba: `ot04_embudo_abandono` contaba
**llegadas** por etapa y encadenaba cada una con la anterior. Con las pendientes
cargadas, un cliente que llegó y no hizo nada contaba como que superó las tres.

La consulta pasa a medir **dentro de la etapa** —`superaron / llegaron`, usando
`completada`— en vez de comparar con el paso previo. La cadena solo era correcta
mientras toda llegada implicara una superación, que era justo lo que este cambio
dejó de ser cierto.

Medido con una cuenta aprobada por la vía real y sin completar nada: **75 % de
superación y 1 detenido en cada etapa**, donde antes salía 100 % y cero.

### El contador de identificadores era 60 veces más lento de lo necesario

`test_escrituras_sostenidas_por_segundo` falló en la suite completa. Podía ser
carga de la máquina —aislado daba 174/s contra un umbral de 50— pero **medirlo
en vez de suponerlo** destapó un coste real que yo había introducido: abrir la
conexión, el `PRAGMA` y el `CREATE TABLE IF NOT EXISTS` **en cada reserva**
costaban **2,4 ms por identificador**, 409 ids/s.

Reutilizando la conexión: **0,04 ms**, 24 946 ids/s. Sesenta veces mejor, con la
misma garantía. La conexión se suelta si queda inservible, para no arrastrar un
error para siempre.

> **Lección.** «Pasa aislado, luego es del entorno» es una conclusión cómoda y
> fue falsa dos veces hoy: una escondía un parche que no se deshacía, la otra un
> coste que yo mismo había metido.

---

## 2026-08-23 — Los cuatro que quedaban abiertos: si la acción existe, el instante se puede sellar

La observación que desbloqueó tres de los cuatro fue del usuario: **«cuando se
desactiva una región, ¿no sería el caso?»**. Sí lo era. Yo había concluido que el
sistema «no registra» esas fechas; lo cierto es que **las acciones existían y
nadie sellaba el instante**. Es el mismo patrón que ya se había aplicado a la
suspensión de suscripciones.

### `casos-activos-al-despublicar` — resuelto

El informe exige `inicio_es_real = 1`, y `versionado.decidir_version` solo lo
concede si **quien llama aporta el instante**. `dim_region` no lo aportaba porque
el origen guardaba el estado presente y lo sobrescribía.

`Dim_RegionOperativa` gana `fechaestadoregion`, y **el repositorio la sella al
cambiar `estadoregion`** — no los servicios: hay dos que despublican
(`despublicacion_automatica_service` y `reevaluacion_region_service`) y el que se
añada mañana lo hereda sin acordarse. Solo cuando el estado cambia de verdad:
reescribirla en cada actualización convertiría «desde cuándo está despublicada»
en «cuándo se tocó por última vez».

Verificado de punta a punta despublicando por la vía real: la versión nueva abre
con `inicio_es_real = 1` y el informe devuelve **1 fila, 4 casos activos, 3
graves**, con la fecha real.

### #45 — el abandono de onboarding, resuelto sin inventar umbrales

El bloqueo declarado era «hay que decidir qué cuenta como abandono: ¿inactividad
de N días?». **No hacía falta decidir eso.** `Fact_Onboarding` ya tenía la
columna `completado` y nadie escribía nunca `False`: las etapas que nadie hacía
sencillamente no existían, y por eso el embudo daba 100 %.

Al aprobar la cuenta —que es cuando el onboarding arranca— se declaran las tres
obligatorias con `completado = False`. A partir de ahí **una etapa que sigue en
`False` es el abandono observado**. Sin umbral, sin inferencia.

`hecho_onboarding` cambia de grano —de «etapa completada» a «etapa del
onboarding»— y gana `completada`, con su migración: `CREATE TABLE IF NOT EXISTS`
no añade columnas a una tabla que ya existe. `dias_desde_alta` queda **ausente**
en las no completadas: no hay días hasta algo que no ocurrió.

### #46 — la versión, ahora sí declarable por el partner

Se añade la cabecera `X-TSI-API-Version`. **Solo lo declarado por el partner
llega con `version_es_derivada = 0`**; lo leído del path se sigue guardando —así
la fila conserva la versión que era cierta cuando ocurrió— pero marcado como
derivado, porque lo es.

⚠️ Esto **corrige un juicio mío anterior**: había puesto `0` a todo lo guardado,
incluida la versión sacada del path. Guardarla antes no la convierte en un hecho
declarado, y la distinción es justo lo que el indicador de adopción necesita.

### `idsession` — cerrado también para varios procesos

La marca en memoria no cubría el multiproceso. El reparto pasa a un SQLite
propio con `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`: **reservar y leer
son la misma operación**, así que dos workers no pueden recibir el mismo número.

⛔ **No es la base de datos del dominio.** Es un fichero de contadores, se puede
borrar sin perder nada de negocio y al arrancar se resiembra desde el `MAX()` de
Pinot. Si SQLite falla, se cae al reparto en memoria: un contador indisponible
no puede dejar al sistema sin poder crear nada.

### Otra prueba que pasaba por accidente

`test_ot13_retirada` daba «0 despublicaciones medidas» **porque ninguna región
tenía `inicio_es_real = 1`** — la condición que este cambio elimina. Al sellarse
la primera, el contador subió a 1 sin que nada se hubiera roto. Base propia, como
`test_ot17_antiguedad` la semana pasada. Es la tercera prueba de esta serie que
se apoyaba en un defecto para pasar.

**Pruebas:** `pytest apps tests` 4 350 · `ng test` 1 408.

---

## 2026-08-23 — Los tres pendientes de fondo: identificadores, reactivación y las decisiones de agosto

### 1. `idsession` derivado de `MAX()` — y con él, otros 46 sitios

Cuarenta y siete repositorios calculaban su identificador siguiente con
`SELECT MAX(id) + 1` sobre tablas **upsert**. Pinot ingiere de forma asíncrona
**siempre**, así que todo lo creado en esa ventana recibía el mismo id y se
sobrescribía. El 2026-08-23 **34 inicios de sesión recibieron el id 985**: el
login devolvía `200` y la petición siguiente `401`.

`core/pinot/secuencia.py` mantiene en el proceso la marca más alta entregada por
tabla y devuelve `max(MAX_en_pinot, ultimo_entregado) + 1`. Se sigue leyendo
Pinot para que un proceso recién arrancado continúe donde quedó el anterior; lo
que se añade es que **dentro del proceso la secuencia no retrocede**. Un fallo de
lectura no interrumpe la escritura: devuelve 0 y manda la marca en memoria.

⚠️ **No resuelve el caso multiproceso.** Con varios workers cada uno llevaría su
cuenta. Hoy el backend corre como un solo proceso (`runserver`), así que la
garantía es real; con gunicorn multi-worker deja de serlo. La solución completa
—contador durable, o UUID como ya usa `Fact_Factura`— es decisión de
arquitectura y sigue anotada.

Se añadió `reset_secuencia_ids` autouse en `conftest`: la marca vive en el módulo
y sin limpiarla una prueba que crea tres sesiones deja a la siguiente empezando
en 4. **Nueve pruebas** nuevas, incluida la de 50 hilos simultáneos.

### 2. La reactivación de suscripciones ya se puede contar

`hecho_suscripcion` publicaba `fecha_suspension` y `fecha_reactivacion`
**fijadas a `None` en código**: no había de dónde sacarlas. Ahora
`Fact_Suscripcion` tiene `fechasuspension` y `fechareactivacion`, y
`mora_suscripcion_service` las sella en los dos puntos de transición que ya
existían — al suspender por factura fallida y al regularizar.

Medido: el informe pasa de `reactivadas: 0` estructural a **`reactivadas: 1`**,
y la ventana de agosto distingue correctamente la reactivación (11-ago) de la
suspensión (29-jul).

### 3. Las tres decisiones de agosto

**#44 — cinco defectos del origen de Suscripciones.** Tres se atajan ahora en
`update()`, el único punto por el que pasa todo cambio de estado: el motivo de
cancelación se borra si el estado no es `Cancelada`, la vigencia invertida se
rechaza **cuando el cambio toca las fechas** —una fila histórica ya invertida no
puede bloquear una suspensión: el origen sigue cobrándola— y las tres formas de
«sin motivo» se unifican a ausencia.

⛔ **Los otros dos no son defectos.** `activo = true` en una `Cancelada` es
**RN-017**: la suscripción sigue viva hasta `fecha_fin` porque el cliente usa lo
que pagó, y por eso `estado_derivado` no mira `activo`. Y `idplan_programado = 0`
es el centinela de «sin cambio» que Pinot obliga a usar al no tener NULL.
«Corregir» cualquiera de los dos rompería algo que funciona.

**#45 — cobertura de pertenencia al 9,5 %.** El autorregistro creaba la cuenta y
su administrador local **sin escribir el vínculo**: la pertenencia se resolvía
solo por el respaldo `admin_local_id`, y de ahí los 2 vínculos para 21 usuarios.
`autorregistro_proveedor_service` ahora vincula. El respaldo se conserva para las
cuentas anteriores.

**#46 — el log de API no registra la versión.** `Fact_LogLlamadaAPI` gana
`version_contrato`, que el middleware resuelve **en el instante de la llamada**.
El cargador la prefiere y marca `version_es_derivada = 0` en esas filas; las
anteriores se siguen deduciendo del path con la marca en 1.

⚠️ **Esto no convierte la versión en un dato declarado por el partner.** Sigue
saliendo del path: para que fuera un hecho haría falta que el partner la pidiera
por cabecera o que la credencial estuviera ligada a una versión, y hoy
`Dim_CredencialAPI` no guarda ninguna de las dos. Lo que sí desaparece es el
riesgo que la decisión señalaba —«el día que el path cambie de forma, la
derivación devolverá otra cosa»—: cada fila conserva la versión que era cierta
cuando ocurrió.

⛔ **La zona sigue fuera, y a propósito.** «Un parámetro mal leído y una consulta
fuera de zona se verían igual, y una de las dos es una acusación de
incumplimiento.» Eso no ha cambiado.

---

## 2026-08-23 — Segundo estado geográfico: arregla la atribución, y destapa que el bloqueo era otro

`database/seed_segundo_estado_geografico.py` siembra un estado —Veracruz— con su
condado, ciudad, dos calles, **una sola región** y cuatro accidentes abiertos.

**Lo que sí arregla.** `dim_geografia` dejaba la región del condado **ausente a
propósito** mientras un estado tuviera varias regiones: elegir una daría «una
cifra que nadie cuestiona porque no parece rota». Con las tres regiones anteriores
compartiendo `idestado = 1`, **ningún condado tenía región**. Ahora
`Boca del Río → Costa Oriente` es inequívoco, y se nota:
`cobertura-flota-por-region` nombra una región real en vez de solo «Sin región
asignada», y `condados-cobertura-critica` ve el condado nuevo.

Va en **dos fases** porque la despublicación es un cambio observado: la región
nace en `Producción`, se carga, se despublica y se vuelve a cargar. Sembrarla
despublicada de golpe no habría abierto una segunda versión.

### ⛔ Y aun así `casos-activos-al-despublicar` sigue vacío

**Mi diagnóstico anterior estaba mal.** Dije que el bloqueo era el estado
geográfico único; era necesario arreglarlo, pero no era el bloqueo.

El informe filtra `WHERE despublicada_en IS NOT NULL`, y esa fecha solo existe si
la versión de la región lleva **`inicio_es_real = 1`** — la marca que distingue
«se sabe cuándo ocurrió el cambio» de «es desde que empezamos a mirar».
`versionado.decidir_version` exige que **quien llama aporte el instante**, y ese
instante solo puede salir de una tabla de historial del origen.

`dim_region.construir` no lo aporta, y **no puede**: nada historiza cuándo se
despublicó una región. `Dim_ValidacionRegion` guarda `Aprobada`/`Rechazada` —el
resultado de validar, no una despublicación— y `Dim_RegionOperativaEstadoRegion`
es una tabla de enlace que se sobrescribe, no un historial. Comprobado: **las 8
filas de `dim_region` llevan `inicio_es_real = 0`**, y siempre lo llevarán.

Es la misma clase que la reactivación de suscripciones: **el informe pide un dato
que el sistema no registra**. Y como con `roles-incompatibles`, la salida no es
técnica — o el origen empieza a historizar el estado de la región, o el informe
se retira. Anotado en `decisiones-pendientes.md`.

⚠️ **Relajar el filtro sería la salida equivocada.** Sin `inicio_es_real`,
`despublicada_en` diría «desde que empezamos a mirar» y el informe presentaría esa
fecha como el día de la despublicación. La marca existe precisamente para impedir
eso.

`pytest dags` → 1 134 passed, 74 skipped.

---

## 2026-08-23 — Cierre de la capa táctica: de 88 a 92 informes con datos

Los 6 informes compuestos que seguían vacíos tenían **cuatro causas distintas**, y
solo una era «no hay caso». Corregido lo que era corregible; queda uno.

### `fecha_inicio_contrato` no se escribía nunca *(3 pantallas)*

Las 8 cuentas reales tenían el centinela, así que `dim_cliente.fecha_alta` y
`cohorte_alta` salían nulas y **antigüedad media, churn por cohorte y tasa de
aprobación** no podían devolver nada. El cargador estaba bien; el campo no se
escribía por la única vía de alta viva —`CU-O01` está retirado— porque
`autorregistro_proveedor_service` lo pasa como opcional y nadie lo manda.

**Decisión del usuario: la fecha de inicio es la aprobación.** Se sella en
`aprobacion_proveedor_service` al aprobar, y no al completar el onboarding: la
relación contractual nace con la aprobación, y el onboarding es la puesta en
marcha de una cuenta que **ya** es cliente y puede quedarse a medias sin deshacer
el contrato. El rechazo no sella nada — hay prueba de ambas cosas.

`update_estado` acepta ahora la fecha y **nunca pisa un valor previo con `None`**:
una reactivación no debe reescribir la fecha del contrato original.

**Relleno de las cuentas anteriores** (`database/migra_fecha_inicio_contrato.py`).
No existe ninguna fecha de aprobación guardada —`fecha_creacion` también es
centinela en todas—, así que se usa **el inicio de la primera suscripción**: la
primera evidencia de que la cuenta operaba comercialmente. ⚠️ Es un sustituto, y
la antigüedad saldrá **por defecto, nunca por exceso**; se prefiere eso a inventar
`today()`, que daría antigüedad cero a cuentas de dos años. Las cuentas **sin
suscripción no reciben fecha**: una rechazada nunca empezó un contrato, y ponerle
uno la metería en la antigüedad media como si fuera cliente. 6 rellenadas, 1
dejada (`Ambulancias del Pacífico`, rechazada-anulada).

### `roles-incompatibles`: retirado

**Decisión del usuario: sobra.** Recibía los pares de roles incompatibles por
parámetro y **ninguna pantalla los enviaba** —hay hasta una prueba que afirmaba
que iba nulo—, así que su consulta devolvía cero filas **por construcción,
siempre**. Retirado de punta a punta: consulta SQL, mapa del servicio, parámetro
de la vista, catálogo del frontend, la zona de la pantalla y sus pruebas.

La zona de **lectura** pasa a ser opcional: Acceso se quedó sin ella, y repetir
`concurrencia-sesiones` por cuarta vez sería relleno, no información. Pedirlo
ahora responde `403`, igual que cualquier informe inexistente.

⚠️ La prueba de que «ningún informe de Cuentas publica `idusuario`» tenía a
`ot18_roles_incompatibles` como **única excepción**. Al retirarse, la excepción
desaparece y la regla queda sin agujeros.

### `suspension-reactivacion`: sembrada la suspensión, la reactivación no se deriva

`hecho_suscripcion` solo tenía `vigente` y `cancelada`. Se sembró una suscripción
`Suspendida` —fila **nueva**, no el cambio de estado de una viva: suspender una
existente la sacaría del MRR y de la cartera, y un seed no debe mover cifras de
negocio para llenar una pantalla—. Ya devuelve fila.

⚠️ **`reactivadas` seguirá en cero, y no por falta de datos**:
`hecho_suscripcion` fija `fecha_suspension` y `fecha_reactivacion` a `None` sin
derivarlas de nada, y no hay de dónde — `Fact_Suscripcion` es una foto del estado
actual y no existe historial de suspensiones. Anotado como decisión pendiente.

### `casos-activos-al-despublicar`: sigue vacío, y por diseño

`dim_geografia` deja la región del condado **ausente a propósito** cuando el
estado tiene más de una región: hoy todas comparten `idestado = 1`, y atribuirlas
a una sola daría «una cifra que nadie cuestiona porque no parece rota». Con un
solo estado geográfico en el sistema, ningún accidente puede atribuirse a la
región despublicada. **No es un defecto** y no se arregla sembrando más regiones:
haría falta un segundo estado con su condado, que es fabricar geografía y no lo
hago sin decirlo.

### Resultado

**92 de 93 informes compuestos devuelven datos** (eran 88 de 94; uno se retiró).

`pytest apps` → 4 316 passed, 6 skipped. `ng test` → 1 408 SUCCESS.

> **Una prueba que pasaba por accidente.** `test_ot17_antiguedad` sembraba su
> cliente y medía la mediana, pero `limpiar_cuentas()` **no vacía
> `dim_cliente`**: convivía con las cuentas reales y pasaba solo porque ninguna
> tenía `fecha_alta`. Al rellenarlas, una `aseguradora` real entró en la mediana
> y la bajó de 234 a 14 días sin que nada se hubiera roto. Se le dio **base
> propia**, el patrón que ya usan otras cinco pruebas del modelo.

---

## 2026-08-23 — Las cuatro pantallas secas de Ventas: sembrada la nutrición del prospecto

`Fact_Interaccion_Demo` y `Fact_NotificacionVentas` estaban **a cero en Pinot** —no
solo en el modelo analítico: nadie había escrito nunca en ellas—, así que
`hecho_interaccion_demo` y `hecho_notificacion_ventas` salían vacíos y cuatro
pantallas de gestión no tenían nada que pintar: `intensidad-demo`,
`secciones-visitadas`, `reglas-disparo` y `latencia-reaccion`.

`database/seed_nutricion_ventas.py` siembra 21 interacciones en 5 sesiones de demo y
5 avisos al ejecutivo. Idempotente.

**El vocabulario no se inventa.** `tipo_evento` sale de
`ingesta_interaccion_demo_service.TIPOS`, las reglas y sus canales de
`reglas_demo_catalog`, y `precios` es la sección que dispara ambas. Sembrar valores
que el sistema no produce convierte el fixture en una afirmación sobre datos que
nadie escribe — es el error del `"09:30"` de `hora_fin`.

**El aviso ignorado importa más que el atendido.** El cargador deriva la reacción
como el primer avance de etapa posterior al aviso, y si no hay ninguno deja
`segundos_a_reaccion` **ausente** con `hubo_avance = 0`: contarlo como latencia cero
haría que los avisos que nadie atendió *mejoraran* el indicador. Se sembraron las dos
caras —3 atendidos, 2 ignorados— porque sin ignorados esa regla no se ejerce. Los
avisos se anclan a las **transiciones reales** de cada prospecto, no a fechas
inventadas, para que la latencia sembrada sea exactamente la que sale.

⚠️ **Ninguna interacción va sin sección.** La consulta tiene un `ifNull(nullIf(...))`
defensivo, pero la ingesta **exige** sección y hasta el inicio de sesión escribe
`'demo'`: una fila sin sección no puede existir. Dejar esa rama sin ejercitar es
honesto; fabricarla sería inventar un caso imposible.

**Resultado, medido contra la API y en pantalla:**

| Pantalla | Resultado |
|---|---|
| `intensidad-demo` | 5 empresas con 8 / 5 / 4 / 3 / 1 eventos y 4 / 3 / 3 / 2 / 1 secciones |
| `secciones-visitadas` | demo 9, precios 6, cobertura 4, integraciones 2 |
| `reglas-disparo` | dos reglas con **tasas distintas**: 0.6667 y 0.5 |
| `latencia-reaccion` | 5 avisos, 3 con reacción, **2 sin**, mediana 3 600 s → «1.0 h» |

### Dos defectos que solo se vieron con datos delante

**`reglas-disparo` calculaba la tasa de acierto y no llegaba a ninguna pantalla.** El
plegable de apoyo mostraba «2 reglas disparadas» y nada más — el número menos
interesante, cuando la pregunta es *cuál funciona*. Se añadió el desglose por regla
siguiendo el patrón que ya usaba `carga-por-ejecutivo` en el mismo componente. Con la
fuente vacía el hueco era invisible.

**«1 eventos · 1 secciones».** Singular sin resolver en la intensidad por empresa,
visible en cuanto hubo un prospecto con un solo evento. Corregido.

`ng test` → 1 408 SUCCESS.

> **Nota de proceso.** Al añadir el desglose rompí el build dos veces: primero metí
> **backticks** dentro de un template literal de TypeScript, y luego usé el pipe
> `number` en un componente que no lo importa. Las dos las cazó `ng test` antes de
> tocar el navegador.

### El entorno, que costó más que el cambio

**El build del frontend fallaba en silencio.** `docker compose build` moría con
`rpc error: EOF` durante `ng build`: 8 GB de RAM para 13 contenedores no dan para la
compilación de producción de Angular. Peor, **yo mismo lo oculté**: filtré la salida
con `| grep | tail`, así que el `exit 0` que leía era el del `tail` y no el del build.
Dos «reconstrucciones» seguidas no reconstruyeron nada y el contenedor siguió sirviendo
el bundle de las 02:33. Se resolvió parando Airflow durante la compilación.

**Pinot volvió a detener la ingesta, esta vez en las 79 tablas.** Y con un efecto que
la primera vez no se vio: `Fact_Session` quedó congelada, y como `SessionRepository`
calcula el id nuevo con `MAX(idsession) + 1` **leyendo de Pinot**, cada login reutilizaba
el id `985` y se pisaba a sí mismo. El login devolvía `200` y el token siguiente daba
`401`. `resumeConsumption` no bastó: el servidor tenía el consumidor en `NOT_CONSUMING`
con 34 registros de retraso y el segmento nuevo **sin asignar**. Hizo falta reiniciar
`pinot-server`; entonces recuperó de 984 a 1 115 sesiones de golpe.

> ⚠️ **`idsession` derivado de `MAX()` sobre Pinot es frágil** y no es cosa de este
> cambio: cualquier retraso de ingesta hace que dos sesiones compartan id en una tabla
> upsert, y la segunda borra a la primera. Anotado en `decisiones-pendientes.md`.

---

## 2026-08-22 — «Cambio programado» pintaba `[object Object]`: aplanado en el backend

El listado `suscripciones` devolvía `cambio_programado: {plan, se_aplica_el}`, un objeto
anidado, y la celda lo pintaba literalmente **`[object Object]`**: el catálogo de columnas
del frontend declara campos escalares y la tabla no recorre objetos.

**Aplanado en el backend**, que es la opción elegida entre las dos que había. Pasa a
`cambio_programado_plan` y `cambio_programado_se_aplica_el`, dos escalares que viajan
**siempre**, ambos `null` cuando no hay cambio — así el consumidor no tiene que distinguir
«no hay cambio» de «este listado no responde eso». La alternativa, dar al catálogo un
`render` por columna, habría metido lógica de presentación en las definiciones de los 32
listados para resolver un caso.

**La fecha no es decorado.** Una reducción aprobada **no se aplica al aprobarse** sino al
cerrar el período ya pagado. Sin ella la tabla diría que hay un cambio pendiente sin decir
cuándo, que es la mitad de la respuesta.

Actualizados a la vez el contrato OpenAPI, el `data-model.md` y el `quickstart.md`, más las
dos columnas del frontend. Se añadió una prueba de que **el objeto anidado no vuelve**
(`test_el_cambio_programado_no_viaja_anidado`), y `cambio_programado` salió de la lista de
campos condicionales de la prueba de conformidad: los dos nuevos son obligatorios y siempre
presentes, así que la comprobación queda **más estricta** que antes.

**Verificación.** `pytest apps` → 4 317 passed, 6 skipped. `ng test` → 1 408 SUCCESS. En
pantalla, con `DirectorEstrategia`: «Básico» y «31/10/2026» en dos columnas; las demás filas,
`—` y `—`.

### ⚠️ Pinot dejó de consumir de Kafka a mitad de la verificación

Al recrear el contenedor del frontend se comprobó que **los seis casos de borde sembrados
habían desaparecido**: `Dim_Cliente` de vuelta a 7 filas, cero demos, cero regiones nuevas.
No fue un fallo del seed —es idempotente y se reejecutó— sino que **las tablas en tiempo real
se quedaron sin ningún segmento consumiendo** tras los reinicios de `pinot-server` de esta
jornada. `pauseStatus` devolvía `pauseFlag: false` con `consumingSegments: []`: ni pausada ni
consumiendo, y publicar en Kafka no daba error.

Se restableció con `POST /tables/{tabla}/resumeConsumption` en las seis tablas, y el seed
volvió a ingerir. Anotado como trampa del entorno: **una ingesta detenida no se anuncia**, se
parece exactamente a un seed que no funcionó.

---

## 2026-08-22 — Los 58 fallos de la suite de frontend: ninguno era un defecto del producto

La suite estaba en **58 FAILED / 1348 SUCCESS**. Los 58 codificaban el comportamiento
**anterior** a los cambios de esta misma jornada: son pruebas que se quedaron atrás, no
funciones rotas. Se arreglaron por familias, y en cada una se conservó lo que la prueba
vigilaba en vez de reescribir la aserción para que pasara.

| Familia | Nº | Qué pasaba |
|---|---|---|
| `http.verify()` con una petición de catálogos pendiente | **37** | Al convertir los filtros de id en comboboxes, las páginas piden además sus opciones. Ninguna prueba la atendía |
| Guards de gestión con `Administrador` | 6 | Escritas a `toBeFalse()` **sin ejecutarlas**: el guard devuelve un `UrlTree`, no `false` |
| Cableado de sidebars | 8 | `Administrador` salió de la gestión, Cuentas ganó su director táctico, y los 3 workpanels de Emergencias se retiraron |
| Definiciones de `casos` | 2 | `situacion` sustituyó a la columna «Activo» |
| Enumeraciones de Soporte | 3 | Ahora se humanizan al pintarlas; dos eran además desfase de índices de columna |
| Estados de región | 1 | Miraba solo la etiqueta, que ahora se humaniza |
| «Agente 3» en la Pantalla Z | 1 | El servicio ya resuelve el nombre del agente |

**La familia grande era un hueco del arnés, no de las pruebas.** Emergencias ya lo había
resuelto —atiende las peticiones de catálogos en su `montar`— y las otras cuatro páginas no.
Se copió su solución tal cual, sin tocar ni una aserción: los 37 fallos desaparecen y lo que
cada prueba comprueba sigue siendo lo mismo.

**Seis pruebas de guard se habían editado sin ejecutarse.** Al quitar `Administrador` de la
gestión alguien cambió `toBeTrue()` por `toBeFalse()`, pero el guard **redirige**: devuelve
un `UrlTree` a `access-denied`. Ahora afirman eso, que es más fuerte que `false` — comprueba
además *a dónde* manda. Y dos de ellas asertaban dos veces la misma variable, así que el
segundo guard no se comprobaba; corregido.

**Tres pruebas cambiaron de sentido en vez de borrarse**, porque lo que vigilaban sigue
mereciendo vigilancia:

- La de los workpanels de Emergencias comprobaba que los tres conservaran sus roles. Los tres
  se retiraron, así que ahora comprueba que **no vuelvan** al sidebar.
- La de `casos` afirmaba que **no** llevaba `situacion`. Ahora afirma que la lleva, que
  `activo` **no** está —era la columna que causaba la ambigüedad— y que la pantalla no la
  deriva. Se añadió una tercera para el formato.
- La de la Pantalla Z afirmaba que la fila decía «Agente 3» y **no** un nombre, que era
  exactamente el defecto. Ahora afirma el nombre, y una prueba nueva cubre el respaldo
  `Agente #3` para el identificador que no resuelve, que es una anomalía y debe verse como tal.

La de los estados de región miraba solo la etiqueta del `<option>` y por eso exigía el
literal crudo `En_Alerta` en pantalla. Ahora comprueba **las dos caras**: se lee «En Alerta»
y viaja `En_Alerta`. Pueden romperse por separado.

**Resultado: `ng test` → 1 408 SUCCESS, cero fallos.** Dos pruebas más que antes.

> **Lección.** Los 58 llevaban toda la jornada ahí y se dieron por «previos» tres veces
> seguidas. Ninguno lo era en el sentido útil de la palabra: todos los produjo trabajo de
> esta misma sesión, y seis los produjo editar aserciones sin ejecutarlas.

---

## 2026-08-22 — El catálogo de columnas gana un tipo `moneda`

`FormatoColumna` tenía `numero` y nada más para los importes, así que la columna de
facturas mezclaba **`49`, `63.5` y `166.88`** en filas contiguas: los decimales caían donde
caía cada valor y una columna de dinero dejaba de compararse leyendo hacia abajo.

Rellenar dentro de `numero` no era opción —dejaría «4 unidades» como `4.00`—, así que la
distinción tiene que declararla **el catálogo de columnas**, que es el único sitio que sabe
si un número es dinero.

**`moneda`**: dos decimales exactos, vía `DecimalPipe` con `'1.2-2'`. Aplicado a las cinco
columnas de dinero que existen en los 32 listados: `precio`, `monto_base`, `impuestos`,
`monto_total` (Suscripciones) y `valor_estimado` (Ventas). Las cinco ya estaban alineadas a
la derecha, así que la alineación no se toca.

⛔ **Sin símbolo de divisa, y no es un olvido.** El sistema no almacena moneda en ninguna
tabla. Un `$` aquí lo inventaría el frontend. Hay una prueba que lo afirma —la celda no
puede contener `$`, `€`, `£` ni `¤`— para que el día que alguien lo añada tenga que
justificarlo. Cuando el backend publique la divisa, `moneda` es el sitio donde ponerla.

**Verificación.** 5 pruebas nuevas (entero, un decimal, dos decimales, ausencia y ausencia
de divisa) y las 74 de `shared/informes` en verde. En el navegador, con
`DirectorFinanciero` y `DirectorEstrategia`: `49.00`, `63.50`, `166.88`, `149.00`, `0.00`, y
`15,000.00` / `99,000.00` en Ventas. `dias_mora` y `reintentos` siguen siendo `13` y `4`:
solo se rellenan las columnas declaradas como dinero.

⚠️ **La suite de frontend tiene 58 fallos, y son previos a este cambio.** Medido revirtiendo
solo las cinco columnas: **58 FAILED / 1348 SUCCESS con y sin ellas**, idéntico. Son de la
capa de gestión —guards de administrador, cableado de sidebars, páginas de Partners,
Soporte, Cuentas y Red Operativa— y corresponden al cambio de «el administrador solo opera»
de esta misma jornada, cuyas pruebas de frontend no se actualizaron. **Está pendiente**;
darlo por verde sería falso.

**Un defecto encontrado de paso, no corregido.** En `suscripciones`, la columna «Cambio
programado» pinta **`[object Object]`**: el backend devuelve `{plan, se_aplica_el}` y la
columna no declara formato, así que cae en `String(valor)`. Arreglarlo tiene dos formas
legítimas —aplanarlo a dos campos en el contrato, o dar al catálogo un `render` por
columna— y esa elección es del contrato, no una corrección. Anotado para decidir.

---

## 2026-08-22 — Los seis casos de borde que la capa táctica afirmaba sin poder enseñar

`database/seed_casos_borde_informes.py`. Seis comportamientos estaban descritos en la
spec y cubiertos por prueba unitaria, y en el navegador no había **ni una fila** que los
ejerciera. Una regla que nadie ha visto fallar es una regla que nadie ha visto.

| Caso | Lo que ahora se puede ver |
|---|---|
| Región `Despublicada`, `En_Alerta` y `Rechazada` | Los cinco estados conviven; `En_Alerta` **opera degradada** y no se agrupa con `Despublicada` |
| Dos validaciones sobre la región rechazada | El historial completo (FR-005): el segundo intento **no sustituye** al primero |
| Unidad sin condado | Condado y estado geográfico **ausentes**, y la fila **no se omite** |
| Factura `En disputa` vencida hace 40 días | Sale **sin `dias_mora`**, junto a una `Pendiente` vencida que sí trae 13 |
| Cuenta `Dado de baja` | La baja es lógica: la fila **sobrevive** con su razón social |
| Tres demos activas | Los **tres formatos** de expiración que el parser tolera, ordenadas a 3, 9 y 21 días |

**Dos cuidados que condicionaron cómo está escrito el seed**, y que importan más que los
datos en sí:

1. **La unidad sin condado nace `activo = false`.** `list_candidatas_por_condado` filtra
   `activo = true`, así que de baja no puede entrar al despacho **por garantía**. Sembrada
   activa quedaría fuera solo porque su `idcondado = 0` no cae en ningún condado — cierto
   hoy, y dependiente de un detalle de la consulta que nadie prometió mantener.
2. **La cuenta dada de baja es una fila nueva, sin personal.** Marcar de baja una cuenta
   existente **impide iniciar sesión a sus usuarios** desde la corrección B9. Un fixture
   para un informe no puede sacar gente del sistema.

**Un defecto del propio seed, corregido antes de darlo por bueno.** Las demos se elegían
entre los prospectos que *no tenían* demo. En la segunda pasada los tres primeros ya la
tenían, elegía otros tres, y cada ejecución sumaba tres demos activas más. Ahora se eligen
**por id**: reejecutar reescribe. Comprobado corriéndolo dos veces — los conteos no se
mueven.

**Verificación contra la API, con el actor de cada departamento y no con Administrador.**
`DirectorExpansion` (flota), `DirectorTecnologico` (regiones y validaciones),
`DirectorFinanciero` (facturas), `DirectorMarketing` (demos) y `Administrador` en
`cuentas-por-estado`, que es suyo por `INFORMES_CUENTAS_ROLES`. Los seis casos salen como
la spec decía. El filtro «Detenida más de 100 días» acota de 5 regiones a 2.

`pytest` sobre los departamentos tocados y sobre despacho, accidentes e informes tácticos:
**2 004 + 821 pasan, 2 saltadas**, ninguna falla. Las tres specs de frontend recién escritas
quedan actualizadas: esos casos ya no dicen «solo en contrato».

**Y luego se miraron las pantallas, que es donde aparecieron dos cosas más.**

**Un defecto del seed que solo se vio pintado.** La cuenta dada de baja se sembró con
`tipo: "Privado"`, copiado de `Dim_Prospecto.tipo_organizacion`. Pero `Dim_Cliente.tipo`
usa **otro vocabulario** —`Corporativo`, `Proveedor`, `Aseguradora`— y el filtro «Tipo»
solo ofrece esos tres. La cuenta salía en el listado y **desaparecía en cuanto alguien
filtraba por cualquier tipo**: presente y a la vez inalcanzable. Corregido a `Corporativo`.
Contra la API la fila se veía perfecta; hizo falta ver el desplegable al lado de la tabla.

**Un requisito que yo mismo había escrito mal.** FR-F09 de la spec de Suscripciones exigía
mostrar los importes «con su moneda». **El sistema no almacena moneda en ninguna tabla**:
`Fact_Factura` no tiene columna, y el único «moneda» del repositorio es una etiqueta de
unidad de la capa estratégica. El requisito se había escrito por analogía en la retro-spec,
sin comprobarlo, y un símbolo en la celda lo habría inventado el frontend. Corregido a
«sin redondear a entero», que sí se cumple.

Queda abierto, en `decisiones-pendientes.md`, que la columna de importes mezcla `49`, `63.5`
y `166.88` sin rellenar decimales. No se cambió sobre la marcha porque el formato numérico
es de la capa compartida y afecta a todas las columnas de los 32 listados: separar «esto es
dinero» de «esto es un conteo» exige un tipo nuevo en el catálogo de columnas, y eso es
diseño de contrato, no una corrección.

> **Lección, otra vez la misma.** La verificación contra la API dio los seis casos por
> buenos. El desplegable que dejaba la fila inalcanzable no está en la respuesta JSON:
> está al lado de la tabla.

---

## 2026-08-18 — Contrato estratégico: el siguiente paso ya no es `/speckit-tasks` de OE5 (D6)

**D6 — §10 del contrato seguía mandando a generar tasks de OE5.** OE5 (y el resto de OE1–OE6)
ya tienen backend HTTP y pantallas Z. El párrafo «siguiente = `/speckit-tasks` de OE5» mentía
el orden de trabajo. Quickstarts de OE3/OE4 decían que `Gerente` no estaba sembrado: el rol
sí está (`ROLES_DEMO` id 23); lo que no se garantiza es una cuenta demo asignada.

Causa: el recuento D5 actualizó «frontend implementado» y dejó el siguiente de producto
viejo. Efecto verificado: §10 ya no apunta a un ciclo Speckit de UI; los quickstarts no
niegan el catálogo del rol.

---

## 2026-08-18 — Frontend estratégico OE1–OE6 ya no está aplazado (D5)

**D5 — Specs que seguían diciendo «frontend aplazado».** El código ya sirve pantallas Z de
OE1–OE6. `contrato-informes-estrategicos.md` §9–§10, specs/planes/quickstarts de backend de los
seis OE, y el recuento de frontend del contrato ahora dicen **implementado** (capa `../frontend/`).
La fila ISO «capacidad de interacción» sigue ⚪ **en la spec de backend** (esa capa no pinta UI).

Causa: las capas de presentación se implementaron y los documentos de backend no se actualizaron.
Efecto verificado: no queda «frontend aplazado» en `specs/001-estrategico/` salvo el asiento
histórico D4 de este changelog.

---

## 2026-08-18 — Capa estratégica: docs al día y backend OE4 (D4)

**D4 — Índices OE1/OE2/OE5 y `acceso-estrategico.md`.** Seguí­an diciendo que el táctico no
existía y que `Gerente` no estaba en código. El sustrato de compuestos **sí está**; `ROL_GERENTE`
y `ROLES_DEMO` id 23 también. `contrato-informes-estrategicos.md` §10 recontado.

**Código OE4.** Nueve GET `/informes-estrategicos/oe4/<informe>`; seis bloqueados 404.
Columnas `distancia_millas` y `condicion_clima` en `hecho_accidente`. Permiso partido:
expediente vs inteligencia vendible. Frontend de OE4 sigue aplazado.

---

## 2026-08-18 — Specs tácticas que mentían el estado (D1, D2, D3)

**D1 — Índices de listados simples.** Seis departamentos (`Cuentas-Clientes`, `Ventas-CRM`,
`Suscripciones-Facturacion`, `Red-Operativa`, `Soporte-Cliente`, `Emergencias`) declaraban
frontend «aplazado deliberadamente» y backend «solo spec». El código ya servía listados
(`backend/apps/*/views/informes_*.py` y `frontend/src/app/modules/*/informes/`). Se actualizaron
los índices `informes-tacticos-simples.md`. Partners ya decía la verdad. Ventas, Suscripciones y
Red Operativa no tienen carpeta Speckit `frontend/`; el índice apunta al módulo Angular.

**D2 — `acceso-tactico.md` §7.** Afirmaba que faltaba crear los seis roles en `Dim_Rol`. Están en
`ROLES_DEMO` (ids 17–22) y en `roles_tacticos.py`. `Gerente` es id 23 (capa estratégica). Analítica
sigue sin módulo táctico.

**D3 — `Status: Draft` en specs ya construidas.** Backend y frontend de `informes-tacticos-simples`
(donde existía spec de capa) y backends de `informes-compuestos-modelo` que el índice ya daba por
hechos (más el frontend de Ventas CRM) pasaron a `Implemented`.

Causa: el código avanzó y los índices no. Efecto verificado: grep de «Aplazado deliberadamente» y
`Status: Draft` en esos árboles queda vacío. No hay cambio de comportamiento.

---

## 2026-08-18 — Catálogo Dim_Rol: Gerente (tablero estratégico)

Alcance: `backend/scripts/_demo_seed_common.py`, `backend/tests/regression/test_credenciales_demo_consistentes.py`,
`.specify/docs/actors.md`.

`Gerente` ya existía en `roles_tacticos.py` y en los permisos de OE1–OE6, pero no tenía fila en
`Dim_Rol`. Sin esa fila ningún usuario podía acumularlo. Se siembra como `idrol` 23. Las seis
autoridades tácticas (17–22) ya estaban; no se toca la decisión de que Cuentas no tenga autoridad
de negocio propia.

---

## 2026-08-18 — Capa frontend de compuestos Cuentas y Clientes (ciclo `/speckit-implement`)

Alcance: `frontend/src/app/modules/cuentas-clientes/gestion/`, `frontend/src/app/app.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts`,
`specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/frontend/`.

Tres pantallas Z (`ciclo`, `incorporacion`, `acceso`). Dos guards: Administrador en ciclo e
incorporación; Director Tecnológico solo en acceso. Ocupación con cobertura, embudo con etapas
en cero, concurrencia por solape, roles vacíos si no hay política. Listados, gestión de cuenta
e incorporación operativa no se tocaron. Rebuild Docker aplazado a petición.

---

## 2026-08-18 — Capa frontend de compuestos Partners y API (ciclo `/speckit-implement`)

Alcance: `frontend/src/app/modules/partners/gestion/`, `frontend/src/app/app.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts`,
`specs/002-tactico/Partners-API/informes-compuestos-modelo/frontend/`.

Sin hallazgo de spec vs. código: tres pantallas Z (`consumo`, `incorporacion`, `entrega`),
guard propio (Director Tecnológico / Admin), trío p95/media/muestras en el mismo bloque,
`meta.nota_muestras` declarado. Listados, consola y portal no se tocaron ni se retiraron.
El Partner y el Desarrollador de APIs no ven los enlaces de gestión.

---

## 2026-08-17 — Capa backend de compuestos Partners y API (ciclo `/speckit-implement`)

Alcance: `specs/002-tactico/Partners-API/informes-compuestos-modelo/backend/`,
`dags/lib/dimensiones/dim_{partner,credencial_api,version_contrato}.py`,
`dags/lib/hechos/{hecho_llamada_api,hecho_cambio_acceso}.py`,
`dags/lib/consultas/partners/` (13 SQL),
`dags/etl/dag_hecho_{llamada_api,cambio_acceso}.py`,
`backend/apps/informes_tacticos/` (permiso, servicio, vistas, envelope).

Los 13 compuestos en alcance de OT08/OT09/OT10. Una sola fuente de consumo (el
detalle); `Fact_APIIntegracion` no se carga. Sin IP, sin hash, sin contacto, sin
ejecutor. p95 al consultar con `muestras` y `percentil_fiable`. Los dos
endpoints ya construidos en `apps/partners` **no se tocan**. La latencia del
modelo diferirá de la de esos endpoints **a propósito** (ellos dan solo media).

Se añadió `hecho_factura.tipo` (columna aditiva) para separar excedente de
ingreso base sin recrear el hecho de Suscripciones.

`informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` no está en este
workspace. El estado queda en
`specs/002-tactico/Partners-API/informes-compuestos-modelo/informes-compuestos-modelo.md`.

---

## 2026-08-17 — Capa backend de compuestos Cuentas y Clientes (ciclo `/speckit-implement`)

Alcance: `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend/`,
`dags/lib/dimensiones/dim_{cliente,usuario_organizacion,etapa_onboarding,rol}.py`,
`dags/lib/hechos/{hecho_sesion,hecho_onboarding}.py`,
`dags/lib/consultas/cuentas/` (9 SQL),
`dags/etl/dag_hecho_{sesion,onboarding}.py`,
`backend/apps/informes_tacticos/` (permiso, servicio, vistas, envelope).

Los 9 compuestos de OT17/OT04/OT18 sobre el modelo. `dim_cliente` queda **ampliada**
(no recreada) por su departamento dueño: seis columnas de cohorte, baja, etapa
derivada, onboarding completo y resultado de solicitud. El embudo parte del
catálogo explícito; la duración de sesión es nula sin cierre; la concurrencia
es solape de intervalos; sin token ni identidad. El Director Tecnológico entra
solo a OT18.

Al crear `hecho_onboarding`, ClickHouse 24.8 rechazó `ORDER BY (..., orden_etapa)` porque
`orden_etapa` es `Nullable`. El `data-model.md` se corrigió a `ORDER BY (fecha, idcliente,
idonboarding)`. No se activó `allow_nullable_key`.

`informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` no está en este
workspace (ruta en `.gitignore`). El estado de los 9 informes queda en
`specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/informes-compuestos-modelo.md`.

---

## 2026-08-17 — Capa frontend de compuestos Soporte al Cliente (ciclo `/speckit-implement`)

Alcance: `frontend/src/app/modules/soporte-cliente/gestion/`, `frontend/src/app/app.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts`,
`specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/frontend/`.

Sin hallazgo de spec vs. código: tres pantallas Z (`cumplimiento`, `cola`, `tendencias`),
guard propio (Gerente / agente / Admin), par cumplimiento/cobertura en el mismo bloque,
`meta.acotado_a` declarado. Listados, cola del agente y dashboard operativo no se tocaron
ni se retiraron.

**F1 (quickstart, 2026-08-17):** la clave del agente en `frontend/quickstart.md` decía
`Demo1234!`; el seed canónico es `password123` (`backend/scripts/_demo_seed_common.py`).
El login real con `lucia.vera.soporte@demo.tsi.com` / `password123` entra. Corregido el
quickstart. No es un defecto de las pantallas Z.

**B1 (ClickHouse, 2026-08-17):** los GET de los 9 compuestos responden 500 porque ClickHouse
devuelve 404 sobre `tsi_tactico` (tablas/SQL del modelo de Soporte). La UI pinta `error` por
zona, no 0 %. No es un fallo de esta capa frontend; hace falta el DAG/modelo cargado.

---

## 2026-08-17 — Capa backend de compuestos Soporte al Cliente (ciclo `/speckit-implement`)

Alcance: `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/backend/`,
`dags/lib/dimensiones/dim_{sla_config,servicio,estado_soporte}.py`,
`dags/lib/hechos/{sla_vigente,hecho_ticket,hecho_accion_ticket}.py`,
`dags/lib/consultas/soporte/` (9 SQL), `dags/etl/dag_hecho_soporte.py`,
`backend/apps/informes_tacticos/` (permiso, servicio, vistas).

Los 9 compuestos de OT19/OT20 sobre el modelo: SLA vigente al crear el ticket (sin
`versionado.py`), cobertura BSC en la misma fila, centinelas `0` → ausencia, sin texto de
ticket ni nombre de agente. El tablero de cola operativo **no se retira** (decisión #20).
`informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` y `decisiones-pendientes.md`
no están en este workspace.

---

## 2026-08-17 — Capa frontend de compuestos Suscripciones (ciclo `/speckit-implement`)

Alcance: `frontend/src/app/modules/suscripciones/gestion/`, `frontend/src/app/app.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts`,
`specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/frontend/tasks.md`,
`specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/informes-compuestos-modelo.md`.

Sin hallazgo de spec vs. código: tres pantallas Z (`cobro`, `movimientos`, `catalogo`),
dos guards (Financiero / Estrategia), `meta.mes` declarado, sin columna de llamadas ni
enlace a métodos de pago. Los listados `/suscripciones/informes` y el catálogo de planes
no se tocaron.

---

## 2026-08-17 — Suscripciones compuestos: los 13 informes sobre el modelo analítico

Alcance: `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend/`,
`dags/lib/dimensiones/dim_{plan,cliente}.py`,
`dags/lib/hechos/hecho_{suscripcion,factura,solicitud_cambio_plan}.py`,
`dags/lib/consultas/suscripciones/` (13 SQL),
`dags/etl/dag_hecho_{suscripcion,facturacion}.py`,
`backend/apps/informes_tacticos/services/suscripciones_compuestos_service.py`,
`backend/apps/informes_tacticos/views/suscripciones_compuestos_views.py`.

### La causa

El departamento no tocaba el modelo analítico. Hacían falta dos dimensiones
conformadas, tres hechos y trece consultas para que MRR, ingresos, renovación,
movimientos y NRR dejen de no tener fuente.

### Cinco defectos del origen que no fallan

1. **`activo = true` en una Cancelada** inflaría el MRR. El modelo lee
   `estado_derivado`; ninguna consulta nombra `activo`.
2. **`motivocancelacion` poblado en Activa** no se copia: el motivo solo entra
   si el estado dice que canceló.
3. **Vigencia invertida** se marca (`vigencia_inconsistente`) y no se corrige
   ni se descarta: sigue contando como ingreso.
4. **`idplan_programado = 0`** se guarda nulo, no como un plan.
5. **Notas de crédito** restan vía `monto_con_signo`; sumar `monto_total`
   inflaría los ingresos.

`dim_cliente` es **conformada**: Cuentas y Clientes la ampliará, no la recreará.
Sin identificador fiscal, sin token, sin últimos dígitos. `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` no está en este workspace.

La autoridad está **repartida**: Financiero → OT06+OT07; Estrategia → OT05.
Ninguno cubre la materia del otro.

---

## 2026-08-17 — Capa frontend de compuestos Ventas-CRM (ciclo `/speckit-implement`)

Alcance: `frontend/src/app/modules/ventas-crm/gestion/`, `frontend/src/app/app.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts`,
`specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/frontend/tasks.md`,
`specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/informes-compuestos-modelo.md`.

Sin hallazgo de spec vs. código: las tres pantallas Z (`embudo`, `captacion`, `nutricion`)
pintan `meta.acotado_a` del envelope, excluyen `GerenteCuentasPublicas` y no titulan CAC.
Los listados `/ventas-crm/informes` y el pipeline no se tocaron.

---

## 2026-08-17 — Hallazgo (B17). ClickHouse no pone NULL en el LEFT JOIN de OT02/OT03

Alcance: `dags/lib/consultas/ventas_crm/ot02_{carga_por_ejecutivo,permanencia_por_etapa,pipeline_ponderado}.sql`,
`dags/lib/consultas/ventas_crm/ot03_efectividad_nutricion.sql`,
`specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md`.

### La causa

ClickHouse rellena un LEFT JOIN sin coincidencia con el **valor por defecto del tipo**, no con
NULL. `ifNull(etapa_en_corte, etapa_actual)` no cae a la dimensión cuando no hay transiciones
(`''` no es NULL). `d.idprospecto IS NULL` marca a todo el mundo como `con_demo` porque el
Int32 ausente llega como `0`. Además, `fechahora <=` en el `ON` del JOIN de conversiones
revienta con `INVALID_JOIN_ON_EXPRESSION` en 24.8.

### El efecto verificado

Con el stack táctico arriba: el estancado sin transiciones no salía en `abiertos` (SC-004);
`con_demo.denominador` era 2 en un escenario de 1+1; `ot02_carga_por_ejecutivo` no ejecutaba.
El pipeline no filtraba `fecha_registro <= hasta`, así que un período anterior al origen
seguía listando los 10 prospectos de 2026.
Tras `nullIf` / `IN (SELECT …)` y la desigualdad en `WHERE`, y con el período vacío en
`1999-01-01` (un corte sobre `dim_prospecto` no puede usar 2098: los 10 prospectos de 2026
siguen abiertos), `pytest dags/tests/test_ot0{1,2,3}*.py` verde.

---

## 2026-08-17 — Ventas y CRM compuestos: los 13 informes sobre el modelo analítico

Alcance: `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/backend/`,
`dags/lib/hechos/hecho_{transicion_embudo,asignacion_prospecto,interaccion_demo,notificacion_ventas}.py`,
`dags/lib/consultas/ventas_crm/` (13 SQL),
`dags/etl/dag_hecho_{ciclo_prospecto,nutricion}.py`,
`backend/apps/informes_tacticos/services/ventas_crm_compuestos_service.py`,
`backend/apps/informes_tacticos/views/ventas_crm_compuestos_views.py`.

### La causa

El departamento no tocaba ninguna tabla del modelo. Hacían falta dos dimensiones
(ya en fase 2) y **cuatro hechos** para servir OT01–OT03 y cubrir CU-T03 y CU-T04,
los dos casos de uso tácticos que ningún informe del proyecto cubría.

### Tres trampas que no fallan

1. **`Dim_Prospecto.activo` mezcla convertido con perdido.** De los tres con
   `activo = false`, dos se convirtieron y uno se perdió. El modelo lee
   `desenlace`; ninguna de las 13 consultas nombra `activo`.
2. **La permanencia sin tramo abierto deja fuera a los estancados** —justo a
   quienes el informe existe para encontrar— y los presenta como los más rápidos.
3. **Un aviso ignorado contado como latencia cero mejora el indicador.**
   `hubo_avance = 0` y `segundos_a_reaccion` ausente quedan fuera de la mediana.

### Lo que no entra

Identidad y contacto del prospecto, notas de transición, metadata de demo,
`estado_envio` (nadie la escribe) y **ninguna columna de coste**, ni vacía.
El informe de convertidos por canal declara en `nota_indicador` que es la parte
medible del CAC. `pesos_etapa` viaja en `meta.filtros` como convención del
informe, no como política.

### El catálogo de OT

La ruta `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` **no está
en el repositorio**. El estado de los 13 informes queda en este changelog y en
`tasks.md` (T014–T064). El defecto de `activo` se anota también en
`decisiones-pendientes.md` #43, para que otros departamentos no lo copien.

### Verificación

Pruebas de texto del catálogo (T014–T016), acotamiento con `acotado_a` (T017),
constructor de los cuatro hechos, y pruebas contra ClickHouse en partición
`209912` para permanencia, embudo, carga histórica, motivos, canales, nutrición,
denominador, periodo vacío y crecimiento aditivo.

---

## 2026-08-16 — Partners y API: cinco listados tácticos en pantalla (FR-014a + `entorno`)

Alcance: `specs/002-tactico/Partners-API/informes-tacticos-simples/frontend/`,
`frontend/src/app/modules/partners/informes/` (catálogo, 2 guards, 2 páginas, rutas),
`app.routes.ts`, `nav-links.ts`,
`backend/apps/partners/permissions.py` (`es_gestor_informes`),
`backend/apps/partners/domain_constants.py`,
`contracts/informes-tacticos-simples.openapi.yaml` (enum `entorno`).

### La causa

El backend de los cinco GET ya existía, pero el Director Tecnológico recibía **403** en todos:
`InformesAccesoPermission` usaba `ROLES_GESTORES` (solo Administrador y Desarrollador de APIs).
FR-014a y `acceso-tactico.md` lo exigen en los cinco, sin acotar. Meterlo en `es_gestor()` le
abriría la consola operativa (emitir, suspender, resolver promociones).

El OpenAPI declaraba `entorno: Produccion` sin tilde; el dominio y la vista validan `Producción`.
Un filtro copiado del contrato produciría `400`.

### El efecto verificado

Un token `DirectorTecnologico` obtiene **200** en los cinco; `es_gestor()` sigue siendo False para
él. El Partner entra a los tres de acceso (`acotado_a: propios`) y recibe **403** en versiones y
alcance. El enum del contrato coincide con `ENTORNO_PRODUCCION`.

### Lo que se hizo

`ROLES_GESTORES_INFORMES` = gestores ∪ Director. `es_gestor_informes()` alimenta permisos y
`acotar()`. `es_gestor()` no cambia. Frontend: ruta hermana `partners/informes` **antes** de
`partners`; dos guards (acceso vs contrato); dos ítems de menú con la misma path y roles disjuntos.
Credenciales no pintan motivo ni secreto. Ausente se ve `—`; cupo `0` se ve `0`.

### Verificación

Karma del módulo: **71 verdes**. Backend: `test_informes_permisos.py` + `test_propiedad_partner.py`,
**36 verdes**. `ng build` de producción sin errores nuevos.

---

## 2026-08-16 — OE3: meta de E3-02 y reclasificación de E3-12

Alcance: `specs/001-estrategico/OE3-escalabilidad-multiregion/backend/`,
`informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §3,
`decisiones-pendientes.md` #38 (ampliada) y #41.

### La causa

El catálogo definía E3-02 como p95 solicitud→confirmación con alerta ≤100 ms.
Esa frase mezcla la latencia **técnica** del algoritmo con el tiempo **operativo**
del proceso. Medido: oferta→confirmación p95 28 s; registro→primera asignación
p95 **106 s = 1,77 min**. Contra 100 ms el informe estaría 1 060 veces en rojo,
y el rojo sería falso.

E3-12 pedía la mediana entre la falla del algoritmo y la intervención manual.
**1 082 de 1 083** despachos manuales no siguen a ningún intento automático.

### El efecto verificado

RNF-DES-001 fija `<2 min p95` para el proceso completo. Con esa meta, E3-02
**cumple** (1,77 min; 58 de 3 638 sobre el umbral). E3-12 no se publica.

### Lo que se hizo

E3-02 mide registro→asignación contra 2 minutos `[NORMATIVO]`, con `meta.alcance`
que separa las dos métricas. E3-12 pasa a ⛔ (decisión #41). E3-04/05/06 se
declaran ⛔ con el prerrequisito de historizar el estado de región (#38).

---

## 2026-08-16 — D1 / #38: el eje de región no es construible (OE6)

Alcance: `specs/001-estrategico/OE6-respuesta-y-vidas/backend/` (`research.md` D1,
`spec.md` corrección de `FR-OE6-008`, `data-model.md` §5),
`dags/tests/test_catalogo_estrategicos.py` (`TestProhibicionDelEjeDeRegion`),
`informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §6.

### La causa

`FR-OE6-008` pedía agrupación por región suponiendo que una región cubre un estado entero.
Se comprobó contra `dim_region` y contra el origen operativo: **dos regiones vivas
comparten el mismo `idestado_geo`** (Ciudad de Mexico). Unir `hecho_accidente` con
`dim_region` por estado duplicaría cada caso —4 252 → 8 504— **sin que la consulta
falle**. Cada región mostraría el total completo.

Y no es un olvido de carga: **no existe relación región↔condado** en el sistema
operativo. La cobertura se define a nivel de estado
(`Dim_RegionOperativaEstadoRegion`).

### El efecto verificado

Con los datos de hoy el eje sería degenerado igual: 4 252 casos en dos condados del
mismo estado. Agrupar por región devolvería una sola fila útil.

### Lo que se hizo

Se agrupa por **condado**. El eje de región queda ⛔ con prerrequisito nombrado
(tabla puente región↔condado). `FR-OE6-008` se corrige. Una prueba sobre el texto
de las consultas falla si alguien «arregla» el eje uniendo `dim_region`. Afecta
también a OE3 (E3-01 a E3-08). Decisión pendiente **#38**.

---

## 2026-08-16 — Red Operativa: los 15 informes compuestos, construidos

Alcance: `dags/lib/consultas/red_operativa/` (15 consultas), `dags/lib/ddl.py` (una dimensión, dos
hechos, cuatro columnas), `dags/lib/dimensiones/dim_region.py`, `dags/lib/hechos/`
(`hecho_baja_unidad`, `hecho_validacion_region`), sus flujos y DAG,
`backend/apps/informes_tacticos/` (servicio, vista, permisos, 15 endpoints), `dags/tests/` (nueve
ficheros nuevos).

**El segundo departamento no necesitó plomería propia.** Reutiliza el cargador de consultas, el
repositorio de lectura, la resolución de período, el versionado de dimensiones y el envelope — todo
construido para Emergencias. Eso es lo que este módulo venía a comprobar: si el segundo hubiera
necesitado la suya, los seis restantes también, y los 108 informes del catálogo volverían a ser 108
soluciones particulares.

### Las dos trampas del departamento

**El catálogo de estados de unidad está incompleto** (decisión #40). Tiene tres filas y el historial
usa cuatro: de **45 transiciones, 6 son «En Misión»**. Un `INNER JOIN` devolvería 39 sin fallar, y lo
que desaparecería es la actividad de las unidades trabajando. El hecho guarda el **nombre** del estado
ya resuelto, y una prueba sobre el texto de las consultas lo vigila en dos mitades: que no se une, y
que el estado se lee por su nombre y no por su identificador.

**La disponibilidad se mide en tiempo, no en transiciones.** Es la peor de las dos porque falla con el
signo invertido: una unidad que nunca falló no tiene ninguna transición, así que contar cambios le da
**0 %** — el peor resultado posible al mejor comportamiento, en el informe que sirve para premiar a
los proveedores fiables.

### El origen confunde dos nociones de «estado» de región

`Dim_RegionOperativa.estadoregion` vale «Producción» —ciclo de vida— y `Dim_EstadoRegion.estadoregion`
vale «Ciudad de Mexico» —geografía—, con el mismo nombre de columna. Y
`Dim_RegionOperativaEstadoRegion`, que el catálogo de informes citaba como fuente del primero,
relaciona con **el segundo**. Se comprobó fila a fila.

Un informe de «regiones publicadas» que leyera la geografía devolvería todas o ninguna, y **las dos
respuestas parecen plausibles**: con dos regiones, «2 de 2» y «0 de 2» son cifras que nadie cuestiona.

### La autoridad repartida

Este departamento no tiene jefatura única: Expansión gobierna crecimiento y flota, Tecnológico los
criterios de validación de región. El error natural es admitir a las dos autoridades y quedarse
tranquilo — eso daría a cada director la materia del otro **sin ningún síntoma**, porque un permiso
demasiado ancho no falla.

La materia se declara **por informe en el servicio**, y un informe sin materia **no lo ve nadie**. Se
comprobó por HTTP con el login real de cada director.

⚠️ Solo dos informes son de validación. «Regiones en riesgo» suena a validación —habla de regiones— y
no lo es: habla de si el mercado aguanta, que es de quien decide dónde crecer.

### El relleno del LEFT JOIN, cuatro veces más

ClickHouse rellena las filas sin coincidencia con el **valor por defecto del tipo**, no con `NULL`, y
volvió a morder en cuatro sitios: el nombre de región salía en blanco, `uniqExact` contaba el `0` del
relleno como una unidad —un condado vecino sin ninguna salía con una—, y `minIf` sin filas que
cumplan devolvía la época cero, dando **–20 677 días**. Ese negativo se ve; lo peligroso es que la
misma causa produce números positivos plausibles en cuanto las fechas caen del otro lado.

### Dos fallos en el andamiaje y dos en mis propias pruebas

`condados_vecinos` es la primera columna de array del modelo, y destapó que `etl_modelo._valor`
llamaba `.item()` sobre un `ndarray` —que también lo tiene, pero exige un solo elemento— y que
`tipos_almacen` hacía `int()` sobre la lista entera.

Y el `transform` de dimensiones leía los catálogos de geografía desde **una lista de cinco nombres a
mano**, así que `vecinos` se sustituía por lista vacía: **ningún condado con vecinos**, que en la
cobertura crítica es la marca de «sin alternativas». Es el mismo fallo que ya había pasado en
`hecho_accidente` con `FUENTES`.

En mis pruebas: una que dije haber verificado por mutación **cuya mutación ni se aplicó** —el
`str.replace` que no falla cuando el ancla no existe— y, tras repetirla bien, otra que **pasaba por el
motivo equivocado**: la región de prueba no tenía versión en producción, así que el resultado era
ausente por otra razón.

### Siete de quince informes son de corte, no de período

Red Operativa es más un departamento de fotos que de películas, y las reglas del catálogo se
escribieron pensando en Emergencias, que es lo contrario. Tres reglas necesitaron declarar
excepciones —el `desde` obligatorio y el período vacío—, todas con su razón escrita y con una prueba
de que la lista de exenciones no acumula entradas muertas.

### Verificación

`dags/`: **582 verdes, 53 saltadas**. `apps/informes_tacticos`: **199 verdes** ejecutado aislado.

⚠️ **En la suite completa del backend fallan 13 pruebas de contraste** que pasan aisladas. Es
contaminación por orden entre pruebas —alguna anterior deja parcheado el cliente de Pinot y los
contrastes, que necesitan Pinot real, reciben el doble—. Es la misma familia que las 5 de
`test_pinot_client_limit`, ya registradas, y **no un defecto de este módulo**: aislado, todo pasa.

---

## 2026-08-16 — Red Operativa: por qué `dim_geografia` no guardaba los vecinos

Alcance: `dags/lib/dimensiones_tasks.py`, `dags/lib/dimensiones/desconocido.py`,
`dags/lib/etl_modelo.py`, `dags/lib/tipos_almacen.py`,
`dags/tests/test_fuentes_del_flujo_de_dimensiones.py` (nuevo).

### La causa: el mismo fallo, por segunda vez

El `transform` del flujo de dimensiones reconstruía los catálogos de geografía desde **una lista de
cinco nombres escrita a mano**. El `extract` sí guardaba `vecinos` y `regiones`; el `transform` no los
volvía a leer, y `catalogos.get("vecinos", [])` los sustituía por una lista vacía.

Es exactamente lo que ya había pasado en `hecho_accidente` con `FUENTES`, y el síntoma vuelve a ser
el mismo: **no falla nada**. Sale un cero plausible y nadie lo cuestiona.

Aquí, además, el cero es la peor lectura posible: `condados_vecinos` vacío significa **«sin vecinos
declarados»**, que en el informe de cobertura crítica es la marca de **sin alternativas** — la
situación más grave que ese informe reporta. Un olvido de lectura se habría publicado como una
emergencia operativa.

Ahora los nombres salen de `dim_geografia.CONSULTAS`, y hay una prueba que **lee el código del flujo**
para comprobar que no vuelve a existir una lista a mano. Verificada por mutación.

### Dos fallos del andamiaje que la primera columna de array destapó

Ninguna columna del modelo era un array hasta `condados_vecinos`, así que ningún camino lo
contemplaba:

* **`etl_modelo._valor`** llamaba `.item()` sobre un `ndarray`. Los arrays de numpy **también** tienen
  `.item()`, pero ahí exige un solo elemento y falla con «can only convert an array of size 1 to a
  Python scalar» — un mensaje que no menciona ni la columna ni el tipo, y que salta dos pasos después
  de la causa.
* **`tipos_almacen._ajustar`** hacía `int(valor)` sobre la lista entera.

### La fila desconocida también necesitaba las columnas

Y su lista vacía **sí es correcta**: no es un condado, es el destino de las calles cuyo condado no
está en el catálogo, así que no puede tener vecinos. Se dice en el código para que nadie lo lea como
una omisión.

### Lo que sigue sin estar bien

`dim_unidad.fecha_alta` y `tuvo_primer_acceso` **siguen sin llegar al almacén**, y la causa es
distinta: el versionado no reescribe nada si ningún **atributo versionado** cambió, y estos dos no lo
son a propósito. Hace falta refrescar las columnas no versionadas de la versión vigente sin abrir
versión nueva — el motor lo permite (`ReplacingMergeTree(version)`), pero el flujo no lo hace hoy.

⚠️ Seis de las ocho consultas de US1 leen esas columnas. Escribirlas antes de resolver esto daría
informes que devuelven cero con toda naturalidad.

---

## 2026-08-16 — Los roles tácticos no existían en la base, y ahora sí

Alcance: `database/siembra_roles_tacticos.py` (nuevo).

### El punto ciego

Los permisos de los informes tácticos conceden acceso a **ocho autoridades
departamentales**. En la base solo existían dos: `DirectorTecnologico` y
`DirectorEstrategia`. Las otras seis —incluido el **Director de Operaciones**, que es la autoridad
de los trece informes compuestos de Emergencias— **no existían ni como rol ni con ningún usuario**.

Los permisos pasaban sus pruebas porque **esas pruebas acuñan el JWT directamente**. Comprueban que
el permiso decide bien, no que exista alguien capaz de obtener ese token. Y la distinción no falla por
ninguna parte: la API responde `403` a quien no tiene el rol, y a un rol que no existe le responde
exactamente igual. «Nadie puede entrar» y «el permiso funciona» se ven idénticos desde fuera.

Lo levantó el usuario, no una prueba. Merece decirse: ninguna de las suites lo habría visto, porque
todas entran por la puerta que se salta el problema.

### Lo que se sembró

Los seis roles que faltaban, y **un usuario por cada uno de los ocho** —no uno con los ocho roles—.
La razón es que la autoridad de Red Operativa está **repartida**: Expansión y Tecnológico no ven lo
mismo, y un usuario con todos los roles haría imposible comprobar ese reparto entrando de verdad.

El script usa los repositorios del backend, que publican por Kafka. No escribe en Pinot: el único
escritor del sistema operativo es el productor. Es idempotente.

### Verificado por login real, no por token fabricado

| Quién | Qué pidió | Resultado |
|---|---|---|
| Director de Operaciones | completitud de Emergencias | **200** |
| Director de Expansión | completitud de Emergencias | **403** — no es su departamento |
| Director de Expansión | mercados activos (crecimiento) | permiso concedido |
| Director de Expansión | motivos de rechazo (validación) | **403** — materia ajena |
| Director Tecnológico | motivos de rechazo (validación) | permiso concedido |
| Director Tecnológico | mercados activos (crecimiento) | **403** — materia ajena |
| Director de Marketing | completitud de Emergencias | **403** |

La autoridad repartida de Red Operativa queda así comprobada **de extremo a extremo**: login, JWT
emitido por el sistema, y el permiso decidiendo por materia.

⚠️ Las contraseñas del script son de entorno de pruebas y están declaradas como tales.

⚠️ **Queda una brecha de método**: todas las pruebas de permisos siguen acuñando el token. Convendría
al menos una que entre por el login, para que el hueco que el usuario encontró no pueda repetirse en
silencio.

---

## 2026-08-16 — Emergencias compuestos: módulo terminado (T076 y T078)

Alcance: recorrido del quickstart contra el stack, y
`informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` actualizado.

**Las 78 tareas del módulo están hechas.**

### T076 — el quickstart, recorrido entero contra el stack levantado

Las nueve comprobaciones del §2, sin fallos:

| | Qué se comprobó | Resultado |
|---|---|---|
| 2.1 | Un informe no crea ninguna tabla | 13 tablas antes y después |
| 2.2 | La completitud puede bajar del 100 % | Sobre datos reales da 1 con 4252 casos —correcto, no hay incompletos—; con el caso fabricado baja, y eso lo prueba T024 |
| 2.3 | La capacidad es la del período | 17 unidades vigentes en cada mes, de las versiones que cubrían ese mes |
| 2.5 | La pérdida de señal ve todo | **59 039 intervalos de 59 045 posiciones y 3 942 huecos** — el flujo viejo veía 10 000 y hallaba 714 |
| 2.6 | Sin dato no es cero | Con `muestra_minima=500` la referencia viene `null`; un período vacío devuelve `data` vacío |
| 2.7 | Los que conviven coinciden | 4252 y 4314 por ambos caminos en los cuatro contrastados |
| 2.8 | Nada sensible sale | Los 13 endpoints publicados, también con la autoridad departamental |
| 2.9 | Ningún caso se pierde | Las distribuciones suman 4252, el total del período |

Los seis intervalos que faltan en 2.5 son las **primeras posiciones de cada unidad**, que no tienen
anterior con el que medir. Su medida es ausente, no un hueco de cero segundos.

### T078 — el catálogo de informes, actualizado

24 de los 27 compuestos de Emergencias pasan a construidos, y los dos que estaban en rojo también:
su defecto era del endpoint operativo y **el modelo lo corrige**. El endpoint viejo sigue en pie a
propósito (T023), así que la nota del defecto se conserva y se completa en vez de borrarse.

**El reparto, contado a mano**: 12 simples, **27 compuestos** y 1 fila que es configuración y no
informe. No son los 12/26 que anticipaba el `tasks.md` ni los 14/25 del resumen: la fila de más es la
desviación entre ETA estimado y llegada real, que el catálogo cuenta aparte y el módulo entrega como
`desviacion-llegada`. Se registra el conteo medido en vez de repetir el previsto.

### Lo que queda abierto, y no es poco

Cuatro decisiones que este módulo destapó y no le corresponde resolver:

* **#34** `rechazo-timeout-por-unidad` divide entre transiciones de estado y trunca su tabla.
* **#35** `tiempo-asignado-cerrado` no devuelve siempre la misma cifra.
* **#36** «retiro forzado» y «cierre forzado» difieren en un factor de 451.
* **#37** la suite del backend no da lo mismo en el host que en el contenedor.

Las tres primeras son informes **clasificados como correctos** que no lo son, y las tres las
encontraron las pruebas de contraste — T028, T047 y T071—, que es exactamente para lo que existen.

---

## 2026-08-16 — T071 y fase 6 (parcial): tres pruebas transversales y tres defectos más

Alcance: `backend/apps/informes_tacticos/tests/api/test_contraste_ot25.py` (nuevo), `dags/tests/`
(tres ficheros nuevos), dos consultas de OT25 con su encabezado corregido, `decisiones-pendientes.md`
(#35, #36, #37).

### T071 estaba sin hacer, y encontró dos defectos más

Se dio US3 por completa con T071 pendiente — el mismo despiste que con T046/T047. Y como las otras
dos pruebas de contraste, es la que más encontró.

**`tiempo-asignado-cerrado` no devuelve siempre la misma cifra** (decisión **#35**). Atribuye cada
caso a una sola unidad con un diccionario por comprensión, así que para un caso con varios despachos
gana **el último que devuelva Pinot** — y Pinot no garantiza orden sin `ORDER BY`. Son 441 casos de
3651, el 12 %. No es que el modelo y el endpoint midan distinto: es que el endpoint no mide siempre lo
mismo, y contrastarlo con una tolerancia sería contrastar contra un número que se mueve solo.

**«Retiro forzado» y «cierre forzado» son dos cosas distintas con nombres casi iguales** (decisión
**#36**), y la diferencia es de un **factor de 451**:

| | Qué es | Cuántos |
|---|---|---|
| `Fact_Despacho.retiro_forzado` | Un indicador del despacho | **1** de 4314 |
| «Cierre forzado» del informe | Transición a `Retirado` con `idusuario` poblado: retiro **manual** desde central, frente al automático por vencimiento | **451** de 3310 |

Dos consultas mías usaban el primero creyendo medir el segundo, y una de ellas
—`retiros-forzados-por-proveedor`— **está publicada como endpoint**. El modelo no puede reproducir hoy
la definición del informe, y no por descuido: lo que distingue un retiro manual de uno automático es
la presencia de `idusuario`, y la identidad está excluida del modelo por decisión constitucional. La
salida natural es un **booleano derivado al cargar** —«el retiro fue manual»— que conserve el hecho
sin la identidad; es un cambio de esquema pendiente. Mientras tanto las dos consultas lo declaran en
su encabezado y la prueba no las compara.

### Una prueba que codificaba mis suposiciones, no una regla

La comprobación de que todo porcentaje lleva su numerador intentaba emparejarlos **por morfología**
—`pct_descarte` con `descartados`, `pct_huecos` con `huecos`— y fallaba en siete informes de
veintiséis: en español el plural del nombre no se deriva del singular del prefijo
(`pct_retiro_forzado` frente a `retiros_forzados`).

Una regla que no funciona se relaja hasta no comprobar nada. Se sustituyó por un **mapa declarado a
mano**: un informe nuevo sin entrada falla, que es el defecto correcto, y sobra una entrada si su
informe desaparece.

### La prueba de latencia mide el escalón, no el rendimiento

Va sobre **siete meses** de datos, y hay una segunda prueba que comprueba que ese rango abarca al
menos tres particiones **con filas**: un informe sobre un día responde rápido siempre, aunque recorra
la tabla entera, así que sin datos suficientes la prueba pasaría sin decir nada. El tope es generoso a
propósito — detecta la consulta que perdió la poda de particiones, no la máquina cargada.

### T075: la suite no da lo mismo según dónde se ejecute

Decisión **#37**. En el host fallan 5 pruebas de JWT que en el contenedor pasan; en el contenedor
fallan 8 recolecciones y ~13 pruebas que en el host pasan, por PyYAML y por los ficheros de la raíz
que la imagen no monta. Y en los dos fallan las 5 de `test_pinot_client_limit`, que **pasan aisladas**
—contaminación preexistente—.

Hoy la respuesta a «está la suite en verde» depende de dónde se pregunte, que es la peor situación
posible: cada entorno da un verde que el otro desmiente. **Cualquier cifra de "N verdes" tiene que
decir dónde se midió.**

### Verificación

`dags/`: **416 verdes, 31 saltadas** (en el contenedor de Airflow).
`apps/informes_tacticos`: **144 verdes** en el contenedor; en el host, 5 rojas por lo anterior.

### Lo que queda de la fase 6

T076 (recorrer el quickstart contra el stack) y T078 (actualizar el estado de los 26 informes en
`TSI-Informes-Tacticos-Requeridos-por-OT.md` y corregir allí el reparto simples/compuestos de
Emergencias).

---

## 2026-08-16 — US3 completa: las diez consultas de OT24 y OT25 y sus ocho endpoints

Alcance: `dags/lib/consultas/emergencias/` (10 consultas), `dags/tests/` (cuatro ficheros nuevos),
`backend/apps/informes_tacticos/services/emergencias_compuestos_service.py` (catálogo, publicados y un
parámetro de lista), `dags/tests/test_catalogo_consultas.py`.

Con esto el catálogo tiene **26 consultas** y el módulo publica **13 endpoints**, que es exactamente
lo que decía su alcance: construye 10, migra 3 y vigila 13.

### Tres errores encontrados al ejecutar, no al revisar

**«Sin cerrar» decía 4251 donde había 616.** La versión obvia de la distribución de resultados agrupa
por `coalesce(resultado_atencion, 'Sin cerrar')`, y hoy hay 3636 casos con hora de cierre y **uno** con
resultado registrado. El informe habría dicho que casi nada se ha terminado cuando lo que pasa es que
casi nada se documenta al terminar: dos problemas con dos responsables distintos, y confundirlos manda
a mirar el sitio equivocado. El grupo se decide ahora con `hora_cierre`, y hay un tercer valor
—«Cerrado sin resultado registrado»— que antes no existía.

**`roundDown` no admite un array de parámetro.** Falla con `ILLEGAL_COLUMN`, un error que habla de
columnas y no de constantes. Se sustituyó por `arrayLast`, que sí opera sobre un array calculado y
devuelve `0` cuando ningún corte encaja — un cero que significa «más nuevo que el primer corte», no
«cero días».

**Los cortes se ordenan antes de usarlos.** `arrayLast` recorre en orden, así que una lista
desordenada como `30,1,7` mandaría cada caso al tramo equivocado **sin fallar**. Se ordena en el
backend, con el resto de la validación.

### El patrón de dato sensible, otra vez, y el arreglo definitivo

`notas`, `solo_nota` y `categoria_nota` dispararon el patrón `%nota%` sobre el texto de las consultas.
La comprobación miraba **el SQL entero como cadena**, así que no podía distinguir la columna con el
texto de una nota de un recuento de notas.

Ahora extrae **identificadores** y los juzga uno a uno, con una lista de permitidos explícita y una
prueba que comprueba que cada permitido tiene forma de recuento o de categoría. Y descarta los
literales antes de extraer: `tipo = 'nota'` compara contra un valor, no nombra una columna — leerlo
como columna hacía fallar una consulta que no toca ningún texto. Verificado por mutación: añadir
`idusuario` a una consulta sigue haciéndola fallar.

### Decisiones que las consultas registran

**La cobertura parte de los casos, no de las evidencias.** Con un `JOIN` desde las evidencias, un caso
sin ninguna no aparecería en ninguna fila y la cobertura saldría del 100 % siempre: el informe diría
que todo está documentado justamente porque no ve lo que falta. Los cuatro grupos —solo foto, solo
nota, ambas, ninguna— son excluyentes y suman el total.

**Los pendientes no son latencia cero.** Si lo fueran, cuanto peor funcionara la sincronización mejor
saldría la latencia, porque cada evidencia atascada bajaría la mediana. Se publican al lado. Y la
latencia se desglosa por tipo porque **todas las notas son pendientes** —su fuente no tiene columna de
sincronización— y sin el desglose esa cifra escondería por completo la de las fotos.

**El volumen se entrega por unidad y no por persona** (FR-034), aunque el catálogo lo pedía por
técnico y el dato está disponible. La prueba lo comprueba en dos sitios: que ninguna respuesta trae
una columna de persona, y que **la tabla tampoco la guarda** — una consulta que no pide el dato lo
deja fuera hoy; una tabla que no lo tiene lo deja fuera siempre.

**La cartera excluye descartados y fusionados.** No están abiertos aunque no tengan cierre: se decidió
sobre ellos, y arrastrarlos inflaría el atraso con trabajo ya resuelto. Los 255 casos abiertos son
exactamente los 616 sin cerrar menos los 220 descartados y los 141 fusionados.

**El denominador de los retiros forzados son los despachos confirmados.** Un retiro solo puede ocurrir
donde hubo aceptación; dividir entre todos los intentos favorecería al proveedor que más rechaza.

### Verificación

`dags/`: **314 verdes**. `apps/informes_tacticos`: **139 verdes**. Los ocho endpoints comprobados por
HTTP contra el stack, con `400` y su explicación para una lista de tramos inválida o vacía, y `404`
para los informes que se vigilan y no se publican.

⚠️ Las cifras de OT24 y OT25 son casi todas cero o nulas, y **es correcto**: el origen tiene 3 fotos,
51 notas, 3 implicados, 3 elementos de clima, 1 escalada y 1 cierre con resultado. Por eso las pruebas
van con datos sintéticos — con los reales, una consulta rota y una fuente vacía se ven exactamente
igual.

---

## 2026-08-16 — US3: modelo ampliado y poblado (evidencia, enriquecimiento y cierre)

Alcance: `dags/lib/ddl.py` (ocho columnas y una tabla), `dags/lib/hechos/hecho_accidente.py` (seis
fuentes nuevas), `dags/lib/hechos/hecho_evidencia.py` y `dags/lib/hecho_evidencia_tasks.py` (nuevos),
`dags/etl/dag_hecho_evidencia.py` (nuevo), `dags/lib/hecho_accidente_tasks.py`, `dags/tests/` (tres
ficheros nuevos, tres ampliados).

Quinto hecho del modelo. Cargado hoy: 51 notas, 3 implicados, 3 elementos de clima, 1 escalada, 1
resultado de atención y **0 calificaciones**; `hecho_evidencia` con 54 filas (3 fotos, 51 notas).

### Un fallo que ocurrió de verdad y no falló nada

Se añadieron las seis fuentes nuevas a `extraer()` y se olvidó añadirlas a `FUENTES` en el módulo de
tareas, que es lo que `transform` vuelve a cargar del disco. El `datos.get(nombre, [])` de `construir`
las sustituyó por listas vacías y **todos los recuentos salieron a cero**.

Cero es un valor legítimo en esas columnas —cero notas es una medición—, así que el resultado era
**indistinguible de un origen sin datos**: el modelo publicó `0` notas donde el origen tenía 51, sin
un solo error, sin un aviso, y con una explicación perfectamente plausible a mano («las fuentes están
casi vacías, ya lo decía research D8»). Se descubrió comparando con el origen a mano.

La prueba que lo caza compara la tupla del flujo con las claves que devuelve `extraer()`. Es barata y
no existía porque nadie había añadido una fuente desde que se escribió el flujo.

### El cero que sí es ausencia, y el que no

Las ocho columnas nuevas se reparten en dos bloques con reglas **opuestas**, y aplicar la de un bloque
al otro rompe el informe en el sentido que peor se detecta:

| | Regla | Qué pasa si se invierte |
|---|---|---|
| Recuentos (`num_*`) | `0` cuando el caso existe y no tiene ninguno | Un caso sin notas desaparece del recuento en vez de contar como no documentado |
| `calificacion`, `resultado_atencion`, `severidad_inicial` | **Ausente** cuando no se registró | Un caso sin calificar se convierte en el peor caso del mes |

El caso ambiguo está vivo en el origen: la única fila de `Fact_CierreAccidente` trae
`calificacion = 0` con `resultado_atencion = "Cierre automático tras retiro forzado"`. Nadie la
calificó. La regla —`0` no está en la escala— no se inventó aquí: **ya la aplica el listado operativo
de cierres**, y se repite en la carga porque los DAG y el backend son procesos distintos que no pueden
compartir la constante.

### La unidad de la evidencia se deriva, porque el origen no la trae

Ni `Dim_EvidenciaFoto` ni `Dim_NotaAccidente` tienen unidad: traen `idusuario`, excluido por la
decisión D6. La evidencia se atribuye al **primer despacho que llegó** — no al confirmado, por dos
razones: `Fact_Despacho` no guarda la hora de confirmación, y además haber confirmado no es haber ido.

Hoy resuelve 23 de 54. Las otras 31 caen en la **unidad desconocida** porque sus casos no tuvieron
ninguna llegada, y se quedan en el informe en vez de descartarse: descartarlas bajaría el volumen de
evidencia sin que nada indicara que faltan filas.

### Lo que no se fabrica

`Dim_NotaAccidente` **no tiene columna de sincronización**. La latencia de las notas es genuinamente
desconocida, así que va ausente: ni cero, que diría que fue instantánea, ni la fecha de carga, que
diría que tardó justo lo que llevamos mirándola. Y las tres fotos vienen con `sincronizado = true` y
`fecha_sincronizacion = null` — el indicador dice que llegó y la fecha dice cuándo; que falte la
segunda no desmiente la primera, solo impide medir. Ninguna de las 54 evidencias tiene latencia
medible hoy, y eso es lo que dirá el informe.

### Dos trampas del andamiaje

**`CREATE TABLE IF NOT EXISTS` no migra nada.** En una instalación nueva la tabla nace con las ocho
columnas; en la existente el `CREATE` no hace nada y las columnas no aparecen. El DDL parecería
correcto y el almacén estaría incompleto, sin error hasta que una consulta pidiera una columna
inexistente. Se añadió `ensure_columnas_nuevas_hecho_accidente()`.

**`num_notas` disparó el patrón `%nota%`** de la prueba de dato sensible. Se declaró la excepción con
su razón —contar no es leer: saber que un caso tiene tres notas no revela ninguna— más una prueba que
comprueba el **tipo** de cada excepción, para que meter `observaciones` en esa lista no funcione. El
patrón sigue siendo amplio a propósito.

### Verificación

`dags/`: **234 verdes**. `apps/informes_tacticos`: **137 verdes**. **SC-010 verificado**: ampliar el
modelo con un hecho y ocho columnas no movió ninguna cifra de US1 ni de US2.

### Lo que queda de US3

Las diez consultas de OT24 y OT25 (T055 en adelante) y sus pruebas.

---

## 2026-08-16 — Emergencias compuestos: cierre real de US2 y arranque de US3

### Primero, una corrección: la fase 4 no estaba cerrada

Se dio por completa con T046 y T047 sin hacer. Ambas eran de US2, y T047 —la prueba de contraste— es
justo la que más encontró de todo el módulo.

### T047 encontró tres cosas, y una era un error propio

**1. Mi consulta medía otro intervalo.** `ot22_tiempo_respuesta_por_severidad` usaba
`segundos_transito`, que es *confirmación → llegada*, mientras el endpoint mide *despacho → llegada*.
Quedaban fuera los ~18 s que la unidad tarda en aceptar. La consulta daba 450,62 s donde el endpoint
daba 468,94.

**2. Sumar dos columnas ya truncadas mete un sesgo de +1 s.** El arreglo obvio era
`segundos_respuesta + segundos_transito`, y da 467,95 frente a 468,95 reales: las dos vienen
truncadas a segundos y cada una pierde medio segundo de media. El sesgo es **constante y del mismo
signo**, así que sobrevive a cualquier promedio y a cualquier comparación entre períodos — no se
delata como ruido, parece precisión. Se calcula con **una sola resta**.

**3. `rechazo-timeout-por-unidad` está mal, y estaba clasificado como correcto** → decisión pendiente
**#34**. Dos defectos independientes:

| | Qué pasa |
|---|---|
| Denominador | Son **transiciones de estado**, no intentos de despacho. Un despacho bien atendido genera cinco filas de historial y uno rechazado dos: **cuanto mejor trabaja una unidad, más baja parece su tasa de rechazo** |
| Truncamiento | 19 528 filas, tope por defecto de 10 000, el **48,8 %** analizado |

Medido en `LOTE-A2`: el endpoint publica **0,0769** (1 de 13 transiciones) donde la tasa real es
**0,2** (1 rechazo de 5 despachos). Un factor de 2,6. Sobre este informe se decide qué proveedor
sigue.

La prueba **declara la discrepancia y falla si algún día desaparece** —eso significaría que la
decisión se resolvió—, en vez de compararlos con una tolerancia amplia: una tolerancia capaz de tapar
un factor de 2,6 no detectaría nada.

### Una exclusión declarada, no disimulada

`tiempo-reportado-a-confirmado` queda **fuera del contraste numérico**. Los dos caminos miden los
mismos 3638 casos y arrancan el cronómetro en instantes distintos: el endpoint en el estado
`REPORTADO` del historial, el modelo en el momento del accidente. Da 72,66 s y 79,02 s, y **las dos
son correctas** para lo que cada una mide. El modelo no guarda hoy el instante de `REPORTADO`, y
añadirlo es un cambio de esquema ajeno a esta historia.

Se comprobó antes de concluirlo que **no** era el truncamiento de Pinot: la consulta filtra por tipo
de estado y deja 7679 filas, por debajo del tope.

### T046 — el pasado no se reescribe

Cambiar el proveedor de una unidad en la dimensión no mueve las cifras de un período ya cerrado.
`hecho_despacho` guarda el proveedor **del momento del despacho**, así que quien hereda las unidades
de otro no hereda sus rechazos.

### Arranque de US3: el modelo ampliado

Ocho columnas nuevas en `hecho_accidente` y la tabla `hecho_evidencia`.

⚠️ **`CREATE TABLE IF NOT EXISTS` no migra nada.** En una instalación nueva la tabla nace con las ocho
columnas; en la que ya existe, el `CREATE` no hace nada y las columnas **no aparecen** — el DDL
parecería correcto y el almacén estaría incompleto, sin ningún error hasta que una consulta pidiera
una columna inexistente. Se añadió `ensure_columnas_nuevas_hecho_accidente()` con
`ALTER … ADD COLUMN IF NOT EXISTS`, y las 4252 filas anteriores quedan en `NULL`, que es lo correcto:
nadie midió cuántas notas tenía un caso cargado antes de que la métrica existiera.

**SC-010 verificado**: ampliar el modelo no alteró ninguna cifra de US1 ni de US2 — las pruebas de
contraste siguen en verde contra los endpoints operativos.

**Un falso positivo instructivo**: `num_notas` disparó el patrón `%nota%` de la prueba de dato
sensible. El patrón es deliberadamente amplio y debe seguir cazando `observaciones` y cualquier
columna de texto futura; lo que no debe cazar es un **recuento**. Se declaró la excepción una a una y
con su razón —contar no es leer: saber que un caso tiene tres notas no revela ninguna—, más una
prueba que comprueba el **tipo** de cada excepción, para que meter `observaciones` en esa lista para
acallar un fallo no funcione.

### Verificación

`dags/`: **201 verdes**. `apps/informes_tacticos`: **137 verdes**.

### Lo que queda de US3

T049/T050 (poblar las ocho métricas), T052/T053 (cargador y flujo de `hecho_evidencia`) y las diez
consultas con sus pruebas.

⚠️ **Un obstáculo encontrado y no resuelto**: `hecho_evidencia` necesita `sk_unidad` por atribución
histórica, y **ninguna de las dos fuentes trae unidad** — `Dim_EvidenciaFoto` y `Dim_NotaAccidente`
solo traen `idusuario`, que está excluido por la decisión D6. Habrá que derivar la unidad del despacho
confirmado del caso. Y `Dim_NotaAccidente` **no tiene `fecha_sincronizacion`** en absoluto, así que la
latencia de las notas es genuinamente ausente: no se puede fabricar.

---

## 2026-08-16 — Emergencias compuestos: fase 4 (US2), despacho y seguimiento

Alcance: `dags/lib/consultas/emergencias/` (10 consultas nuevas), `dags/tests/` (5 ficheros nuevos,
`almacen.py` ampliado con despachos y posiciones), `backend/apps/informes_tacticos/` (servicio con
parámetros por informe, vista con notas, 4 endpoints publicados).

**Cuatro endpoints nuevos**: ratio demanda/capacidad y pérdida de señal (migrados, corrigen defectos),
primer intento y desviación de llegada (nuevos). Seis consultas más se añaden **sin publicar
endpoint**: existen solo para contrastar los informes que ya funcionan.

### El defecto de CU-T08: el histórico se reescribe solo

El endpoint anterior cuenta la flota con `activo = true`, es decir **la de hoy**. Aplicado a un
período pasado responde a una pregunta que nadie hizo: «¿cuántos casos hubo entonces por cada unidad
que tenemos ahora?».

El síntoma es el peor de su clase: el informe de marzo consultado en marzo y el **mismo** informe de
marzo consultado en agosto dan cifras distintas, sin que en marzo haya pasado nada. Nada falla, nada
avisa, y las dos cifras son plausibles.

La consulta nueva saca la capacidad de las **versiones de unidad cuya vigencia solapa el mes medido**.
`valido_hasta IS NULL` se trata como «sigue vigente» y no como «caducó» —confundirlo dejaría fuera
justamente a las unidades activas— y se cuentan unidades y no versiones, porque una unidad que cambió
de nombre a mitad de mes sigue siendo una unidad.

T041 lo comprueba dando de baja una unidad **después** del mes medido: ese mes no puede moverse. Con
`es_vigente = 1` la prueba falla, verificado por mutación.

### La cuarta comprobación de T043 no comprobaba lo que decía

«Los despachos sin llegada quedan fuera de la referencia» resultó no ser falsable: `median()` ignora
los nulos por sí solo, así que colarlos en la ventana no desplaza nada. Al mutar la consulta la prueba
seguía verde.

El daño real estaba en otro sitio: en **`llegadas_comparables`**, el número que decide si hay muestra
suficiente. Veinte rechazos y dos llegadas darían una muestra de veintidós, se superaría el mínimo, y
se publicaría como norma la mediana de **dos** llegadas. No es una referencia desplazada: es una
referencia que no debería existir, presentada como sólida. La prueba se reescribió sobre ese punto.

Las otras tres —mediana y no promedio, ventana anterior, muestra insuficiente ⇒ ausente y no cero— sí
fallaban al mutar desde el principio.

### Un fallo de ClickHouse cuyo mensaje apunta a otra parte

En `ot23_desviacion_llegada`, la columna interna **no puede llamarse igual que el alias de salida**.
Si coinciden, el nombre dentro de `medianIf(segundos_referencia, …)` se resuelve al propio alias —que
ya es una agregación— y falla con `ILLEGAL_AGGREGATION`, un error que habla de agregaciones anidadas y
no menciona el alias por ninguna parte.

Antes de dar con ello se probaron subconsultas en vez de `WITH`, un nivel extra de `SELECT` y el
analizador nuevo. Ninguno era la causa, y el nivel extra llegó a quedarse en el fichero pareciendo la
solución; se retiró al comprobar que sin él la consulta funciona igual. Se descartó a propósito la
otra salida que también funcionaba —un `LIMIT` grande en la subconsulta—: meter un tope de filas en
una consulta de informe es exactamente el defecto que este mismo módulo corrige en la pérdida de
señal.

### Distinciones que los informes anteriores borraban

**Rechazado no es vencido.** Un rechazo tiene una persona y un motivo detrás, y la conversación es
sobre criterios de aceptación; un vencimiento significa que nadie contestó, y la conversación es sobre
turnos y sobre el aparato. El informe anterior los sumaba en un «no atendidos» que no dice qué
arreglar — y que además hace parecer ausente a una unidad con muchos rechazos y ningún vencimiento,
que es la que siempre responde.

**`en_curso` no es un fracaso.** Es un despacho sin desenlace. Contarlo como perdido convierte cada
consulta hecha a media tarde en un informe pesimista que mejora solo al día siguiente. Los cinco
desenlaces se publican como cinco columnas y no agrupando por `resultado`: agrupando, un desenlace sin
casos **desaparecería de la respuesta**, y un cero que falta se lee como un dato que no existe en vez
de como lo que es.

**`Escalado_zona` es un origen propio.** Repartirlo entre automático y manual borraría la única señal
de que la cobertura local no daba abasto.

### La pérdida de señal ya no puede truncarse

La agregación ocurre en el servidor y devuelve una fila por proveedor, así que no hay nada que
truncar. T042 comprueba que el denominador coincide con el origen sobre los datos reales —el flujo
viejo habría dado 10 000— y que el origen supera esa cifra, porque si no la prueba no distinguiría un
truncamiento de un período tranquilo.

### Verificación

`dags/`: **198 verdes**. `apps/informes_tacticos`: **127 verdes**. Los cuatro endpoints comprobados
por HTTP contra el stack: `200` con la nota de FR-032 en la desviación, `400` con parámetros fuera de
rango, `404` para los informes que se vigilan y no se publican.

---

## 2026-08-16 — Emergencias compuestos: fase 3 (US1) completa

Alcance: `dags/tests/` (`almacen.py` ampliado, `test_ot21_distribuciones.py`,
`test_ot21_descarte_fusion.py`, `test_ot21_ranking.py` nuevos),
`dags/lib/consultas/emergencias/ot21_ranking_ubicaciones.sql`,
`backend/apps/informes_tacticos/` (servicio, vista, urls, dos ficheros de prueba nuevos).

### Un error de alcance corregido: seis publicados donde el contrato publica uno

El registro exponía como endpoint los **seis** informes OT21. El contrato publica **uno**: solo la
completitud se migra, porque el endpoint que la sirve hoy está mal. Los otros cinco ya los sirve
`informes-tacticos-agregados` **correctamente**, y sus consultas existen aquí para **contrastarlos**.

Publicarlos habría creado dos endpoints respondiendo lo mismo desde almacenes distintos. Mientras
coincidan nadie lo nota; el día que difieran hay dos cifras verdaderas y ninguna forma de decidir cuál
rige — que es exactamente la situación que la prueba de contraste existe para vigilar.

Se separó **`CATALOGO`** (lo que se puede calcular) de **`PUBLICADOS`** (lo que se sirve), con una
prueba parametrizada que comprueba que cada informe no publicado devuelve `404` por HTTP. La ruta
perdió además el segmento `compuestos/` y el `meta` propio que se habían desviado del contrato: para
quien consume esto es «el informe de Emergencias», y que por dentro salga del modelo analítico no es
asunto de la URL.

### Defecto encontrado por T027: el LEFT JOIN no rellena con nulo

En ClickHouse un `LEFT JOIN` sin coincidencia rellena con el **valor por defecto del tipo**, no con
`NULL`. Una calle que no está en el catálogo geográfico volvía como **cadena vacía**, y
`coalesce(calle, 'Desconocido')` no disparaba porque `''` no es nulo.

El síntoma es una fila del ranking con la calle en blanco: parece un fallo de maquetación y significa
que la ubicación no se pudo resolver. Corregido con `nullIf(calle, '')`.

Es la misma familia que el resto de los defectos de este módulo —ausencia confundida con vacío, con
cero o con centinela— y otra vez no habría fallado nada: la consulta funciona, devuelve filas, y solo
una de ellas queda muda.

### La prueba de contraste compara invariantes, no filas

Los dos caminos **agrupan por claves distintas a propósito**: el endpoint actual reparte por calle y
las consultas del catálogo por condado, porque el informe se pidió por zona y una calle no es una
zona. Comparar fila a fila habría medido esa diferencia de forma, no una de cálculo, y habría fallado
siempre sin señalar nada.

Se comparan los totales del período y los conteos por categoría — lo que ambos afirman sobre el mismo
conjunto, y lo que un tablero suma. Verificado falsable alterando una consulta del catálogo.

⚠️ **Limitación registrada**: `descarte-fusion` solo se puede contrastar **día a día**, porque el
endpoint actual publica las tasas **sin su denominador** y sin él las tasas diarias no se recomponen
en una del período —promediarlas daría un número distinto y plausible—. Es precisamente lo que el
contrato nuevo prohíbe: «todo porcentaje viene con su denominador, para que la fracción sea
comprobable». Este informe es la demostración de por qué esa regla está ahí.

### La completitud queda excluida del contraste, y esa exclusión es la tesis

Las demás pruebas exigen que las dos cifras **coincidan**; esta exige lo contrario. El endpoint actual
devuelve `1.0` **todos los días de un año entero** —se comprobó contra el stack—, y eso no es calidad
perfecta: es que la pregunta no se está haciendo.

La prueba no comprueba que hoy difieran, porque hoy coinciden: no hay ningún caso incompleto, así que
100 % es la respuesta correcta. Comprueba que el endpoint actual **no puede** dar otra cosa. Que la
consulta nueva sí puede es lo que demuestra T024, fabricando el caso que los datos reales no traen.

### Verificación

`dags/`: **171 verdes**. `apps/informes_tacticos`: **120 verdes**. 27 pruebas nuevas en esta fase.
Los ayudantes de casos de prueba se centralizaron en `dags/tests/almacen.py` para que un cambio en el
esquema del hecho no haya que perseguirlo por cuatro ficheros — el que se olvidara seguiría pasando
con datos que ya no existen.

---

## 2026-08-16 — Emergencias compuestos: catálogo de consultas y capa base (fases 1 y 2)

Alcance: `dags/lib/consultas/` (cargador + 6 consultas OT21), `dags/tests/test_catalogo_consultas.py`
(nuevo), `backend/core/clickhouse/client.py` (parámetros y ajustes),
`backend/core/repositories/informes_tacticos/` (`modelo_repository.py`, `catalogo_consultas.py`,
nuevos), `backend/apps/informes_tacticos/` (servicio, vista, permisos, período, urls, envelope),
`backend/config/settings.py`, `docker/accidentes.yml`.

### Un catálogo de consultas, no un repositorio por informe

Un informe compuesto es ahora **un fichero SQL** en `dags/lib/consultas/emergencias/`, junto al
modelo que consulta. El backend lo **lee**; el único escritor del almacén sigue siendo Airflow. Es lo
contrario del diseño anterior, donde cada informe traía su repositorio con la consulta incrustada en
Python y dos informes que medían lo mismo podían calcularlo distinto sin que nada lo delatara.

El contenedor de Django monta `../dags/lib/consultas` en `/opt/consultas:ro` (`CONSULTAS_DIR`). Se
montó en vez de copiarse: una copia habría divergido, que es el fallo que este módulo sustituye.

### Las reglas del catálogo se comprueban sobre el texto, no sobre el resultado

Seis reglas, todas ellas fallos que **la ejecución no delata**: sin `FINAL` sobre un hecho acumulado
la consulta funciona y devuelve cifras infladas *solo a veces*; con una columna sensible funciona y
publica el dato; sin `ORDER BY` funciona y devuelve las filas en orden arbitrario.

Las seis se verificaron **falsables por mutación**. Dos hallazgos del proceso:

* El `FINAL` obligatorio no se puede comprobar buscando la cadena `"hecho_accidente FINAL"`: el alias
  va en medio (`hecho_accidente AS h FINAL`). La comprobación literal daba por incumplida una
  consulta correcta, y aceptar «cualquier alias» habría dado por cumplida una que no lo lleva.
* El `ORDER BY` se comprueba **anclado a principio de línea**. Buscarlo en cualquier parte daba por
  ordenada una consulta cuyo único `ORDER BY` está dentro de una función de ventana — que no ordena
  nada de lo que sale.

### Dos defectos encontrados ejecutando contra ClickHouse de verdad

**Los conteos llegaban como cadenas.** `count()` es `UInt64` y ClickHouse entrecomilla los enteros de
64 bits en JSON por defecto: un conteo de 1664 llegaba como `"1664"`. No falla en ninguna parte —una
pantalla pinta igual un número que su texto— y solo se nota cuando algo los **suma**, porque en
JavaScript sumar dos cadenas las concatena: 1664 + 1527 daría `"16641527"` en vez de 3191. Se corrige
con `output_format_json_quote_64bit_integers=0` en todas las consultas del catálogo, y la prueba que
lo vigila va **contra ClickHouse real**: un cliente de mentira devuelve el tipo que decida quien
escribe la prueba.

**Una guardia que defendía de algo que no pasa.** Se escribió una traducción de `NaN`/`Inf` a nulo
razonando que ClickHouse los emitiría literalmente en JSON. Se comprobó por la ruta real —HTTP desde
el contenedor de Django— y **es falso**: `SELECT 1/0, 0/0, NULL` devuelve `{"inf":null,"nan":null,
"nulo":null}`. La guardia se retiró en vez de dejarse con una justificación desmentida.

### Lo que se retiró por ser resto del módulo anterior

`InformesTacticosCompuestosPermission` e `informe_compuesto_response` habían quedado **sin ninguna
referencia** tras la decisión #20, y codificaban el diseño viejo: el rol `Administrador` como único
acceso, y un `meta.materializado` que existía porque cada informe tenía su tabla y su DAG. En el
modelo esa distinción no existe —un período sin filas es un período sin datos— así que
`materializado` habría sido siempre `True`: un campo que no informa de nada pero que el frontend
seguiría mirando para decidir si pinta.

### Detalles de la capa base

* **Solo lectura impuesta por el servidor**, no por disciplina: `readonly=1` en toda consulta, más una
  prueba de que ningún fichero del catálogo contiene `INSERT`/`ALTER`/`DROP`/`TRUNCATE`/`CREATE`/
  `OPTIMIZE`. Las dos hacen falta: el ajuste protege de lo que se añada mañana, la prueba de lo que ya
  está escrito.
* **El rango viaja como parámetro con tipo** (`{desde:Date}` → `param_desde`), ligado por el servidor.
  Con interpolación, un valor que contenga SQL **es** SQL.
* **Período por defecto de 30 días**, `[hoy-29, hoy]` y no `[hoy-30, hoy]`: restar 30 daría 31 días
  contando ambos extremos. No falla ni se ve, pero dos períodos «de 30 días» consecutivos
  compartirían una jornada y las sumas no cuadrarían.
* **Una vista parametrizada**, no 26 clases. El nombre del informe llega por la URL pero se busca en
  un **registro explícito**; nunca se convierte en una ruta de fichero, que haría de la URL una forma
  de leer el disco.
* **Permisos**: Director de Operaciones (autoridad del departamento, sin acotamiento por titularidad)
  y Administrador (con el suyo). El `Operador` ve los listados simples y **no** estos: un listado es
  su trabajo del día, un compuesto es una lectura de gestión sobre el trabajo de todos. La exención de
  acotamiento **no** alcanza al dato sensible, que sigue excluido para todos los cargos.

### Verificación

`dags/`: **12 verdes** (catálogo), las seis reglas confirmadas falsables por mutación.
Backend: **3612 verdes y 5 rojas** en la suite completa; **90 verdes** en `apps/informes_tacticos`,
incluidas 11 del repositorio; tres mutaciones (interpolar el rango, quitar `readonly`, rellenar nulos
con cero) confirmadas como detectadas.

⚠️ **Las 5 rojas son preexistentes y no de este cambio**: todas en
`tests/regression/test_pinot_client_limit.py`, que **pasa aislado** y falla dentro de la suite
completa — contaminación por orden entre pruebas. Se comprobó corriendo la suite **sin** el fichero
nuevo de este módulo: fallan las mismas 5. Queda anotado como defecto aparte.

También hay **8 errores de recolección y 13 rojas al correr la suite dentro del contenedor** que no
aparecen en el host: la imagen del backend no lleva PyYAML ni los ficheros de la raíz del repositorio
(`database/esquemas.json`), que esas pruebas necesitan. Es un hueco del entorno del contenedor, no del
código; la suite de referencia sigue siendo la del host.
Endpoint por HTTP contra el stack levantado: `200` para Director de Operaciones y Administrador,
`403` para Operador y Cliente, `401` sin credencial, `404` con nombre fuera del registro (enumerando
los publicados), `400` con `top` fuera de rango.

### T024: la prueba que demuestra que el defecto quedó corregido

`dags/tests/test_ot21_completitud.py` (6 pruebas). Escribe casos incompletos en la partición `209912`
—muy posterior a cualquier dato real— y la descarta al terminar; se verificó que las 4252 filas reales
quedan intactas.

**Por qué hacía falta fabricar el caso.** Con los datos de hoy el endpoint defectuoso **acierta por
casualidad**: no hay ningún caso al que le falte severidad o condado, así que la respuesta correcta
*es* 100 %. Comparar las dos cifras no demuestra nada porque coinciden. El defecto está latente, y la
única forma de exhibirlo es construir el caso que lo destapa.

Se cubren los dos campos críticos por separado, el caso al que le faltan los dos (cuenta una vez, no
dos), el 100 % legítimo —una consulta que devolviera siempre menos de 1 pasaría las demás pruebas y
estaría igual de rota, dando una alarma permanente que nadie tardaría en ignorar— y el período vacío,
que da **nulo y no cero**.

**Una prueba no prevista resultó necesaria**: que una calle no resoluble cuente como incompleto. La
consulta juzga la ubicación por `condado` y no por `idcalle` —un caso puede traer una calle que no
está en el catálogo geográfico—, pero en todos los demás casos del fichero los dos campos van juntos,
así que una consulta que mirara `idcalle` pasaba igual. Era la única distinción que el encabezado del
SQL declaraba y las pruebas no comprobaban.

**Cuatro mutaciones confirmadas**: contar todo como completo (el defecto heredado), mirar `idcalle` en
vez de `condado`, ignorar la severidad, y devolver `0` en vez de nulo con denominador cero.

### El defecto de los enteros de 64 bits estaba también en el cliente de los DAGs

Lo destapó T024: los conteos llegaban como `"2"` en vez de `2`. Se corrigió igual que en el backend.
Que los dos clientes coincidan no es cosmético — la prueba de contraste (T028) compara la cifra del
endpoint con la de la consulta, y `"2" != 2` la haría fallar por una diferencia de **serialización**
en vez de una de cálculo, que es la clase de ruido que enseña a desconfiar de la prueba y no del dato.

`query_clickhouse` acepta además parámetros con tipo, para poder ejecutar las consultas del catálogo
**tal como se publican**: si hubiera que interpolarlas para correrlas, la prueba estaría comprobando
una consulta distinta de la que sirve el endpoint.

---

## 2026-08-15 — Decisión #20 resuelta: retirados los tres informes compuestos del diseño anterior

Alcance: `backend/apps/informes_tacticos/` (3 vistas, 3 rutas, 1 servicio, 3 repositorios y 4
ficheros de prueba **retirados**), `frontend/.../emergencias/` (3 tarjetas, 3 métodos y 3 tipos
retirados), `dags/` (3 DAGs, 3 módulos de tareas, 3 de pruebas, `dag_backfill` y 3 definiciones de
tabla retirados; 2 DAGs transversales **repuntados al modelo**),
`decisiones-pendientes.md` (#20 cerrada), `modelo-analitico/tasks.md` (T048 desbloqueada).

**Se eligió la opción B**: los endpoints se retiran junto con el módulo ya marcado como sustituido, y
esos informes se rehacen cuando se especifiquen los compuestos sobre el modelo.

### Por qué no era limpieza

Los tres endpoints estaban **vivos y pintados en los workpanels**, y el modelo analítico ya había
demostrado (T047) que dos de los tres publicaban cifras truncadas:

| Informe | Publicaba | Real | Veía |
|---|---|---|---|
| Pérdida de señal | 714 huecos | **3 942** | **16,9 %** |
| Rendimiento — rechazos | 344 | **661** | **51 %** |

No calculaban distinto: **dos consultas viejas no llevaban `LIMIT` explícito**, recibían el tope por
defecto de 10 000 filas y truncaban en silencio. Corriendo la lógica vieja sobre datos completos
salían exactamente las cifras del modelo.

Retirarlos deja tres huecos declarados en las pantallas; dejarlos habría seguido publicando números
equivocados sin ningún aviso.

### Lo que se repuntó en vez de borrarse

`dag_validacion_calidad` y `dag_mantenimiento_bd` apuntaban a las tres tablas retiradas. Borrarlos
habría quitado la única validación de calidad del almacén; dejarlos apuntando a tablas inexistentes
habría sido **peor todavía**: un DAG de calidad que valida lo que ya no está **no falla, informa de
que todo va bien**.

Ahora vigilan y optimizan los **cuatro hechos del modelo**. Y en el modelo `OPTIMIZE FINAL` importa
más que antes: sus hechos son `ReplacingMergeTree(version)`, y esa operación es la que fusiona las
versiones que si no habría que resolver con `FINAL` en cada consulta.

`dag_backfill` sí se retiró entero: existía **solo** para reprocesar esas tres tablas, y en el modelo
reprocesar es volver a correr el DAG.

### Lo que NO se hizo, y es deliberado

⚠️ **Las tres tablas de ClickHouse no se borraron.** Ya no se refrescan ni se recrean —su DDL se
retiró—, pero sus filas siguen ahí. Destruir datos no es reversible y no formaba parte de la
decisión: queda como un `DROP TABLE` manual cuando se quiera.

La prueba de la tesis del modelo (`test_informe_sin_flujo_propio`) las sigue restando del conjunto de
tablas presentes, con el comentario de por qué.

### Verificación

Backend: **3590 verdes** (14 menos: las pruebas de lo retirado). Frontend: **847 verdes**.
`dags/`: **137 verdes** en el contenedor de Airflow, sin errores de importación — es lo que comprueba
que ningún DAG quedó referenciando lo que ya no existe.

---

## 2026-08-15 — Frontend de Ventas, Suscripciones y Red Operativa: la serie completa, y dos defectos más

Alcance: `frontend/src/app/modules/{ventas-crm,suscripciones,red-operativa}/informes/`
(3 catálogos, 7 guards, 6 páginas, 3 rutas), `shared/informes/` (**`meta.alcance` añadido**),
`app.routes.ts`, `nav-links.ts`, 5 ficheros de prueba (44 nuevas),
`contrato-informes-simples-frontend.md` (§2.4),
y en backend: `informes_nutricion_repository.py`, su doble de pruebas, su fixture y una prueba nueva.

**Con esto los 32 listados tácticos tienen pantalla.** Los tres departamentos restantes no traían
ejes ni exclusiones nuevas, así que fueron trabajo de catálogo y guards — salvo por dos cosas que sí
aparecieron.

### `meta.alcance` no llegaba a la pantalla, y este era el departamento donde importa

La capa compartida leía `meta.alcance` del envelope y **no lo mostraba**. Lo emite un solo listado —la
composición de flota— y por la razón de más consecuencia de la serie: `dado_de_alta` significa que la
unidad **existe**, no que pueda acudir.

Perderlo devolvía el riesgo entero que el backend declaró para evitarlo: quien leyera el listado como
cobertura decidiría sobre unidades fuera de servicio, ocupadas o ya en camino a otro accidente.

Añadido al componente con dos reglas propias, ahora en el contrato (§2.4):

* **se muestra siempre que venga**, también con la lista vacía — advierte de una lectura equivocada
  del listado, no de un recorte de los datos;
* **un valor desconocido no se pinta crudo**: es un identificador, no un texto para el usuario.

### Un `500` en producción: el centinela que ordenaba después de los dígitos

`demos-activas` devolvía **`500`** contra el stack real.

`Dim_Prospecto.demo_expiracion` es texto con formatos mixtos —la decisión #29—, así que la consulta
filtra por **prefijo** `YYYY-MM-DD`, que es lo único seguro. Pero el valor centinela es la cadena
`'null'`, y comparando texto **`'null' >= '2026-08-16'` es cierto**: cualquier letra ordena después de
cualquier dígito. La fila colada llegaba sin fecha utilizable y reventaba al componer el cursor de la
página siguiente.

Es la **regla 1 de Pinot** del contrato común incumplida —«NULL no existe: se comparan centinelas»— en
el sitio menos evidente: un filtro de rango sobre texto.

**Ninguna prueba lo detectó porque el fixture sembraba `None`**, no la cadena `'null'` que Pinot
devuelve. Es la tercera vez en esta serie que un doble inventado esconde un defecto real, y las tres
lo destapó el recorrido en navegador.

Corregido en el repositorio, en el doble de `conftest.py` —que tampoco reproducía el centinela— y en
el fixture, más tres pruebas nuevas.

### Las distinciones que los guards protegen

Cada departamento parte sus listados en más de un guard, y ninguno por simetría:

* **Ventas:** `reasignaciones` es supervisión pura — el reparto de cartera es decisión de jefatura,
  no herramienta del gerente cuya cartera se reparte.
* **Suscripciones:** dos autoridades distintas. El catálogo y los precios son de **Estrategia**; el
  resultado económico, de **Finanzas**. Un guard único daría a cada director el área del otro.
* **Red Operativa:** tres grupos. Una región **no pertenece a ninguna empresa de flota**, así que los
  proveedores quedan fuera aunque sí vean su flota; y las validaciones son solo del Tecnológico,
  porque el detalle de por qué se rechaza una región no le sirve a quien decide dónde crecer.

En los tres, el índice ofrece **solo** lo que el guard permite: un enlace que el guard rechaza no es
una fuga, pero sí una interfaz que promete lo que no cumple.

### Verificación

Frontend: **847 verdes** (803 previas + 44 nuevas). Backend: **3605 verdes**. Los 12 endpoints
responden `200` contra el stack reconstruido, y la advertencia de flota se comprobó en pantalla.

---

## 2026-08-15 — Frontend de Emergencias: cerrado el tercer valor de `acotado_a`, y un defecto que solo se vio en pantalla

Alcance: `specs/002-tactico/Emergencias/informes-tacticos-simples/frontend/` (spec, tasks),
`frontend/src/app/modules/emergencias/informes/` (catálogo, 2 guards, 2 páginas, rutas),
`app.routes.ts`, `nav-links.ts`, 3 ficheros de prueba (44 pruebas),
y en backend: `informes_casos_service.py`, su fixture, su prueba y el contrato OpenAPI.

**Con este módulo los tres valores de `acotado_a` están validados de punta a punta**: `todos`
(Cuentas y Clientes), `propios` (Soporte) y ahora `zonas_contratadas`.

### Lo verificado en navegador, con dos roles sobre los mismos datos

| | |
|---|---|
| Rol **Operador** → `todos` | 50 filas de varios condados, **sin aviso** |
| Rol **Cliente** → `zonas_contratadas` | 3 filas de **un solo condado**, con su aviso propio |
| El aviso | **no** dice que los accidentes sean del cliente: son hechos de terceros ocurridos donde contrató cobertura |
| Situación impuesta | `meta.filtros.situacion = cerrado` — la emergencia en curso no es información del cliente |
| Coordenadas | **ninguna**, ni en la respuesta ni en pantalla |
| Columna «Estado» | **ninguna**: `activo`, `hora_fin` y `duplicado_de` van por separado |
| Guard | el Cliente queda fuera de despachos, evidencia y cierres |

### El defecto: `hora_fin` salía como `1786625595899`

`Fact_Accidente.horafin` es una columna `STRING`, pero **guarda epoch-ms escrito como texto** — lo
escriben `cerrar_caso_service` y `cancelar_caso_service` con el reloj del sistema. El backend la
devolvía **verbatim** mientras normalizaba a ISO todas las demás marcas de tiempo de la API. En
pantalla eso es un número ilegible que además no se puede ordenar ni comparar como fecha.

**Ni las pruebas de backend ni las de frontend lo detectaron, porque el fixture lo inventaba.** Yo
había sembrado `horafin="09:30"`, un formato que no existe en producción, y la prueba pasaba
comparando contra un dato falso. Peor: sobre esa invención llegué a «corregir» el contrato quitándole
el `format: date-time`, que en realidad era correcto.

Corregido en los cuatro sitios: el servicio normaliza a ISO tolerando que el valor no sea numérico,
el fixture usa epoch-ms como los escritores reales, la prueba afirma el **formato** en vez de un
literal inventado, y el contrato explica que la columna de origen es `STRING` y por qué.

> **Lección, y es la segunda vez que aparece.** Un fixture inventado no es una prueba: es una
> afirmación sobre datos que nadie produce. El recorrido en navegador lo destapó, igual que destapó
> `controlClass` en el piloto. Las dos veces, lo que falló primero fue una suposición mía sobre la
> forma del dato — no el código que la consumía.

### La exclusión constitucional, protegida donde se rompería

Hay una prueba que recorre **el catálogo de columnas y filtros** buscando coordenadas e identidad de
implicados. No es redundante con la del backend: el catálogo del frontend es justo el sitio donde
alguien añadiría una columna «para el mapa», y ahí el backend no puede impedirlo.

La spec declara además que **este módulo no dibuja mapas**, para que la pregunta «¿y si pedimos las
coordenadas?» no se abra por el nombre del departamento.

### Verificación

Suite completa del frontend: **803 verdes** (759 previas + 44 nuevas). Backend: `apps/accidentes` y
`apps/seguimiento`, 463 verdes tras la corrección.

---

## 2026-08-15 — Frontend de Soporte al Cliente: `acotado_a` validado de punta a punta

Alcance: `specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/frontend/` (spec, tasks),
`frontend/src/app/modules/soporte-cliente/informes/` (catálogo, 2 guards, 2 páginas, rutas),
`app.routes.ts`, `nav-links.ts`, 2 ficheros de prueba (18 pruebas),
y en backend: el `enum` de `estado` en el contrato OpenAPI **y su prueba de conformidad**.

**Se eligió este departamento para cerrar el hueco del piloto.** Cuentas y Clientes validó todo menos
el aviso de alcance, porque sus ocho listados son globales. Aquí `tickets` devuelve `propios` a un
reportador y `todos` a quien atiende, así que la garantía más delicada de la capa compartida se
ejercita contra el backend real.

### Lo verificado en navegador, con dos roles sobre los mismos datos

| | |
|---|---|
| Rol **Soporte** → `todos` | 14 filas de varias cuentas, **sin aviso** |
| Rol **Cliente** → `propios` | 12 filas de **una sola cuenta**, con el aviso |
| **Estado vacío acotado** | «No hay tickets con esos criterios. **No hay resultados entre tus registros.**» |
| **`403` real** | un Cliente sin cuenta resuelta ve el mensaje del backend, no una lista vacía |
| Guard de escalados | el Cliente queda fuera; el índice ni se lo ofrece |

El estado vacío es lo que más importa: es justo cuando no hay filas cuando «no hay» y «no hay de los
tuyos» se leen igual, y es la ambigüedad que `acotado_a` existe para evitar. Ahora está cerrada en la
pantalla, no solo en la respuesta.

### Un hueco del contrato de backend, cerrado de paso

El OpenAPI declaraba `estado` como **texto libre** y el backend **sí** lo valida contra las
constantes del dominio. Sin el `enum` declarado, el frontend no podía ofrecer un desplegable sin
copiar de un sitio que nadie comprueba — y un `400` evitable acabaría llegando al usuario. Añadido al
contrato, con la prueba de conformidad extendida para que no pueda divergir. Es la tercera vez que
este mismo patrón aparece en el departamento.

### Una regla de navegación que no se rompió

Añadir `PartnerIntegracion` al enlace del sidebar puso en rojo una prueba existente: **FR-UI-033** —la
consola de Partners y su portal no se fusionan, y ningún rol descubre la existencia del otro
departamento—. No se actualizó la prueba para que pasara: **se quitó el enlace**.

El backend sí le permite el listado, así que la ruta le responde si llega a ella; lo que no tiene es
un enlace. Queda anotado como decisión de producto en `tasks.md`, no resuelta por conveniencia.

### Verificación

Suite completa del frontend: **759 verdes** (741 previas + 18 nuevas). Backend: la prueba de
conformidad del contrato de Soporte sigue verde con el `enum` nuevo.

---

## 2026-08-15 — Piloto de frontend: los 8 listados de Cuentas y Clientes, verificados en navegador

Alcance: `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/frontend/`
(spec, plan, tasks — **nuevos**),
`frontend/src/app/modules/cuentas-clientes/informes/` (**nuevo**: catálogo, 2 guards, 2 páginas,
rutas), `frontend/src/app/shared/informes/` (**3 correcciones**),
`app.routes.ts`, `nav-links.ts`, 3 ficheros de prueba (56 pruebas),
`.claude/launch.json` y `frontend/proxy.local.conf.json`.

**La hipótesis de la capa compartida se confirma.** Las ocho pantallas salen de **un catálogo de
definiciones y una sola página parametrizada**: ninguna implementa tabla, paginación ni manejo de
error. Añadir un listado es añadir una entrada al catálogo.

### La capa compartida necesitó tres cambios, y eso es el resultado del piloto

Se construyó antes que cualquier pantalla precisamente para descubrir esto. Los tres se corrigieron
**en `shared/informes`**, no en una página:

**1. Faltaba el formato `lista`.** Tres listados devuelven arreglos —`roles`, `roles_servidor`,
`roles_negocio`— y se pintaban con las comas pegadas de `String(['a','b'])`. De paso quedó fijado que
**un arreglo vacío es ausencia**: quien no tiene roles no tiene «cero roles», no los tiene.

**2. `controlClass` no existía.** Importé la constante de estilo y nunca la asigné al componente.
**Las 42 pruebas de Karma pasaron igual** —compila en JIT, con comprobación de plantillas más laxa— y
lo encontró el compilador AOT al arrancar el servidor de desarrollo. Es la demostración concreta de
por qué el recorrido en navegador no es opcional, y de por qué avisé al entregar la capa de que sus
plantillas aún no estaban type-checkeadas.

**3. El pipe de números fijaba el locale `'es'`**, que exige registrar sus datos; sin ellos **lanza al
renderizar**, o sea que la tabla se cae al pintar un número. Ahora usa el `LOCALE_ID` de la
aplicación.

### Dos decisiones propias del piloto

**Dos guards, no uno.** El backend declara Administrador en siete listados y Administrador o Director
Tecnológico en `accesos-tecnicos`. Un guard único con la unión de roles le daría los siete al Director
Tecnológico — la contradicción con el §5.1 del SRS que `acceso-tactico.md` marca con ⚠️. Hay una
prueba por cada mitad, y se verificó en navegador.

**El índice se genera del mismo catálogo** que las páginas y filtra por rol: al Director Tecnológico
le ofrece **solo** el suyo. Ofrecerle enlaces que su guard rechaza no sería una fuga —el guard sigue
cerrando— pero sí una interfaz que promete lo que no cumple.

### El vacío que no es un defecto

`transferencias-propiedad` devuelve cero filas **siempre**, porque nadie escribe
`Fact_HistorialTransferenciaPropiedad` (decisión #28). Su estado vacío lo dice: *«la fuente de este
informe aún no se alimenta… No es un fallo de la pantalla»*. Un «no hay transferencias» genérico
habría hecho que alguien buscara el defecto en el código.

### Verificado en navegador contra el stack real

Requirió **reconstruir los contenedores**: el de Django corría una imagen anterior a *todos* los
informes tácticos —decisión #26—, así que las 32 rutas respondían `404`. Reconstruidos `django` y
`frontend`, se recorrieron las ocho pantallas:

| Comprobación | Resultado |
|---|---|
| Las ocho con datos reales | ✅ |
| **`400` real** (`dias_minimo=-5`) | ✅ muestra el `detail` del backend, **sin** «Reintentar» y **sin** tabla vacía |
| Director Tecnológico en los siete | ✅ redirigido a `access-denied` |
| Director Tecnológico en accesos técnicos | ✅ entra |
| Índice filtrado por rol | ✅ le ofrece solo el suyo |
| Valores ausentes | ✅ guion, nunca `0` ni fecha de época |
| Vacío de transferencias | ✅ explica la #28 |
| Rango de fechas | ✅ solo en transferencias |
| Recuento total | ✅ no aparece |

### Lo que este piloto NO validó, y queda declarado

**`meta.acotado_a`.** Ninguno de los ocho listados de este departamento acota —son de Administrador y
globales—, así que la garantía más delicada de la capa **no se ejercitó de punta a punta**. La cubren
las pruebas de componente, que no es lo mismo. Se cierra con el siguiente departamento acotado:
Soporte (`propios`) o Emergencias (`zonas_contratadas`).

### Verificación

Suite completa del frontend: **741 verdes** (685 previas + 56 nuevas). Build de desarrollo limpio.

---

## 2026-08-15 — Capa compartida de frontend para los listados tácticos simples

Alcance: `specs/002-tactico/contrato-informes-simples-frontend.md` (**nuevo**),
`frontend/src/app/shared/informes/` (**nuevo**: tipos, servicio, store, dos componentes),
3 ficheros de prueba (42 pruebas).

**Ninguna página la usa todavía.** Es deliberado: se construye la capa antes del piloto, igual que
`core/informes/` se construyó antes del piloto de backend. Los 32 endpoints comparten cursor,
envelope, filtros y forma de error; hacerlos departamento por departamento habría producido siete
tablas divergentes, y la primera que se despistara habría abierto el hueco.

### Las tres cosas que la capa existe para no perder

Son cosas que el backend garantiza y que **una pantalla puede tirar a la basura sin que nada falle**,
que es lo que las hace peligrosas.

**1. `meta.acotado_a` llega a la pantalla, y sobre todo al estado vacío.** El backend lo emite para
que un resultado vacío no sea ambiguo: «no hubo accidentes graves» y «no hubo accidentes graves *en
mis zonas*» se leen igual sin él. El componente lo muestra como aviso cuando hay filas y **lo
incorpora al texto del estado vacío** cuando no las hay — que es justo cuando la ambigüedad muerde.

Toma tres valores, no dos. `todos` **no produce aviso**: un cartel permanente diciendo «lo ves todo»
sería ruido, y enseñaría a ignorar la franja donde a veces sí hay una advertencia real. Y
`zonas_contratadas` tiene texto propio: los accidentes ocurridos en una zona contratada **no
pertenecen al cliente**, así que un «tus accidentes» afirmaría algo falso sobre datos de
siniestralidad ajenos. Hay una prueba que lo exige.

**2. Un `400` se muestra como error legible, nunca como tabla vacía.** El backend rechaza en vez de
recortar, y su `detail` nombra los valores válidos. Capturarlo para pintar una tabla vacía
reintroduciría el fallo silencioso que la regla evita: el consumidor leería «no hay resultados» donde
el sistema dijo «tu petición está mal». El `detail` viaja **tal cual**; sustituirlo por un «Ha
ocurrido un error» tiraría justo la información con la que se puede corregir.

Y un `400` **no ofrece «Reintentar»**: repetir lo mismo devuelve lo mismo. Un `403` tampoco es una
lista vacía — no tener acceso es distinto de que no haya datos, y es la diferencia que el backend
eligió a propósito frente a devolver `200` con `data: []`.

**3. Un valor ausente se pinta ausente, nunca como cero.** El backend devuelve `null` de forma
deliberada —una calificación sin poner no es la nota mínima, una hora de fin ausente no es 1970— y
rellenarlo en el último paso desharía esa distinción. Hay dos pruebas emparejadas: `null` pinta un
guion, y un `0` que el backend sí devolvió pinta `0`.

### Lo que el cursor opaco impone al diseño

No hay total de resultados ni números de página, y **no se pueden inventar**: contar filas es
exactamente lo que la paginación keyset evita para no repetir ni perder registros con ingesta
continua. La navegación es siguiente/anterior, con «anterior» resuelto guardando los cursores
visitados — lo que `lista-accidentes` ya hacía a mano, ahora una sola vez y probado.

Dos detalles que la prueba fijó:

- **cambiar de filtros vuelve a la primera página.** Los cursores visitados pertenecen a la consulta
  anterior; reutilizarlos pediría continuar un recorrido que ya no existe, y la respuesta sería
  plausible y equivocada;
- **un error borra el cursor de la página siguiente.** Pertenecía a una respuesta que no llegó, y
  conservarlo dejaría avanzar sobre datos que no se leyeron.

### Dos defectos propios, encontrados al ejecutar

**Un comentario HTML con acentos graves dentro de una plantilla literal.** Cerraba la cadena y
rompía el fichero entero. Lo detectó el compilador.

**El pipe de números con locale fijo.** Fijar `'es'` exige registrar sus datos, y sin ellos el pipe
**lanza al renderizar** — es decir, la tabla se cae al pintar un número. Ahora usa el `LOCALE_ID` que
la aplicación tenga configurado.

### Verificación

`shared/informes`: 42 pruebas. Suite completa del frontend: **685 verdes**. Build de desarrollo
limpio.

⚠️ **Sin verificación en navegador**, y a propósito: ninguna página consume la capa todavía, así que
no hay nada que renderizar. Esa comprobación corresponde al piloto.

---

## 2026-08-15 — Decisión #23 resuelta: la pertenencia a una cuenta ya se puede escribir

Alcance: `config/settings.py` (una entrada), `core/repositories/cuentas_clientes/cuenta_usuario_repository.py`
(`vincular`, `desvincular`), `apps/cuentas_clientes/services/user_management_service.py`
(`idcliente` opcional en el alta), 1 fichero de prueba nuevo (10 pruebas),
`decisiones-pendientes.md` (#23 cerrada).

**Lo que faltaba era una línea.** `Dim_Usuario_Cliente` y su topic estaban declarados en
`database/tablas.json` desde el principio; lo que no existía era la entrada en
`settings.KAFKA_TOPICS`, sin la cual ningún repositorio podía publicar. No es que se olvidaran de
llamar a un método: el método no existía porque no había dónde escribir.

**La consecuencia que arrastraba era grande.** Los tres lectores de esa tabla —el expediente de
cliente en Seguimiento, los tickets en Soporte y el resolutor de pertenencia de los listados
tácticos— caían siempre en el respaldo por `admin_local_id`. De una organización con cinco usuarios,
**uno solo** veía los datos de su cuenta; los otros cuatro recibían `403`. En backend eso era una
nota; en pantalla se lee como una aplicación rota, y por eso se resolvió antes de empezar el
frontend de los listados.

**Decisión tomada:** cualquier usuario vinculado ve los datos de su organización.

### Tres cosas que se conservaron a propósito

**El respaldo por `admin_local_id` se queda.** Las cuentas creadas antes de este cambio no tienen
filas de vínculo, y quitarlo dejaría sin acceso a sus administradores. Así **no hace falta migrar
nada**: lo viejo sigue funcionando y lo nuevo suma.

**El criterio estricto sigue siendo estricto.** Red Operativa y Suscripciones acotan por
administrador local porque sus pantallas operativas lo hacen — dar de alta unidades y ver la
facturación. Si el vínculo también los ampliara, este cambio habría abierto una puerta trasera en dos
departamentos que no la pidieron. Hay una prueba que fija que `por_vinculo_a_cuenta` reconoce al
empleado y `por_admin_local` **no**.

**El `idcliente` del alta es opcional.** Los usuarios internos de TSI no pertenecen a ninguna
organización, y exigirlo dejaría sin poder crearlos. Su ausencia no vincula a nada por defecto.

### Y una que se decidió al escribirla

**`desvincular` marca inactivo, no borra.** Las tres consultas filtran por `activo = true`, así que
marcar basta para retirar el acceso. Borrar haría indistinguible «nunca perteneció» de «se le retiró
el acceso», que es justo lo que alguien necesitará saber el día que pregunte por qué un usuario dejó
de ver los datos de su cuenta.

### Verificación

Suite completa: **3601 verdes**, 2 saltadas por casos de uso retirados. Las 10 pruebas nuevas fijan
el comportamiento y, sobre todo, **la consecuencia**: sin vínculo un empleado no resuelve ninguna
cuenta —el estado en que estaba todo el sistema— y con vínculo resuelve la suya.

---

## 2026-08-15 — Listados tácticos de Emergencias (5 endpoints): un eje de acotamiento nuevo y tres correcciones de spec

Alcance: `core/informes/cobertura.py` (**nuevo**, aditivo),
`core/repositories/accidentes/` (4 repositorios de informes),
`core/repositories/seguimiento/informes_despachos_repository.py`,
`apps/accidentes/` (3 servicios, `views/informes_views.py`, `permissions.py` ampliado, 4 rutas),
`apps/seguimiento/` (1 servicio, 1 vista, 1 ruta),
`backend/conftest.py` (rama de consultas falsas **y corrección de las ramas de catálogo**),
9 ficheros de prueba nuevos (167 pruebas),
`spec.md`, `data-model.md` y el contrato OpenAPI (**corregidos**),
`specs/002-tactico/contrato-informes-simples.md` (§5.6 y §5.7).

**Es el primer módulo desde Red Operativa que amplía la capa transversal**, y por una razón
legítima: ninguno de los tres ejes anteriores acota por cobertura geográfica. La ampliación es
aditiva —`core/informes/acotamiento.py` no se tocó— y las suites de los seis departamentos previos
quedaron intactas.

### El cuarto eje no acota por titularidad

Los tres anteriores preguntan **de quién es la fila**: el ejecutivo del prospecto, la cuenta de la
suscripción, el partner de la credencial. Este no. Un cliente no ve «sus» accidentes —no son suyos en
ningún sentido— sino los de **las zonas que tiene contratadas**.

Cambian tres cosas a la vez, y por eso vive en su propio módulo en vez de ser un parámetro más:

| | Ejes de titularidad | Cobertura contratada |
|---|---|---|
| Lo que se resuelve | un identificador | **un conjunto de ubicaciones** |
| Cómo filtra | `= x` | **`IN (…)`** |
| No tener nada | no se da | **cero resultados** |

`meta.acotado_a` toma un valor propio: **`zonas_contratadas`**. Reutilizar `propios` diría algo falso.

**Sin zonas contratadas es CERO, nunca TODO.** De las dos lecturas posibles, una da el mapa de
siniestralidad completo a quien no contrató nada. La guarda se escribe explícita porque el fallo por
omisión —un `if zonas:` que se salte el filtro cuando el conjunto está vacío— cae justo en la lectura
peligrosa, y sin ruido: la respuesta conserva la forma correcta.

**El conjunto se resuelve una vez, antes de consultar.** Condados → ciudades → calles son dos
consultas por petición, sea cual sea el número de zonas, y hay una prueba que lo mide. El módulo
operativo hace hoy lo contrario a diez líneas de donde hace lo correcto: comprueba el condado **fila
a fila mientras recorre**, con un coste que crece más cuando las zonas del cliente son escasas — es
decir, cuando menos resultados va a haber.

### Tres correcciones que la implementación obligó a hacer

**1. `borrador` no se puede dar, y la spec lo pedía.** `BORRADOR` es un estado formal que vive en el
histórico. `Fact_Accidente` no guarda nada que lo distinga: un caso en borrador es `activo = true`
sin hora de fin, **idéntico a cualquier otro caso en curso**. Implementarlo devolvería **todos los
casos activos** etiquetados como detenidos en borrador — la forma correcta con el contenido
equivocado. Obtenerlo de verdad exige el histórico, que es justo lo que FR-008 prohíbe: FR-002 y
FR-008 se contradicen, y gana FR-008. Retirado de la spec, del data-model, del contrato y del
catálogo, donde la fila queda marcada ⛔ con el motivo.

**2. `cerrado` y `duplicado` no eran disjuntos.** Un duplicado que conservara hora de fin salía en
los dos filtros — contando el mismo hecho dos veces, que es exactamente el defecto que la distinción
existe para evitar. `cerrado` exige ahora además que el caso no apunte a otro.

**3. El cursor de casos y cierres era inpaginable.** `idaccidente` es **texto** —el número de caso—
y el componente de cursor convierte a entero por defecto. La primera página funcionaba y la segunda
daba `400`. Lo encontró la prueba de integridad del recorrido.

### Lo que el caso guarda, y lo que no

`Fact_Accidente` **no tiene columna de estado**. Pero tres hechos suyos distinguen las tres formas de
quedar inactivo: `activo`, `horafin` y `idaccidenteorigen`. El listado devuelve **los tres por
separado** y no un estado calculado: la exclusividad entre cerrado, descartado y fusionado la
garantiza el módulo de fusión, no este, y un campo derivado empezaría a mentir el día que esa
garantía cambiara, conservando la forma correcta.

Un recuento de «casos inactivos» sin distinguir sumaría **emergencias atendidas, falsas alarmas y
duplicados**: el trabajo realizado y el ruido descartado como la misma cosa.

Mismo criterio en despachos: «en tránsito» se deriva de las **horas del propio despacho** —despachado,
sin llegada, sin retiro—, no del histórico de estados. Y `0` es el centinela de «aún no ha ocurrido»:
una guarda por nulidad dejaría **ningún** despacho en tránsito.

### Una exención de cargo no levanta una exclusión constitucional *(§5.7)*

El Director de Operaciones ve los casos de todas las zonas y **sigue sin ver las coordenadas del
accidente ni la identidad de los implicados**. Su exención es de **acotamiento**; aquellas son
exclusiones que la constitución impone sobre el dato, no sobre quién pregunta.

La distinción importa porque el camino contrario se recorre sin querer: quien implementa una exención
de alcance puede leerla como «este rol lo ve todo». Cada listado con dato excluido lleva ahora una
prueba **con la autoridad del departamento**, no solo con el rol acotado.

### La hora que vale es la del sitio, y las dos tablas no son simétricas

La fotografía toma su hora de registro de una **columna propia**; la nota, de la **marca genérica de
modificación**, porque no tiene columna de sincronización. Tomar la equivocada devolvería la hora de
última modificación como si fuera la de captura, y **el error sería invisible** en los registros
hechos en línea —donde ambas coinciden—, apareciendo solo en los capturados sin conexión, que son
justamente los que importan.

Por eso cada prueba mira **los dos casos a la vez**: sin conexión, dos horas distintas; en línea, dos
iguales. Verificar solo uno de los dos no distinguiría una implementación correcta de otra que sella
la hora de subida en ambos campos.

> **Deuda anotada.** Que la nota carezca de columna propia de sincronización es una asimetría del
> modelo. Mientras siga así, cualquier consulta sobre sincronización de notas depende de una columna
> genérica que una actualización futura pisaría.

### Dos defectos que las pruebas encontraron en lo ya construido

**Las ramas del Pinot falso capturaban consultas ajenas.** Mis ramas de catálogo despachaban solo por
la lista de columnas, y los 19 informes agregados consultan `Dim_Calle` y `Dim_Ciudad` con **la misma
lista y distinto `WHERE`**. Resultado: tres pruebas de agregados en rojo, y —peor— filas filtradas por
la columna equivocada. Cada rama exige ahora también su cláusula `WHERE`.

**Las pruebas de coste en consultas de Partners y Soporte pasaban en vacío.** El contador envolvía
`PinotClient.query` y llamaba al original pasándole `self`; el mock que instala `mock_pinot` se llama
**sin** `self`, así que cada consulta lanzaba `TypeError`, la petición acababa en `401` y el conteo
quedaba en cero — con lo que `muchas == pocas` comparaba nada contra nada. Corregido en los tres
módulos, y añadida la guarda `pocas > 0` que impide que vuelva a pasar desapercibido.

Al arreglarlo apareció un matiz real: un catálogo que solo aplica a algunas filas cuesta **una**
consulta más para toda la página, no una por fila. La aserción de igualdad exacta hacía fallar un
comportamiento correcto; ahora es una cota fija, que es la que detecta el `N+1` de verdad.

### Verificación

`apps/accidentes` + `apps/seguimiento`: 463 pruebas verdes. Suite completa: **3591 verdes**, 2
saltadas por casos de uso retirados. Cobertura de los cuatro servicios, las dos vistas, el eje nuevo
y los cinco repositorios de informes: **95 %**.

---

## 2026-08-15 — Listados tácticos de Soporte al Cliente (2 endpoints): el módulo que verifica la capa transversal

Alcance: `core/repositories/soporte/` (2 repositorios de informes),
`apps/soporte_cliente/` (2 servicios, `informes_views.py`, `permissions.py` ampliado, 2 rutas),
`backend/conftest.py` (rama de consultas falsas),
6 ficheros de prueba nuevos (88 pruebas),
`contracts/informes-tacticos-simples.openapi.yaml`, `spec.md` y `data-model.md` (**corregidos**),
`database/seed_usuario_partner_demo.py` (comentario falso), `decisiones-pendientes.md` (#23).

**`core/informes/` no se tocó**, y esa era la hipótesis del módulo. Es el segundo consecutivo que
solo consume la capa transversal: la parametrización del criterio de pertenencia que introdujo Red
Operativa cubrió el departamento que la necesitaba —el que usa el criterio **amplio**— sin ampliarse.
Si hubiera hecho falta modificarla, la corrección iba allí, no aquí.

### El acotamiento se decide por lo que NO se tiene

Dos roles distintos —Cliente y Partner de integración— acotan por el mismo eje, y ninguno ve lo del
otro. Decidirlo por «ser Cliente» es un fallo que el módulo operativo **ya tuvo que corregir**: el
Partner reporta y no es Cliente, así que esa comparación lo habría dejado **fuera** del acotamiento,
viendo tickets ajenos.

La capa transversal lo resuelve sola: con los roles de atención como amplios y los de reporte como
acotados, un usuario con **ambos** cae en la rama amplia, que es exactamente FR-012. Y hay una prueba
que recorre toda combinación de hasta tres roles comprobando que el resolutor transversal y el
`es_solo_reportador` del módulo operativo **deciden lo mismo**. Sin ella, pantalla y listado podrían
acotar a poblaciones distintas sin que ninguna supiera de la otra.

### La spec decía cuatro valores y el dominio tiene cinco

`situacion_compromiso` se describía con cuatro situaciones: en curso, en riesgo, incumplido y sin
compromiso. Falta **`cumplido`**, que `resolver_ticket_service` escribe al resolver dentro de plazo.

Implementar las cuatro al pie de la letra habría dejado el filtro rechazando con `400` un valor
legítimo —«no es válido» cuando sí lo es— y **habría hecho imposible listar los tickets resueltos a
tiempo**. Es el mismo patrón que ya apareció en cuatro departamentos: la spec cita literales que no
coinciden con lo que el código escribe.

Corregido en los tres sitios —`spec.md`, `data-model.md` y el enum del contrato— y cerrado con una
prueba que compara el enum del OpenAPI contra las constantes del dominio. Si mañana aparece un sexto
valor, falla ahí en vez de manifestarse como un `400` inexplicable.

### `sin compromiso` no es ausencia de dato, y `sin clasificar` sí

Dos tickets pueden llegar sin situación de compromiso por motivos opuestos:

* **sin clasificar** — aún no hay contador; llega con `null`, y no se le atribuye ninguna;
* **`sin compromiso`** — está clasificado y **no se le pudo asignar plazo**; llega con su propio
  valor.

El vigilante de plazos descarta el segundo precisamente porque no tiene compromiso que vigilar: es el
único estado en que un ticket puede quedarse indefinidamente sin que ningún proceso lo mire.
Colapsarlo a `null`, u omitirlo, reintroduciría el defecto que la corrección anterior resolvió.

### El texto de los mensajes no se consulta

`Fact_Historial_Ticket` guarda `mensaje` y `es_nota_interna`. **Ninguna de las dos está en la lista
blanca**, y esa es toda la protección. La pantalla operativa las lee y filtra después —tiene que, le
hacen falta—; un listado táctico responde qué pasó, cuándo y quién lo hizo, y no necesita la prosa.

No consultarlas es más seguro que filtrarlas: un filtro correcto sigue siendo un filtro que alguien
puede olvidar al añadir un campo dentro de seis meses, y el fallo sería silencioso — la respuesta
conservaría la forma esperada, solo que con notas internas dentro.

### La autoría se decide por la ausencia de autor, no por el tipo de acción

Manual y automático están registrados **por duplicado**: el tipo de acción y la presencia de autor.
La ausencia de autor es la señal autoritativa, y es deliberada — antes se registraba al supervisor
que **recibía** el escalado como si lo hubiera ejecutado, y la corrección consistió en dejar el autor
vacío y mover al supervisor a destinatario.

Por eso `tipo_escalado` se deriva del autor. Si las dos señales se contradijeran el dato estaría
corrupto; decidir por el tipo lo **ocultaría**. Una prueba exige que coincidan en todos los registros.

De los once tipos de acción, el listado incluye exactamente dos. `alerta_sla_riesgo` es un **aviso**
—el ticket no cambia de agente ni de nivel— y `cierre_automatico_por_vencimiento` **cierra**, no
deriva. Contarlos daría la impresión de que la cola se deriva mucho más de lo que se deriva.

### Un defecto encontrado por las pruebas, el mismo de Partners

`urls.py` iba a importar `TicketsView` de `informes_views` teniendo `views.py` otra `TicketsView`
operativa: la segunda importación habría sustituido a la primera **en silencio**, y la ruta de
informes serviría el listado operativo. Resuelto con alias explícito antes de que llegara a fallar.
Es la segunda vez en dos módulos: conviene mirarlo en los departamentos que quedan.

### Un hallazgo transversal que no se arregla aquí (#23)

`Dim_Usuario_Cliente` **tiene topic de Kafka declarado** y aun así **ningún código de producción
publica en ella**. `ClienteLookupService` consulta la tabla y cae en `admin_local_id` cuando no
encuentra nada — es decir, siempre.

Consecuencia: hoy, en **todos** los departamentos, la pertenencia se resuelve de hecho por
administrador local, incluidos los listados que declaran el criterio amplio. Una organización con
cinco usuarios tiene uno solo que puede consultar sus listados acotados. Poblar esa tabla decide
quién de una organización ve qué, y eso excede a un módulo de listados. Anotado para decisión.

De paso se corrigió el comentario de `seed_usuario_partner_demo.py`, que justificaba sembrar por
`admin_local_id` diciendo que la tabla «no tiene topic de Kafka». Sí lo tiene; la conclusión práctica
era correcta y el motivo no.

### Verificación

`apps/soporte_cliente`: 202 pruebas verdes (114 previas + 88 nuevas). Suite completa: **3400 verdes**,
2 saltadas por casos de uso retirados. Cobertura de los dos servicios, las vistas y los dos
repositorios de informes: **96 %**.

---

## 2026-08-15 — Listados tácticos de Partners y API (5 endpoints) y la regla de la lista blanca

Alcance: `core/repositories/partners/` (3 repositorios de informes),
`apps/partners/` (3 servicios, `views/informes_views.py`, `permissions.py` ampliado, 5 rutas),
`apps/partners/views/urls.py` (**corrección**: colisión de nombres),
`backend/conftest.py` (rama de consultas falsas),
6 ficheros de prueba nuevos (156 pruebas),
`specs/002-tactico/contrato-informes-simples.md` (§5.5 y el recuento de listados).

**No se tocó ninguna pieza compartida.** `core/informes/` quedó igual: el acotamiento por
organización que introdujo Suscripciones y corrigió Red Operativa cubrió este departamento sin
ampliarse. Es la primera vez que la capa transversal absorbe un módulo nuevo sin cambiar.

### El estado no está en la tabla: se deriva, y ahora se deriva dos veces

`Dim_Partner` **no tiene columna `estado`**. Los seis estados de incorporación —Registrado, Plan
asignado, Pruebas activo, Pendiente de aprobación, Producción activa, Suspendido— salen de combinar
`activo`, `planapi`, las credenciales y el último evento de la bitácora.

`ConsultaPartnerService.derivar_estado` ya lo hacía, pero consulta la bitácora **una vez por
partner**. Correcto para una ficha; sobre una página de cincuenta, cincuenta consultas.

`_derivar_estado` replica la **precedencia** alimentándose de **dos consultas por lote**. Dos
derivaciones del mismo concepto es exactamente el tipo de duplicación que se paga tarde: si divergen,
el mismo partner tendría un estado en su ficha y otro en el listado, y ninguna pantalla sabría que la
otra discrepa. Por eso hay una prueba que **ejecuta las dos sobre los mismos datos** en los seis
casos y exige que coincidan.

Consecuencia declarada: el filtro `estado` empuja a SQL solo `Suspendido` y `Registrado`; los otros
cuatro comparten un pre-filtro y se refinan en Python, así que **una página puede devolver menos
filas que `limit`**. Es comportamiento del listado, no un defecto de la paginación — y por eso la
prueba de integridad del recorrido se hace sin ese filtro.

### La regla nueva: enumerar las columnas, no filtrarlas después *(§5.5)*

`Dim_CredencialAPI.client_secret_hash` autentica a quien lo tenga. Lo natural es quitarlo al
construir la fila. Lo natural **falla abierto**: el día que alguien añada otra columna sensible a la
tabla, entra por la consulta, atraviesa el filtro que no la conoce y se publica sin que ninguna
prueba se entere.

La lista blanca invierte el defecto: lo que no está enumerado no sale, y añadir una columna a la
tabla no cambia nada. Una prueba lee el propio fichero del repositorio y comprueba que ninguna
consulta literal use `SELECT *`. Otra comprueba que **el contrato OpenAPI tampoco declare** el campo:
si apareciera ahí, la implementación tendría permiso escrito para publicarlo.

Aplica igual al medio de cobro de Suscripciones y al contacto del proveedor en Red Operativa, que ya
lo hacían de facto. Ahora está escrito.

### Lo que este módulo no puede decir, y por qué se dice en otro sitio

Una credencial con `activo=False` puede estarlo porque el partner **la revocó** —decisión de
seguridad— o porque **se desactivó en cascada** al suspenderlo por impago. En `Dim_CredencialAPI` las
dos filas son **idénticas**.

El listado de credenciales no inventa el motivo: no lo tiene. La bitácora sí, con **tipos distintos**
(`revocacion_credencial` y `desactivacion_por_cascada`). Agruparlos bajo una etiqueta cómoda como
«desactivada» llevaría a reactivar en bloque tras el pago, resucitando una credencial cuyo secreto
está comprometido. Hay una prueba por cada mitad: una exige que el listado **no** traiga motivo, otra
que la bitácora **sí** los distinga.

En la misma línea, la **reactivación sin motivo es correcta**: el SRS exige motivo al cortar el
acceso, no al devolverlo. Presentarla como dato faltante induciría a «completar» un registro completo.

### Sin alcance configurado no es acceso ilimitado

`Dim_Preferencias_Cliente.zonas_geograficas` vacío significa **que nadie lo ha configurado**.
Devolver `[]` invita a leerlo como «sin restricción», y en un listado cuya función es decir qué datos
puede consumir un partner, eso daría por contratado un alcance que nadie acordó. Se devuelve `null`.

### Un defecto encontrado por las pruebas: la ruta servía la vista equivocada

`apps/partners/views/urls.py` importaba `PartnersView` de `informes_views` y, más abajo, otra
`PartnersView` de `partner_views`. La segunda importación **sustituía a la primera en silencio**, así
que la ruta de informes servía el listado operativo. Ninguna prueba del módulo operativo podía
detectarlo. Corregido con un alias explícito y comentado en el sitio.

### Verificación

`apps/partners`: 672 pruebas verdes (558 previas + 114 nuevas de informes, más las de servicio).
Cobertura de los tres servicios de informes y las vistas: 93 % (mínimo 83 %).

---

## 2026-08-15 — Listados tácticos de Red Operativa (4 endpoints) y la corrección del acotamiento

Alcance: `core/informes/pertenencia.py` (**nuevo**), `core/informes/acotamiento.py` y
`envelope.py` (ampliados de forma **compatible hacia atrás**),
`core/repositories/red_operativa/` (3 repositorios de informes),
`apps/red_operativa/` (3 servicios, 4 módulos de vistas, `permissions.py`, 4 rutas),
`apps/suscripciones/views/informes_base.py` (declara su criterio explícitamente),
`backend/conftest.py`, 10 ficheros de prueba nuevos,
`specs/002-tactico/contrato-informes-simples.md` (§5.3 y §5.4),
`decisiones-pendientes.md` (#22).

**Es el primer módulo que CORRIGE la capa transversal en vez de ampliarla**, y por eso su
comprobación de compatibilidad pesaba más que en los anteriores. Salió limpia: piloto, Ventas,
Suscripciones y los 19 informes agregados, todos sin moverse.

### La generalización de Suscripciones se quedó corta, y esto lo demuestra

El eje «organización» se diseñó allí como si **«pertenecer a una cuenta» fuese un concepto único**.
No lo es:

| Criterio | Quién cumple | Pantallas |
|---|---|---|
| **Administrador local** | Una sola persona por cuenta | Alta de unidades, facturación |
| **Vínculo a la cuenta** | Cualquier miembro | Expediente de cliente, tickets |

Unificarlos rompería la regla del contrato común —*un informe nunca más amplio que su pantalla*— en
un departamento u otro. Así que el criterio pasa a ser **parámetro explícito** y cada listado declara
el suyo. El defecto sigue siendo el estricto, que es lo que Suscripciones ya hacía: **se añadió una
opción, no se alteró la existente**.

Corregirlo ahora, con dos departamentos usándolo, fue barato. Con cinco no lo habría sido.

> **Trampa encontrada de paso.** `CuentaUsuarioRepository.get_cliente_ids_for_user` **suena** a
> criterio amplio y es el estricto: solo mira `admin_local_id`. El amplio real es
> `list_cuentas_del_usuario`.

### El defecto de mayor consecuencia de toda la serie

**`activo` significa «existe», no «puede acudir».** Los cuatro estados operativos de una unidad
—`Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`— viven **solo en el histórico**, y obtenerlos
cuesta una consulta por unidad.

Un listado de flota presentado como disponibilidad llevaría a decidir cobertura sobre unidades fuera
de servicio, ocupadas o ya en camino a otro accidente. **En los módulos comerciales un error así
infla una cifra; aquí decide si alguien acude.**

Tres defensas, y la prueba comprueba las tres: el campo se llama `dado_de_alta`, la respuesta
**declara su alcance** en `meta`, y ningún campo promete disponibilidad. La regla sube al contrato
común como **§5.4**.

### Dos hallazgos más, de la misma familia

**`En_Alerta` no se agrupa con `Despublicada`.** Es una región **operativa** con cobertura
degradada: candidata a despublicarse, no despublicada. Agruparlas ocultaría exactamente la ventana en
la que OT13 puede actuar. Mismo patrón que «en disputa» vs «impaga» en Suscripciones.

**Una baja forzada trae su caso afectado; una normal, no.** No es una etiqueta: es la traza de
impacto que el SRS exige. Sumar ambos tipos convertiría un incidente operativo —un accidente que se
quedó sin su unidad— en una estadística de rotación de flota.

### Rendimiento: el riesgo que la spec anotaba

La geografía se resuelve **por lotes** —dos consultas por página, no una por fila—, reutilizando el
patrón que `ubicacion_catalogo_repository` ya tenía. La prueba **cuenta consultas con 100 unidades**
y no mide tiempo: con diez, una implementación N+1 parece igual de rápida y el defecto pasaría.

### Lo que no sale

`latitud`, `longitud` y `contactoproveedor`. La posición de una unidad es dato sensible sujeto a
control y auditoría, y no aporta a un listado de composición — para seguir una unidad en tránsito
existe el módulo de seguimiento, con su propio control.

**Verificación.** 2925 → **3162** pruebas (+237), mismas 2 omitidas, cero regresiones.

---

## 2026-08-15 — Listados tácticos de Suscripciones y Facturación (4 endpoints) y el eje «organización»

Alcance: `core/informes/acotamiento.py` (segundo eje) y `core/informes/periodo.py`
(`parse_fecha_columna`, ambos ampliados de forma aditiva),
`core/repositories/suscripciones/` (3 repositorios de informes),
`apps/suscripciones/` (3 servicios, 4 módulos de vistas, `permissions.py`, 4 rutas),
`backend/conftest.py`, 12 ficheros de prueba nuevos,
`specs/002-tactico/contrato-informes-simples.md` (regla 5 de Pinot),
`decisiones-pendientes.md` (#20 y #21). **Los 16 contratos OpenAPI del catálogo** corregidos.

**El segundo eje de acotamiento.** El primero —«persona», de Ventas y CRM— asume que el titular *es*
el solicitante. Éste tiene un **salto de indirección**: el usuario pregunta y el resultado se acota a
la cuenta cliente a la que pertenece. Red Operativa, Partners y Soporte heredan este mismo eje, así
que la quinta y la sexta copia ya no aparecerán solas.

**Y una diferencia deliberada con el resolutor operativo.** `resolve_cliente_activo` exige cuenta
`Activo`; el táctico **no**. Aquél controla escrituras; éste, la lectura de los propios registros — y
una cuenta suspendida es justamente donde su responsable mira para saber qué regularizar (FR-011).
Negárselo lo dejaría a ciegas sobre su propia deuda.

### El requisito de seguridad más fuerte de la serie

`Dim_MetodoPago.tokenpasarela` **no es un hash**: `cobro_service.py:68` lo pasa a la pasarela para
ejecutar el cargo. **Quien lo tenga, puede cobrar.** No hay nada que romper —bastaría con leer la
respuesta— y el impacto no es informativo sino económico.

La prueba inspecciona **la respuesta serializada completa** de los cuatro listados, no los campos que
el contrato declara. La razón: un `SELECT *` filtra el campo **aunque el contrato no lo mencione**.
El contrato describe lo que se pretende devolver; la respuesta es lo que se devuelve.

### Dos hallazgos que habrían producido informes equivocados

**1. «Sin cambio de plan programado» es un centinela `0`, no una ausencia.** El código escribe un `0`
explícito. Un filtro escrito como comprobación de nulidad sería **siempre cierto** y devolvería
*todas* las suscripciones como si todas tuvieran una reducción pendiente — alimentando una previsión
de ingresos con reducciones inventadas.

**2. Una factura `En disputa` no es una factura impaga.** `estado_pago` toma **cuatro** valores, no
tres. La disputa significa que el cliente abrió un reclamo y el sistema **dejó de reintentar el
cargo**; presentarla como mora induce a perseguir un cobro detenido a propósito, que es lo que
corrigió el hallazgo B41. El filtro de vencidas la excluye **en la consulta**, no en Python: filtrar
después de paginar devolvería páginas incompletas.

### Lo que se hizo bien por comprobar antes

`Dim_MetodoPago.fechaexpiracion` es `LONG`, así que el filtro de caducidad va **entero a la base**.
En Ventas y CRM la columna equivalente era texto con formatos mixtos y obligó a un filtro en dos
pasos y a admitir páginas cortas. Comprobar el tipo **antes** de diseñar evitó arrastrar aquella
complejidad, y la lección sube al contrato común como **regla 5 de Pinot**.

### Defecto sistémico corregido

**Los 16 contratos OpenAPI del catálogo táctico eran YAML inválido** — la misma descripción sin
comillas con `data: []`, repetida por copia. Ninguno se había cargado nunca con un parser. Ahora los
16 validan, y los tres departamentos implementados tienen una prueba que carga su contrato y compara
la implementación contra él.

**Verificación.** 2579 → **2925** pruebas (+346), mismas 2 omitidas, cero regresiones. La ampliación
de `core/informes/` se comprobó **aditiva** (T011): ni el piloto, ni Ventas y CRM, ni los 19 informes
agregados se movieron.

---

## 2026-08-15 — Listados tácticos de Ventas y CRM (4 endpoints) y el acotamiento por titularidad

Alcance: `backend/core/informes/acotamiento.py` (**nuevo**, transversal a 7 departamentos),
`core/informes/{envelope,vistas}.py` (ampliados de forma aditiva),
`backend/core/repositories/ventas_crm/` (3 repositorios de informes),
`backend/apps/ventas_crm/` (3 servicios, 3 módulos de vistas, `permissions.py`, 4 rutas),
`backend/scripts/seed_demo_ventas_tactico.py` (**nuevo**), `backend/conftest.py`,
13 ficheros de prueba nuevos, `specs/002-tactico/contrato-informes-simples.md` (§5.1 y §5.2),
`decisiones-pendientes.md` (#19).

**Lo que este módulo aporta a los seis departamentos restantes.** El piloto construyó el andamiaje
de forma —período, paginación, envelope—; éste construye el de **acceso**: un único resolutor de
acotamiento por titularidad, y el campo `meta.acotado_a` que declara el alcance de cada respuesta.
Soporte acotará por cliente reportador, Partners por partner, Red Operativa por proveedor de flota;
ninguno vuelve a decidir la regla.

**Pedir lo ajeno es `403`, nunca sustitución silenciosa.** Es la decisión con más consecuencias.
Devolverle su propia cartera a quien pidió la ajena produce un informe plausible que **responde a una
pregunta que nadie hizo**, y además le oculta al solicitante que pidió algo indebido. El
comportamiento se copió del que ya estaba verificado en producción
(`consulta_notificacion_ventas_service.py`), en vez de inventarlo.

### Tres hallazgos que habrían producido informes equivocados

**1. «Perdido» no es «inactivo».** Un prospecto se vuelve inactivo por dos motivos **opuestos** y los
dos dejan `activo = false`: se perdió la oportunidad, o **se ganó** y ya es cliente. Un listado de
perdidos filtrado por `activo = false` incluiría los convertidos — es decir, **presentaría los éxitos
comerciales como fracasos**, sin dar ningún error. El filtro tiene tres valores, no dos, y la
condición de cada uno vive en una tabla y no en un `if` encadenado, para que la equivalencia
prohibida no pueda colarse sin verse.

**2. La expiración de la demo no se puede comparar en SQL.** `demo_expiracion` es `STRING` cuando
todo lo demás es `LONG` epoch-ms, y el sistema acepta tres formatos (`Z`, `+00:00`, sin zona).
Compararla entera da resultados incorrectos sin error visible. Se resuelve en dos pasos: prefiltro
por el prefijo `YYYY-MM-DD` —los diez primeros caracteres sí son uniformes— y refinamiento exacto en
el servicio, **con el mismo instante** que calcula los días restantes. La causa raíz queda anotada
como decisión pendiente **#19**.

**3. Los datos de contacto no salen.** `Dim_Prospecto` guarda `gmail` y `telefono`; el propósito
táctico es supervisar la cartera, no contactar. Columnas enumeradas y prueba que mira el código,
porque el doble en memoria recorta las columnas él mismo y una prueba contra la respuesta seguiría
pasando con un `SELECT *`.

### El fixture del que depende que este módulo esté probado

`dos_carteras`. **Con una sola cartera poblada, filtrar por ejecutivo y no filtrar devuelven lo
mismo**, así que toda prueba de acotamiento pasa aunque el acotamiento no exista. Es el fallo más
fácil de cometer aquí, y por eso los dos gerentes tienen cartera a la vez y de tamaños distintos.

### Defecto preexistente corregido

**El contrato OpenAPI no era YAML válido** — una descripción sin comillas contenía `data: []`,
exactamente el mismo defecto que el del módulo piloto. Ahora hay una prueba que lo carga y compara
la implementación contra él, endpoint por endpoint.

### Lo que se declara y conviene saber

Una página de `demos-activas` **puede devolver menos filas que el `limit` pedido**: el prefiltro por
día trae de más y el refinamiento descarta con precisión de segundo. `has_next` es la autoridad; el
número de filas no lo es. Y `reasignaciones` **no lo ve un gerente** ni acotado a lo suyo: el reparto
de cartera es una decisión sobre él, no una herramienta suya.

**Verificación.** 2193 → **2579** pruebas (+386), mismas 2 omitidas, cero regresiones. La ampliación
de `core/informes/` se comprobó **aditiva** (T011): ni el piloto ni los 19 informes agregados se
movieron.

---

## 2026-08-15 — Piloto de listados tácticos: Cuentas y Clientes (8 endpoints) y la capa transversal

Alcance: `backend/core/informes/` (**nuevo**, 5 módulos), `backend/core/repositories/cuentas_clientes/`
(3 repositorios de informes + constantes canónicas en 3 existentes),
`backend/apps/cuentas_clientes/` (3 servicios, 3 módulos de vistas, `permissions.py`, 8 rutas),
`backend/conftest.py` (doble de Pinot ampliado), 14 ficheros de prueba nuevos,
`specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/`, `decisiones-pendientes.md` (#18).

**Qué se construyó.** Los 8 listados de OT04, OT17 y OT18, y con ellos **el andamiaje que los siete
departamentos restantes reutilizan**: período con rango opcional, paginación keyset por cursor,
envelope `{data, meta:{pagination, filtros}}`, vista base con las tres validaciones que el contrato
obliga a rechazar en vez de tolerar, y presentación de ausencias.

**El cursor y el `ORDER BY` salen del mismo objeto.** Es la decisión de diseño con más consecuencias:
si divergen, la consulta devuelve la página anterior en vez de la siguiente y el consumidor pagina en
círculos **sin recibir ningún error**. `Cursor` genera ambos, más la cláusula keyset con su
desempate anidado, desde una única declaración de campos.

### Tres correcciones sobre la spec, todas del mismo tipo

La spec citaba **valores literales que no existen en el sistema**. Implementarlos al pie de la letra
no habría fallado: habría devuelto `200` con `data: []` para siempre.

| Dónde | Decía | Es | Efecto de no corregirlo |
|---|---|---|---|
| L6 sesiones | `estadosession = 'Activa'` | `'Inicio sesion'` | Listado vacío permanente |
| L7 credenciales | `estadocredencial = 'Temporal'` | `'Cambio contraseña'` | Listado vacío permanente |
| L3 cuentas (OpenAPI) | `enum [... Suspendido, Baja]` | `Rechazado`, `Dado de baja` | `400` a un filtro correcto |

No es hipotético: `credential_repository.py:14` documenta que **este mismo fallo ya ocurrió** —un
seed escribía `"ACTIVA"` mientras el código comparaba contra `"Activo"`, invalidando la credencial de
todos los usuarios sembrados—. Por eso la corrección no fue cambiar un literal por otro, sino
**centralizar los estados** donde aún eran literales sueltos: `ESTADO_SESION_*` en
`session_repository`, `ESTADO_CLIENTE_*` en `cliente_repository`, y consumirlos desde el informe.

**Y un cuarto caso, de orden.** L7 debía ordenarse por `fecha_solicitud_cambio`, columna que existe
en el esquema y **ningún escritor rellena**. Un cursor sobre una columna siempre ausente no localiza
ninguna fila: la **segunda página** habría fallado, y solo con datos suficientes para que hubiera
segunda página. Se ordena por `fecha_actualizacion`, que lleva el dato y significa lo mismo; el campo
de la respuesta conserva su nombre.

### Lo que el doble en memoria no podía cubrir

`conftest.py` recorta a mano las columnas que cada consulta enumera, así que una prueba que solo
mirase la respuesta seguiría en verde si alguien cambiara una consulta a `SELECT *` —y la contraseña
viajaría contra Pinot real—. Las pruebas de research D7 tienen por eso **dos mitades**: la respuesta
y el texto de las consultas del repositorio.

Del mismo modo, las de centinelas (D3) se verifican contra `_coerce_value` y `core/informes/formato.py`,
no contra el doble, que no coerciona nada. Esa laguna produjo un defecto real durante la
implementación: `dias_transcurridos` convertía el centinela `LONG` en «hace 106.752.011.843 días».
La ausencia la decide ahora un único `marca_ausente`, compartido por la fecha que se muestra y por
los días que se calculan, para que las dos lecturas no puedan discrepar.

### Defectos preexistentes corregidos de paso

- **El contrato OpenAPI no era YAML válido**: una descripción sin comillas contenía `data: []`.
  Ninguna herramienta lo había cargado nunca. Ahora hay una prueba que lo carga y compara la
  implementación contra él, endpoint por endpoint.
- **`fechahorainiciosesion` se sembraba como texto ISO** en 16 sitios, cuando el esquema la declara
  `LONG` epoch-ms y el escritor real escribe epoch-ms. Nadie la leía, así que nadie lo notaba.

### Lo que queda abierto

`transferencias-propiedad` está implementado y verificado, pero
`Fact_HistorialTransferenciaPropiedad` **no la escribe nadie**: la transferencia solo deja rastro en
la auditoría. Contra el stack real ese endpoint devolverá vacío. Es trabajo del módulo operativo
(CU-O15) y está anotado como decisión pendiente **#18**.

**Verificación.** 1673 → **2193** pruebas (+520), mismas 2 omitidas, cero regresiones.
`apps/informes_tacticos` intacto (research D1), que era el guardián del aislamiento del piloto.

---

## 2026-08-14 — Modelo analítico táctico: esquema en estrella implementado

Alcance: `dags/` (7 módulos de dimensión y hecho, 4 flujos nuevos, 15 ficheros de prueba),
`specs/002-tactico/modelo-analitico/`, `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`
(marcado como sustituido), `decisiones-pendientes.md` (#19 y #20).

**Por qué.** El diseño anterior creaba **una tabla y un flujo por informe**. Con ~105 informes
compuestos por delante, eso son ~105 tablas y ~105 flujos, cada uno con su forma de calcular lo mismo
y su oportunidad de discrepar. El modelo en estrella los resuelve con consultas.

**Qué se construyó.** 5 dimensiones y 4 hechos en `tsi_tactico`, cargados por 4 flujos de Airflow.
Los hechos van particionados por mes y la recarga **descarta la partición** en vez de borrar por
condición — que en este almacén es una mutación, y las tres tablas viejas acumulan una por corrida
con ~180 fechas literales cada una.

**El defecto que justificaba el modelo, corregido.** `dim_unidad` guarda una fila por **versión**:
cada despacho apunta a la versión vigente cuando ocurrió, así que cambiar de proveedor ya no
reescribe la historia. El flujo anterior lo reconocía en su propio código («usa el `idcliente`
**actual** […] no un snapshot histórico real»).

**Tres defectos encontrados en los informes que sustituye**, todos verificados con cifras:

1. ⚠️ **Truncamiento silencioso a 10 000 filas.** Dos consultas a Pinot sin `LIMIT` explícito reciben
   el límite por defecto del cliente. La pérdida de señal analizaba **10 000 de 59 045 posiciones**
   (16,9 %) y publicaba el resultado como completo: 714 huecos donde hay 3 942. El rendimiento por
   proveedor veía **10 000 de 19 528 transiciones**: 344 rechazos donde hay 661.
2. **La completitud del índice de calidad no podía dar otra respuesta que `1.0`**: comparaba contra
   nulidad y el origen usa centinelas.
3. **`Fact_NotificacionDespacho` no tiene hora propia de confirmación ni rechazo** y tiene 31 filas
   para 4 314 despachos. Los hitos se tomaron de `Fact_HistorialDespachoUnidad`.

**Validación.** Corriendo la lógica del flujo viejo sobre datos completos salen exactamente las
cifras del modelo (3 942 huecos, 661 rechazos, 331 abortos), y el tiempo medio de llegada coincide
al centésimo: **669.44 s**. Suite de `dags/`: **151 pasan**. Backend: **1 673 pasan, 2 omitidas**,
sin movimiento — este módulo solo lee el sistema operativo.

**Lo que NO se retiró, y por qué.** Las tres tablas y sus flujos siguen vivos: tres repositorios del
backend los leen, y dejar de refrescarlos mientras los endpoints siguen consultándolos serviría datos
congelados sin error visible. Registrado como decisión pendiente #20.

---

## 2026-08-14 — Autoridades departamentales: catálogo de roles y constantes

Alcance: `backend/scripts/_demo_seed_common.py`, `backend/core/auth/roles_tacticos.py`,
`.specify/docs/actors.md`, `.specify/docs/architecture/architectural-patterns.md`,
`specs/002-tactico/` (contrato común, `acceso-tactico.md` y las 7 specs de módulo).

**Por qué.** Los informes tácticos especificados en `specs/002-tactico/` asignaban permisos
solo a roles operativos. Al revisar el §5.1 del SRS —que define, por departamento, un
responsable operativo y una autoridad superior— se comprobó que **seis de las ocho
autoridades no existían como rol del sistema**, y que `actors.md` las documentaba en una
sección marcada como fuera de alcance.

**Roles añadidos al catálogo** (`ROLES_DEMO`, fuente única de `Dim_Rol`): `DirectorMarketing`
(17), `DirectorFinanciero` (18), `DirectorExpansion` (19), `DirectorOperaciones` (20),
`GerenteExitoCliente` (21) y `DirectorDatos` (22). `DirectorTecnologico` (6) y
`DirectorEstrategia` (14) ya existían y suman autoridad táctica sin perder su papel
operativo.

**Defecto latente corregido de paso.** `GerenteCuentasPublicas` **estaba referenciado por
código de producción en cuatro sitios de `apps/ventas_crm`** —entre ellos la asignación
automática, que enruta los prospectos del sector público a ese rol— y **no existía en el
catálogo**. Ningún usuario podía tenerlo, así que esos prospectos se quedaban sin ejecutivo
candidato. Añadido como idrol 16.

**Constantes.** Nuevo `backend/core/auth/roles_tacticos.py`, transversal en vez de duplicado
en siete `permissions.py`: dos departamentos comparten `DirectorTecnologico`, y repetir la
cadena en siete sitios es como aparecen las divergencias de un carácter que nadie detecta
hasta que un permiso deja de conceder. Expone conjuntos **por materia**, no por
departamento, porque el SRS advierte que la autoridad «no siempre es una jefatura única»:
en Suscripciones y Red Operativa está repartida, y en Cuentas y Clientes alcanza a un solo
listado.

**Dos discrepancias documentales resueltas** a favor del SRS, según lo decidido: `actors.md`
asignaba Ventas y CRM a un «Director Comercial» que ese mismo documento había introducido
—el §5.1 dice Director de Marketing—, y Cuentas y Clientes al Gerente de Éxito del Cliente
—el §5.1 dice Director Tecnológico, y **solo sobre la capa de accesos técnicos**—. El rol
`Director Comercial` queda retirado.

**Hallazgo anotado, no resuelto.** Cuentas y Clientes **no tiene autoridad de negocio**: la
única que el §5.1 le asigna es el Director Tecnológico con alcance limitado. Sus siete
listados restantes quedan bajo el Administrador, que es a la vez su responsable operativo.
Puede ser intencional o faltar un cargo; queda en `decisiones-pendientes.md`.

**Límite que se dejó explícito en código y en spec.** La autoridad accede **sin el
acotamiento por titularidad**, pero esa exención **no alcanza al dato sensible**:
coordenadas, identidad de personas implicadas, secretos de autenticación y medios de cobro
siguen excluidos de todo informe para todos los roles. Son exclusiones constitucionales, no
de acotamiento.

**Verificación.** `python -m pytest` → **1673 passed, 2 skipped**, idéntico a la línea base:
el catálogo crece de 14 a 21 roles sin identificadores ni nombres duplicados, sin reutilizar
el idrol 11 (obsoleto), y sin que ninguna suite existente se mueva. Los conjuntos de
autoridad y el predicado `es_autoridad` verificados por separado.

**Pendiente.** Ningún usuario de demo tiene todavía los roles nuevos. Sembrarlos entra con
la implementación de los informes, que es cuando habrá algo que puedan consultar.

---

## 2026-08-01 — Revisión `002-tactico` (spec vs. docs globales)

Alcance: `specs/002-tactico/`, `.specify/docs/infra/infrastructure.md`

**T1** — `spec.md` no declaraba las 9 características ISO/IEC 25010 ni trazabilidad OT (solo el `plan.md` lo hacía). Corregido: sección Constitution Compliance + enlace a `informestacticos/auditoria-esquemas-informes-v2.md`; FR-011 (ClickHouse/Postgres Airflow ≠ almacén de dominio).

**T2** — `infrastructure.md` §1 afirmaba “infraestructura de datos única / no se usa PostgreSQL” de forma absoluta, en tensión con el stack `tactico` ya documentado en §2.1. Reformulado: Kafka+Pinot = canal único del *modelo dimensional*; Postgres de Airflow = solo metastore. Encabezado §5 actualizado (ya no dice “no implementar todavía” mientras §5.1 está activo). Regla vinculante §4 añadida sobre ClickHouse/Postgres.

**T3** — Todo el feature vive bajo `specs/002-tactico/infraestructura/` (`spec.md`, plan, research, data-model, contracts, quickstart, tasks, índice). `feature.json` apunta a esa carpeta. Se eliminó `checklists/` (gate de `/specify` ya cumplido; no aporta valor operativo tras plan/tasks cerrados).

**T4** — Variable `CLICKHOUSE_DB` (default `tsi_tactico`; no `TSI-tactico` — el guion no es válido como identificador ClickHouse sin comillas). Init en `docker/tactico/clickhouse-init/`; documentado en contrato, quickstart y `.env.tactico.example`.

---

## 2026-07-15 — Módulo Emergencias (revisión spec vs. implementación)

Alcance: `despacho-inteligente`, `evidencia-unidad`, `registro-accidente`, `seguimiento-cierre-de-casos`

> Nota: el `git status` del repo también mostraba otros archivos modificados/sin trackear que
> **no** correspondían a este trabajo (cambios previos ya en curso antes de esta sesión,
> p. ej. `confirmar_despacho_service.py`, `mi_seguimiento_views.py`, extracción de templates
> `.html`, etc.). Esta entrada solo cubre lo hecho en esa sesión.

### Backend

**G1 (CRITICAL) — Jobs periódicos sin agendar.**
`run_timeout_despacho_job`, `run_gps_senal_perdida_job` y el job de depuración GPS existían
pero nadie los invocaba (no había Celery/APScheduler ni cron configurado). Se agregaron
management commands de Django (patrón `send_onboarding_reminders.py`):
`backend/apps/despacho/management/commands/run_timeout_despacho_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_senal_perdida_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_depuracion_job.py`.
**Pendiente:** decidir invocación en producción (cron, worker separado, Celery beat).

**G2 (HIGH) — Estado de unidad forzado a "Activa" al liberar despacho.**
Al retirar o abortar un despacho, la unidad siempre volvía a `Activa`, ignorando
`Fuera de servicio` (RN-SEG-003 no implementada). Corregido en
`backend/apps/seguimiento/services/retiro_despacho_service.py` y
`backend/apps/seguimiento/services/abortar_mision_service.py` (consultan estado actual
antes de liberar; `cerrar_caso_service.py`/`forzar_retiro_service.py` heredan el fix vía
`RetiroDespachoService`).

**G4 (HIGH) — Mensaje de error genérico en registro de accidente.**
`AccidenteListCreateView.post` respondía siempre `"duplicado_posible"` ante un
`DuplicateConflictError`, aun cuando la advertencia real era `fuera_cobertura`. Corregido
en `backend/apps/accidentes/views/accidente_views.py` (usa `advertencias[0]` real, expone
el arreglo completo).

**G5 (HIGH) — Scoring de "disponibilidad reciente" hardcodeado.**
En `consulta_candidatas_service.py`, el 15% del score de RN-DES-008 era constante
(`disp_score = 0.5`). Se agregó `_disponibilidad_reciente_score()` (score real por tiempo
continuo en estado `Activa`, tope 30 min).

**G6 (MEDIUM) — Selección de accidente "padre" en fusión usa campo incorrecto.**
`ValidacionAccidenteService.suggest_parent_id` usaba `fechahoraaccidente` en vez del
`fechahoramodificado` de la primera transición a `BORRADOR`/`REPORTADO`
(`Fact_AccidenteTipoEstadoAccidente`), per RN-REG-010b. Corregido en
`backend/apps/accidentes/services/validacion_accidente_service.py` (fallback a
`fechahoraaccidente` si no hay historial).

**G9 — Verificado sin cambios.** `registrar_posicion_gps_service.py` sí invoca
`RegistrarLlegadaService` automáticamente vía geofencing (RF-SEG-002) — falso positivo del
análisis previo.

### Frontend

**G3 (HIGH) — Auto-sync de evidencias nunca se activaba.**
`EvidenciaSyncSchedulerService.iniciarAutoSync()` existía pero no se llamaba desde ningún
lado — código muerto. Corregido: nuevo `listarIdsAccidentesPendientes()` en
`evidencia-offline-store.service.ts`; `sincronizarTodosLosCasos()` ahora usa la unión de
casos en sesión + pendientes reales en IndexedDB; `app.component.ts` invoca
`iniciarAutoSync()` en el constructor (corre durante toda la vida de la app).

**Bug preexistente (detectado al verificar G4 en el frontend) — Manejo del conflicto
409 roto.** `registro-accidente.page.ts` leía `err.error` en vez de `err.error.data`
(envoltura `{data, meta}`) y usaba `idaccidente_duplicado_sugerido` (siempre `null`) en
vez de `idaccidente_similar`. Resultado real: el diálogo de "posible duplicado" nunca se
abría y la fusión nunca funcionaba. Corregido en
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`;
se agregó manejo explícito de `error === 'fuera_cobertura'`. Tests actualizados en
`registro-accidente.page.spec.ts`.

### Verificación realizada

- Backend: `pytest apps/despacho apps/accidentes apps/seguimiento` → 285/285 tests.
- Frontend: `tsc --noEmit` (app + spec) sin errores. (Karma/Jasmine no se pudo correr por
  falta de Chrome en el entorno; recomendado correr `ng test` localmente.)
- Docker: `docker compose -f accidentes.yml build` exitoso.

### Pendientes / fuera de alcance

- **G7** — Notificaciones push/SMS en despacho son stubs (`_default_push`/`_default_sms`
  siempre "exitosos"); requiere integración real con un proveedor.
- **G8** — Payload estructurado de alerta crítica hacia monitoreo (RF-DES-008) no
  confirmado a fondo.
- **G10 / T108** — No existe endpoint de reversión (undo) para descarte/fusión de
  accidentes; decisión de alcance pendiente. Ver `registro-accidente/tasks.md` T108.

---

## 2026-07-16 — Regularización de contrato para proxy de ruta OSRM

Alcance: `seguimiento-cierre-de-casos`

El endpoint `GET /api/v1/seguimiento/ruta` (`backend/apps/seguimiento/views/ruta_views.py`,
`core/osrm/client.py`) se implementó junto con el trabajo del 2026-07-15 pero no se agregó
al contrato OpenAPI ni a `tasks.md` en su momento (violación Principio VI — API-First).
Regularizado: contrato agregado en
`contracts/seguimiento-cierre-de-casos.openapi.yaml` (`/seguimiento/ruta`), tarea T042b y
fila CA-SEG-002b en `traceability.md`.

---

## 2026-07-31 — Auditoría de suites, paginación en Pinot e higiene de datos

Alcance: `registro-accidente`, `seguimiento-cierre-de-casos`, `evidencia-unidad`,
`despacho-inteligente`, `Red-Operativa/alta-unidades`, `Suscripciones-Facturacion`,
`Cuentas-Clientes`, infraestructura de datos (`database/`).

Origen: ejecución completa de las suites unitarias y recorrido end-to-end del sistema
contra el stack real (Kafka + Pinot + Django + Angular), no un ciclo `/plan`→`/tasks`.

### Infraestructura de datos

**D1 (CRITICAL) — Pinot recortaba en silencio toda consulta sin `LIMIT`.**
Pinot aplica un `LIMIT 10` implícito cuando la consulta no declara uno, y la respuesta no
distingue "hay 10 filas" de "hay 10 de 500". 31 consultas del repositorio no declaraban
tope, así que los repositorios filtraban y paginaban en Python sobre un recorte arbitrario
(sin `ORDER BY`, ni siquiera estable entre llamadas). Efecto verificado en el entorno real:
con 13 accidentes activos el listado mostraba 10, y filtrar por severidad operaba sobre ese
recorte. Corregido en `backend/core/pinot/client.py`: `PinotClient.query` añade un tope
explícito (`DEFAULT_QUERY_LIMIT`) cuando el SQL no trae uno, respetando los `LIMIT` propios.
Regresión en `backend/tests/regression/test_pinot_client_limit.py`.

**D2 (HIGH) — `Dim_Usuario_Cliente` y `Dim_CondadoVecino` no existían.**
Ambas se consultaban desde código productivo pero no estaban declaradas en
`database/esquemas.json` ni creadas en Pinot (`TableDoesNotExistError`).
`GET /api/v1/cliente/expedientes` respondía **500** y CU-O34 (escalamiento a condados
vecinos) fallaba al buscar adyacencias. Declaradas en `database/esquemas.json` y
`database/tablas.json`, sembradas por `database/seed_vinculos.py`.
**Causa de que los tests no lo detectaran:** el doble en memoria de `conftest.py` sí tenía
ambas tablas — el doble era más completo que la base real.

**D3 (MEDIUM) — `seed_soporte.py` publicaba `Dim_Usuario_Cliente` sin su clave primaria.**
El registro entraba con el centinela de nulo de INT y convivía como fila huérfana junto al
vínculo real. Corregido; `database/seed_flota_demo.py` retira las filas ya escritas así.

### Backend

**B1 (HIGH) — Paginación real en SQL en lugar de recorte en memoria.**
`AccidenteRepository.list_activos` traía la tabla y filtraba en Python. Reescrito para que
filtros, orden y tope viajen en el SQL, con paginación keyset por `idaccidente` y
`(filas, cursor_siguiente)` como retorno. `ConsultaAccidenteService.listar` encadena
páginas acotadas solo cuando el filtro por estado (que vive en otra tabla) deja la página
corta, con techo `MAX_PAGINAS_ENCADENADAS`. `HistorialEmergenciasService` lee por bloques
(`_leer_accidentes`) en vez de `SELECT * FROM Fact_Accidente`; además ordenaba por
`horainicio` mientras paginaba por `idaccidente`, lo que dejaba huecos entre páginas —
ahora ambas usan la misma clave. `GET /api/v1/accidentes` expone
`meta.pagination.next_cursor` y acepta `cursor`. Único escaneo amplio que se conserva:
`find_nearby` (agrupación de duplicados), acotado ahora por ventana temporal en el SQL.

**B2 (HIGH) — Rollback silencioso en importación de lote de unidades.**
`importacion_lote_unidad_service.importar` compensaba con
`unidad_repo.update(id, {"activo": False})` sin `base`, lo que releía de Pinot un registro
recién escrito por Kafka y todavía no ingerido; `update()` devolvía `None` en silencio y el
rollback no hacía nada. Dejó en la base 6 unidades activas apuntando a un `idusuario` que
nunca se persistió (no pueden iniciar sesión: CU-O30 `find_by_usuario`). Corregido pasando
el registro creado como `base`. Regresión:
`test_importar_when_credencial_falla_y_pinot_aun_no_ingirio_igual_revierte`.

**B3 (HIGH) — Filtro de flota por tipo de unidad siempre vacío.**
`UnidadEmergenciaRepository.list_active` filtraba por `idtipounidad`, columna que no existe
en `Dim_UnidadEmergencia` (la real es `tipounidademergencia`, texto). Cualquier filtro por
tipo devolvía cero unidades. Corregido en repositorio, servicio y vista; el endpoint acepta
`tipo` y mantiene `idtipounidad` como alias. La respuesta ahora expone
`tipounidademergencia` y `placa`.

**B4 (MEDIUM) — `idaccidente_duplicado_sugerido` retirado del contrato 409.**
El backend lo emitía siempre `null` y el frontend nunca lo usaba (fusiona sobre
`idaccidente_similar`, el reporte ya registrado; el duplicado rechazado por el 409 nunca
llegó a crearse). Retirado de `accidente_views.py`, del OpenAPI de `registro-accidente` y
del `spec.md` correspondiente.

**B5 (MEDIUM) — Motivo ilegible al sincronizar evidencia offline.**
`SincronizarEvidenciaService` capturaba `KeyError` y reportaba al técnico el nombre crudo
de la clave (`'estadoimplicado'`). Se agregó `_exigir_campos`, que nombra qué falta y en
cuál ítem local.

### Frontend

**F1 (HIGH) — «Mis expedientes» llevaba a una página de detalle sin `idaccidente`.**
`nav-links.ts` apuntaba a `/seguimiento/expedientes`, que cargaba `DetalleExpedientePage`
(un stub) sin parámetro: renderizaba un encabezado vacío y no pedía nada. Se creó
`ListaExpedientesPage` (listado con los tres estados, paginación por cursor y acción `eye`)
y se implementó `DetalleExpedientePage` con el chrome de workpanel del golden sample.

**F2 (MEDIUM) — La ruta `/` ignoraba la sesión.**
Redirigía siempre al portal comercial público, así que un usuario autenticado que escribía
la URL base veía "Iniciar sesión / Registrarme". Nuevo `landingRedirectGuard` que resuelve
al home del rol (misma función `homePathForRoles` que usa el login).

**F3 (MEDIUM) — `plan-detalle` fingía solo lectura con `input disabled readonly`.**
Prohibido explícitamente por el design-system, sección 5 ("en modo Ver, datos como `dl`…
nunca `input disabled`"). Reescrito al chrome del golden sample: «Volver a la lista» con
`arrow-left`, eyebrow de modo, `h1` + badge en la misma fila y datos en `dl` con `dt`
uppercase.

**F4 (LOW) — Homogeneización de estados asíncronos.**
`validacion.page.ts` mostraba la tabla de historial solo si había datos: sin skeleton, sin
error y sin vacío — "todavía no se pidió" y "vino vacío" se veían igual. Migrado a los
componentes canónicos `app-list-*`. Se homogeneizó `data-testid="error"` →
`data-testid="error-state"` en `evidencia-unidad`. Se agregó `download` al set Tabler
(`tabler-icon.component.ts`) en vez de introducir un ícono fuera del set único del sistema.

**F5 (LOW) — Paginación visible en la lista de accidentes.**
La lista pedía 20 registros y no ofrecía avanzar. Se agregó el paginador Anterior/Siguiente
con la misma convención que `catalogo-planes`
(`btn-pagina-anterior`/`btn-pagina-siguiente`), apoyado en el cursor real del backend;
cambiar un filtro reinicia la paginación.

### Suites de prueba

- **La suite backend no arrancaba**: `apps/accidentes/` no tenía `__init__.py`, así que
  pytest nombraba `apps/accidentes/tests/` como el módulo top-level `tests` y su
  `conftest.py` como el `conftest` raíz — 16 módulos fallaban al importar `PINOT_STORE` y
  la sesión se interrumpía por errores de colección. Agregados los `__init__.py` faltantes.
- `pytest.ini` tenía `testpaths = apps`, así que `backend/tests/` (incluida la regresión de
  la cadena crítica) nunca se ejecutaba. Ahora `testpaths = apps tests`.
- Los contadores de throttling de DRF persistían entre tests (viven en el caché de Django);
  un test que agotaba un scope hacía fallar con 429 a los posteriores según el orden de
  colección. Nuevo fixture autouse `reset_throttle_history` en `conftest.py`.
- El doble de Pinot se actualizó para honrar los predicados nuevos (filtros, cursor, orden
  y `LIMIT` de accidentes y flota). Sin eso los tests dejaban de medir lo que hace Pinot.

### Higiene de datos (entorno demo)

`database/higiene_datos.py` (idempotente, con `--dry-run`): desactiva unidades de prueba de
humo y unidades huérfanas (residuo de B2), consolida el rol `Unidad` duplicado (idrol 4 y 7
→ 4; los permisos se evalúan por nombre, así que el acceso no cambia) y sanea descripciones
de accidente con contenido ofensivo cargado como dato de prueba.
`database/seed_flota_demo.py` repone una flota mínima consistente (una unidad por usuario
con rol Unidad, correctamente ligada) y retira los vínculos usuario-cliente con clave
centinela.

### Verificación realizada

- Backend: `pytest` → 901 pasan, 2 skipped (antes: la suite no arrancaba).
- Frontend: `ng test` → 312 pasan (antes: 285 pasaban, 9 fallaban).
- Recorrido end-to-end contra el stack real: 34/34 pasos, incluido el recorrido paginado
  completo (13 filas en 5 páginas, sin repetidos ni faltantes) y los controles de acceso.

---

## 2026-07-31 (2) — Acceso denegado, unificación de credenciales y paginación de históricos

Alcance: `Cuentas-Clientes`, `despacho-inteligente`, `seguimiento-cierre-de-casos`,
infraestructura de datos y seeds (`database/`, `backend/scripts/`).

Continuación de la entrada anterior, sobre las dudas que quedaron abiertas allí.

### Frontend

**F6 (HIGH) — Ruta `access-denied` inexistente: 28 guards caían al portal público.**
Todos los guards de rol redirigen a `/cuentas-clientes/auth/access-denied` cuando la
sesión es válida pero el rol no alcanza. Esa ruta nunca se declaró, así que el
wildcard `**` capturaba la navegación y llevaba al portal comercial, donde el usuario
veía "Iniciar sesión / Registrarme" y parecía que se le había caído la sesión.
Creada `AccessDeniedPage` y registrada **dentro del shell autenticado**, para que el
usuario conserve su navegación: muestra la sesión vigente (correo + roles) y un CTA
«Volver a mi inicio» que resuelve con `homePathForRoles`, la misma función del login.
Los guards no se tocaron: estaban bien, faltaba el destino.

### Backend

**B6 (HIGH) — `get_current_estado` decidía el estado de una unidad sobre 10 filas.**
`HistorialEstadoUnidadRepository.list_by_unidad` traía sin `LIMIT`, ordenaba en Python
y devolvía el primero. Con el recorte implícito de Pinot (ver D1), el estado vigente
de una unidad se calculaba sobre 10 filas arbitrarias de su historial: una unidad con
más de 10 cambios de estado podía reportar uno viejo y quedar mal clasificada para
despacho. Orden, cursor y tope ahora van en el SQL.

**B7 (MEDIUM) — Traza GPS sin paginación.**
`Dim_HistorialUbicacionUnidadEmergencia` es la tabla que más rápido crece (una posición
cada ~10 s por unidad en misión ≈ 2.900 filas por jornada). `list_by_unidad` la leía
entera y sin tope, así que Pinot devolvía 10 puntos: el job de depuración GPS decidía
qué conservar mirando solo los 10 primeros, y la histéresis de geofence evaluaba la
llegada con una traza truncada. Ahora `list_by_unidad` pagina por keyset con ventana
temporal en el SQL, y `iter_by_unidad` recorre la traza completa por bloques para los
consumidores que sí la necesitan (`gps_depuracion_service`, `registrar_posicion_gps_service`).

**B8 (MEDIUM) — `estadocredencial` unificado a "Activo".**
Convivían "ACTIVA" (seeds) y "Activo" (código). El login no lo notaba porque solo
bloquea "Inactivo", pero `onboarding_service` exige `== "Activo"` y por tanto rechazaba
la credencial de **todos** los usuarios sembrados. Valores canónicos centralizados en
`credential_repository.py` (`ESTADO_CREDENCIAL_ACTIVO/INACTIVO/CAMBIO_PASSWORD`),
literales sueltos reemplazados en servicios y seeds, y las 12 filas ya escritas
migradas con `database/migra_estadocredencial.py`.

### Seeds y datos demo

**S1 (HIGH) — Dos convenciones de contraseña y un fixture E2E apuntando a la nada.**
`database/seed_usuarios.py` sembraba "Demo1234!" y `backend/scripts/*` "password123":
la misma cuenta pedía una u otra según cuál hubiera corrido último. Además
`e2e/fixtures/auth.fixture.ts` usaba cuentas `@tsi.com` tomadas de `backend/conftest.py`
—fixtures en memoria de los tests unitarios— que no existen en ningún entorno real, así
que todos los tests de Playwright fallaban en el login. Nuevo módulo compartido
`backend/scripts/_demo_seed_common.py` (`DEMO_PASSWORD`, `ESTADO_CREDENCIAL_ACTIVO`,
`DEMO_DOMAIN`), consumido por todos los seeds; fixture E2E reescrito con las 10 cuentas
reales y la contraseña como constante. Verificado: 10/10 autentican.

**S2 (HIGH) — Catálogos de roles superpuestos entre seeds.**
`database/seed_usuarios.py` definía idrol 4 = "Operador" y `seed_demo_usuarios_roles.py`
creaba otro "Operador" en idrol 11. Como `Dim_Rol` es upsert por clave primaria, el
segundo seed no agregaba: renombraba el rol de los usuarios ya vinculados al id que
pisara. De ahí el rol `Unidad` duplicado que la higiene consolidó y que reaparecía en
cada re-seed. Catálogo canónico único en `_demo_seed_common.ROLES_DEMO` + búsqueda
inversa `ROL_ID_POR_NOMBRE`; ambos seeds lo consumen.

**S3 (HIGH) — `seed_demo_director_estrategia.py` sobrescribía al Gerente de Ventas.**
Hardcodeaba `USER_ID = ROLE_ID = CRED_ID = 12` y `USER_ROLE_ID = 31`, exactamente los
del Gerente de Ventas. Correrlo **borraba** `lucia.ramos.ventas`. Detectado en vivo al
ejecutarlo; usuario restaurado y el script pasa a asignar ids libres con `_siguiente_id`.

**S4 (MEDIUM) — Flota ligada a usuarios por id fijo.**
`seed_flota_demo.py` asignaba la unidad 2 a `idusuario=4`, asumiendo que ese usuario
tenía rol Unidad. Al unificar el catálogo de roles, el usuario 4 pasó a ser Operador y
la unidad quedó ligada a alguien que no puede iniciar sesión como unidad (CU-O30
`find_by_usuario` → 403 en `mi-despacho`). Ahora la flota se liga a los usuarios que
**realmente** tienen rol Unidad, resueltos por nombre de rol; se agregó un segundo
usuario Unidad al catálogo demo (`marco.silva.unidad`) para que el despacho pueda
demostrar selección de candidata y escalamiento de zona.

**S5 (MEDIUM) — `Dim_Preferencias_Cliente` vacía.**
`zonas_geograficas` define sobre qué condados el cliente ve expedientes (RN-SEG-005);
sin la fila, el filtro resolvía a cero condados y "Mis expedientes" salía vacío aunque
hubiera casos cerrados. Sembrada en `database/seed_vinculos.py`.

### Tests de infraestructura nuevos

- `tests/regression/test_doble_pinot_vs_esquemas.py` — compara el doble en memoria de
  `conftest.py` contra `database/esquemas.json` en ambos sentidos, y verifica que toda
  tabla consultada por código productivo esté declarada. Habría detectado D2 con el
  mensaje exacto (verificado quitando las dos tablas del esquema).
- `tests/regression/test_credenciales_demo_consistentes.py` — impide que vuelvan a
  divergir la contraseña demo, el valor de `estadocredencial`, el catálogo de roles y
  las cuentas del fixture E2E.

### Verificación realizada

- Backend: `pytest` → 912 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan.
- Recorrido end-to-end contra el stack real: **42/42 pasos**, incluyendo despacho manual
  creado sobre la candidata que ofrece el sistema, detección de duplicados devolviendo el
  caso similar, y los 12 usuarios demo autenticando con una sola contraseña.
- Navegador: página de acceso denegado conserva la navegación y muestra la sesión;
  «Mis expedientes» lista un expediente real y su detalle renderiza en `<dl>` sin inputs.

---

## 2026-07-31 (3) — Escalamiento de zona demostrable, evidencia paginada y limpieza de datos demo

Alcance: `evidencia-unidad` (backend), infraestructura de datos y seeds (`database/`,
`backend/scripts/`).

Cierra las dudas de la entrada anterior.

### Backend

**B9 (MEDIUM) — Galería de evidencias con el mismo bug de clase D1.**
`EvidenciaFotoRepository.list_by_accidente` traía `SELECT * FROM Dim_EvidenciaFoto
WHERE idaccidente = ...` sin `LIMIT`, y filtraba `sincronizado`, ordenaba y paginaba
en Python **después**. Pinot recortaba a 10 filas antes de que ese filtro se aplicara:
un accidente con más de 10 fotos podía perder evidencia real de la galería sin error
visible. Filtro, orden y tope ahora viajan en el SQL. Regresión con 15 fotos
verificando que las 15 aparecen, más un recorrido paginado sin repetidos ni faltantes.

### Datos demo

**S6 — `rename_demo_unidad_gmail.py` eliminado.**
Era un one-shot que renombraba `diego.ramirez.operador@demo.tsi.com` →
`...unidad@demo.tsi.com`, contradiciendo el catálogo canónico donde el usuario 4 es
Operador. Sin referencias en el resto del repo.

**S7 — Tercera unidad y condado vecino con flota propia.**
El condado 2 (Benito Juárez) existía solo en `Dim_CondadoVecino` como adyacencia, sin
`Dim_Condado`/`Dim_Ciudad`/`Dim_Calle` propios ni unidades: todo escalamiento CU-O34
resolvía "sin unidades disponibles" aunque la consulta de adyacencia funcionara.
Agregados en `database/seed_catalogos.py` (condado, ciudad y calle de Benito Juárez) y
`database/seed_usuarios.py` (tercer usuario `valeria.cortes.unidad@demo.tsi.com`,
rol Unidad). `seed_flota_demo.py` ahora liga cada unidad a su `idcondado` propio y
resuelve los usuarios **por nombre de rol**, no por id fijo — antes asumía que
`idusuario=4` tenía rol Unidad; al unificar el catálogo de roles (ver S2 en la entrada
anterior) ese usuario pasó a ser Operador y la unidad quedaba huérfana.

Verificado end-to-end: con la flota del condado 1 agotada, escalar a zona (CU-O34)
encuentra y asigna la unidad 3 en Benito Juárez (`origen: "Escalado_zona"`), en vez de
reportar siempre "sin unidades en condados vecinos".

**S8 — `database/reset_despachos_demo.py` (nuevo).**
Cada corrida de flujo end-to-end deja despachos activos y unidades `Ocupada`/`En
Misión`; con una flota de 2-3 unidades eso agota las candidatas disponibles en pocas
corridas. El script libera los despachos activos y devuelve las unidades a `Activa`
sin tocar el estado del caso (`Fact_Accidente`) — no reemplaza un cierre real, es
mantenimiento de la flota demo. Idempotente, acepta `--dry-run`.

### Verificación realizada

- Backend: `pytest` → 914 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan (sin cambios en esta entrada).
- Recorrido end-to-end contra el stack real: **45/45 pasos**, incluyendo el camino
  completo de CU-O34 (condado local agotado → escalamiento → asignación exitosa en
  el condado vecino), verificado también en el navegador (Monitoreo de despacho
  muestra el caso escalado).

---

## 2026-08-01 — Homogeneización de estados loading/error/vacío en el frontend

Alcance: `despacho-inteligente`, `evidencia-unidad`, `seguimiento-cierre-de-casos`,
`Soporte-Cliente`, `Suscripciones-Facturacion` (frontend), `.specify/docs/design/design-system.md`.

Refactor de mantenibilidad, no corrección de bug ni de diseño: las páginas afectadas ya
cumplían el design-system (mostraban los 3 estados no felices correctamente), pero cada
una reimplementaba el mismo HTML que `app-list-loading-skeleton` / `app-list-error-state` /
`app-list-empty-state` ya encapsulan — visualmente indistinguible del golden sample, con
el costo de tener el mismo patrón duplicado en ~10 archivos.

### Migradas a los componentes compartidos

| Página | Loading | Error | Vacío |
|---|---|---|---|
| `despacho/mi-despacho` | ✓ | ✓ | ✓ |
| `despacho/monitoreo-despacho` | ✓ | ✓ | — (detalle, no aplica) |
| `evidencia-unidad/panel-disponibilidad` | ✓ | ✓ | — (detalle, no aplica) |
| `seguimiento/historial-emergencias` | ✓ | ✓ | ✓ |
| `seguimiento/mi-seguimiento` | ✓ | ✓ | ✓ |
| `soporte-cliente/detalle-ticket` | ✓ | — (sin error propio) | — |
| `soporte-cliente/mis-tickets` | ✓ | — (usa toast, no bloque) | ✓ |
| `suscripciones/plan-form` | ✓ | — (error de guardado sin retry, se deja inline) | — |
| `evidencia-unidad/galeria-evidencias` | — | — (semántica `alerta-media`, no crítica) | ✓ (con CTA proyectado) |
| `soporte-cliente/cola-agente` | — (skeleton de master-detail, forma propia) | — (banner persistente, no bloque) | ✓ |

Todos los `data-testid` (`loading-skeleton`, `error-state`, `empty-state`,
`btn-reintentar-lista`) se mantuvieron idénticos: **ningún spec de contrato de UI ni test
existente requirió cambios**, la migración es puramente de implementación.

### Deliberadamente dejadas sin migrar

- **`soporte-cliente/dashboard-soporte`** — grid de KPIs (design-system distingue
  "bloques de KPIs con ring charts" de listados; el skeleton de filas no representa la
  forma de una card de métrica).
- **`suscripciones/mi-suscripcion`** — tarjeta resumen con título propio
  ("No pudimos cargar tu suscripción") + descripción; el componente compartido es de una
  sola línea de mensaje, forzar el título ahí perdería información.
- **`cuentas-clientes/incorporacion-clientes/aprobacion-solicitudes`** — usa `@empty` de
  Angular dentro de una lista corta (una fila de texto), no un bloque de página completo.
- **`cuentas-clientes/auth/login`, `ventas-crm/registro-publico`** — falsos positivos de
  la búsqueda inicial: el `animate-pulse` detectado es el punto de estado "En vivo" del
  header, no un skeleton de carga.
- Errores con tono `alerta-media`/banner persistente en vez de bloque con "Reintentar"
  (`galeria-evidencias`, `cola-agente`, `dashboard-soporte`) se dejan inline: forzarlos al
  componente compartido cambiaría su severidad semántica (crítico vs. advertencia) o su
  patrón de interacción (bloqueante vs. banner conviviendo con datos).

### Regla añadida al design-system

Sección "Estados de carga, vacío y error": los componentes compartidos son la
implementación obligatoria para cualquier página con estos tres estados, no solo listados
Ver-only; reproducir el patrón con HTML propio solo se justifica cuando la forma del
contenido difiere genuinamente (KPIs, resumen con título) o el error no tiene una acción
de "Reintentar" con sentido.

### Verificación realizada

- Frontend: `ng test` → 316 pasan (sin cambios en el conteo — la migración no tocó ningún
  test, todos los `data-testid` se preservaron).
- `ng build` de producción sin errores nuevos.
- Recorrido end-to-end contra el stack real: 45/45 pasos.
- Navegador: `mis-tickets` (8 tickets, sin loading colgado), `mi-suscripcion` (renderiza
  sin errores) verificados tras el despliegue.

---

## 2026-08-02 — Limitaciones conocidas de los informes tácticos compuestos (`002-tactico`)

Alcance: `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`, hallazgos de la
revisión final contra el stack real. No son bugs — son decisiones de diseño forzadas por
huecos del esquema actual, documentadas aquí para no volver a proponerlas sin este
contexto (una ya se resolvió, ver entrada de más abajo).

**L1 — Semántica de `materializado` en los 3 informes compuestos.** Los DAGs
(`perdida_senal_gps`, `indice_calidad_historico`, `rendimiento_por_proveedor`) reprocesan
el histórico completo en cada corrida, no una ventana incremental. Consecuencia: una vez
que un DAG corrió al menos una vez, `materializado` es `true` para *cualquier* período
consultado (incluso uno futuro sin datos) — la ausencia de filas para ese rango se lee
como "sin eventos en ese período", no como "el DAG no lo ha procesado todavía". Si en el
futuro se necesita una ventana incremental (por volumen de datos), esta semántica cambia
y hace falta una lógica de "no materializado" por período explícita (ej. una tabla de
control de corridas por rango de fechas). No es necesario hoy — el volumen de datos del
proyecto no lo justifica.

**L2 — `rendimiento_por_proveedor` usa el proveedor *actual* de cada unidad, no el
histórico.** `Dim_UnidadEmergencia.idcliente` no tiene versión histórica (sin tabla tipo
SCD) — el DAG no puede saber qué proveedor operaba una unidad en el momento de un
despacho pasado si esa unidad cambió de proveedor después. Si el negocio necesita
atribución histórica correcta de rendimiento por proveedor (ej. para negociar contratos
según desempeño pasado), hace falta una tabla nueva `Fact_HistorialProveedorUnidad` (o
similar) que registre cada cambio de `idcliente` por unidad con su vigencia — no
implementada, es un cambio de esquema más grande que L3 (tabla nueva completa vs. un
campo en tabla existente).

**L3 — `idusuario` en `Fact_HistorialDespachoUnidad` — RESUELTO 2026-08-02.** Ver la
sección "Campo `idusuario` en `Fact_HistorialDespachoUnidad`" más abajo — esta limitación
ya no aplica.

---

## 2026-08-02 — Campo `idusuario` en `Fact_HistorialDespachoUnidad`

Alcance: `database/esquemas.json`, `backend/core/repositories/despacho/`,
`backend/core/repositories/informes_tacticos/seguimiento_repository.py`, `backend/conftest.py`.

Resuelve L3 de la entrada anterior: el informe táctico "% de cierres forzados sobre total
de cierres" (`informes-tacticos-simples`) aproximaba "forzado" con
`estadonuevo = 'Retirado'` sobre el total de transiciones a estado terminal, sin poder
distinguir un retiro hecho por un Operador de uno automático por vencimiento — la tabla
no tenía forma de saber quién (o si alguien) causó la transición.

**Cambio de esquema:** campo `idusuario` (INT, nullable) añadido a
`Fact_HistorialDespachoUnidad` — `NULL`/ausente cuando la transición es automática
(sistema), poblado con el id del operador cuando la transición la causa una acción humana
explícita (ej. retiro forzado desde central).

**Cambio de código:** ver detalle en `traceability.md` de
`specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/` — repositorio de
escritura de historial de despacho actualizado para aceptar `idusuario` opcional, caso de
uso de retiro de despacho actualizado para pasar el id del operador actuante, y
`cierres_forzados()` reescrito para calcular "forzado" como `estadonuevo='Retirado' AND
idusuario IS NOT NULL` en vez de la aproximación anterior.

---

## 2026-08-13 — Soporte §3.7: B43 (tickets sin plazo y sin decirlo), B44 (el sistema firmaba como el supervisor) y F20

Alcance: `backend/apps/soporte_cliente/` (constantes, registro, reapertura, monitoreo),
`frontend/src/app/modules/soporte-cliente/` (+ pruebas). SRS §3.7.1 y R-03.

**B43 — un ticket clasificado podía quedarse sin compromiso de tiempo, en silencio.**
Registrando un ticket como `ana.torres.cliente` salió `prioridad: crítico`,
`estado: Abierto` y **`sla_status: null`**. La causa: su suscripción está *Cancelada*, así que
`AsignacionSLAService` no encuentra plan, devuelve `None`, y el ticket se guardaba sin plazo y
**sin ninguna marca**. En la cola se veía igual que cualquier otro; el vigilante de SLA lo
descarta por `idslaconfig is None` y nunca lo marca en riesgo ni lo escala.

El SRS solo admite un caso en que el contador no arranca —el ticket **sin clasificar**—, y le da
un estado propio (`Pendiente_de_clasificacion`) precisamente para que se vea. Aquí había un
tercer caso no declarado e invisible. Lo grave no es la ausencia de plazo, que puede ser
correcta: es que se presentaba como un ticket cronometrado.

Corregido con `sla_status = "sin compromiso"` cuando el ticket está clasificado pero no hay regla
aplicable —en el alta, en la clasificación manual y en la reapertura, donde además impide
conservar un «en curso» viejo que ya nadie vigila—. La cola lo destaca en ámbar y el detalle
explica el motivo. El vigilante sigue ignorándolos, pero ahora por una rama explícita.

> **Queda una decisión de negocio, no técnica** (anotada en `decisiones-pendientes.md`): si un
> cliente **sin suscripción activa** debe tener compromiso de tiempo en soporte, y con qué plan.
> Hoy no lo tiene y ya se ve; qué *debería* ocurrir no lo dice el SRS.

**B44 — el escalado automático quedaba firmado por el supervisor.** `MonitoreoSLAService`
escribía la bitácora con `idusuario=supervisor_idusuario`, de modo que decía que **él** había
escalado el ticket. R-03 del SRS: "cuando la ejecuta un proceso automático, se registra
explícitamente como acción del sistema, **lo que permite distinguir una decisión humana de una
automática**"; §3.7.1 lo repite para este caso concreto. El supervisor es el **destino**, y su
sitio es `id_agente_asignado`, no el campo de autor. Corregido y verificado contra el stack real:
tras forzar el vencimiento del ticket #14 el barrido deja
`escalado_automatico_sla | idusuario: None` y el supervisor sigue asignado.

**F20 — el historial se leía como código.** Se pintaba el `tipo_accion` crudo
(«escalado_automatico_sla») y un guion donde va el autor. Con eso, B44 era además
indetectable a simple vista: un guion se lee como dato que falta, no como «lo hizo el sistema».
Añadido `historial-ui.ts` con frases legibles por acción y la marca **«Sistema»** en las entradas
sin autor humano —el vigilante de SLA y el cierre automático—. Verificado en el navegador:
*"Escalado automáticamente por incumplimiento de SLA · Sistema"*.

**Resto de §3.7 recorrido y sin defecto**: la regla absoluta de clasificación —un ticket ligado a
un caso de emergencia activo sale **crítico** aunque el texto sea trivial: probado con "Consulta
sobre el color del botón" sobre un caso vivo—; el ticket sin clasificar no arranca contador; las
**notas internas no llegan al cliente** (filtradas en la API, no solo en la UI); la reapertura
**no crea un ticket nuevo** y conserva el historial (#7: `cierre_confirmado` + `reapertura`, mismo
agente); el escalado conserva la titularidad; y modificar un SLA **no edita**: el PATCH responde
**201** creando `idslaconfig` nuevo y cierra el anterior con `activo=false` y
`fechavigenciahasta`, de modo que los tickets viejos conservan el compromiso que estaba vigente.

Suites: backend **1673 passed, 2 skipped**; frontend **643 SUCCESS**.

---

## 2026-08-13 — §3.4 cerrada: B42 (los avisos de vencimiento no los enviaba nadie) y el ticket con nombre

Alcance: `backend/apps/partners/services/expiracion_credencial_service.py`,
`backend/apps/soporte_cliente/services/registrar_ticket_service.py` (+ pruebas).
SRS §3.4.1 y §3.4.2.

**B42 — «El sistema avisa antes del vencimiento y de nuevo al producirse»: no avisaba a nadie.**
`PartnerNotificacionService.notificar_proximo_vencimiento()` y `notificar_vencimiento()` estaban
escritos, redactados con cuidado y **con pruebas propias**… y **ningún código de producción los
llamaba**. `ExpiracionCredencialService` solo escribía la bitácora: `avisar_proximas_a_vencer()`
devolvía `avisadas: [23]` sin que saliera un correo. El partner se enteraba del vencimiento
cuando su integración empezaba a fallar contra el entorno de pruebas.

Por qué la suite no lo veía: las pruebas del notificador lo invocaban **a mano**, así que
comprobaban que el mensaje se redacta bien, no que alguien lo mande. Es la variante de laboratorio
del cuarto patrón (§6): la capacidad construida y la puerta sin cablear.

Corregido cableando ambos avisos en el servicio de expiración, con tres pruebas nuevas que
aseveran **que alguien se entera** —destinatario, nombre de credencial y días restantes— y una
cuarta que fija lo que no puede romperse: **un buzón caído no deja credenciales vencidas
operativas**. La expiración es un control de seguridad, así que el envío va en su propio
`try/except` y el barrido termina.

**Detalle de §3.4.2 pendiente desde la pasada anterior.** El rechazo de una segunda disputa decía
solo *"La factura ya tiene una disputa abierta"*; el SRS pide indicar **cuál** es el ticket
existente "para que continúe la conversación ahí". Sin el número, el mensaje es un callejón sin
salida. Ahora nombra el ticket, y el portal ya lo muestra tal cual desde F19.

**Verificado contra el stack real:** republicada la credencial de sandbox del partner 970002 con
vencimiento a 3 días y ejecutado el barrido en el contenedor →
`AVISOS ENVIADOS: [('api.rescateandino@demo.tsi.com', 'integracion-andina…', 3)]`. Antes de la
corrección, la misma ejecución devolvía `avisadas: [23]` y no enviaba nada.

**Resto de §3.4 revisado y sin defecto**: la instantánea del estado del partner en cada llamada,
el ciclo de avisos de mora (T-10/T-5, sin duplicar, y el ciclo se cierra si regulariza), las
alertas de cuota al 80 %/100 % que llegan **también al Desarrollador de APIs** y nunca mencionan
interrupción del servicio, y la regeneración del sandbox por autoservicio tras vencer —el plan y
el registro se conservan, el nombre queda libre al desactivarse la vencida, y el portal tiene el
formulario de emisión por entorno—.

> Dato de entorno, no defecto: la credencial `tablero-interno` (idcredencial 12, Sandbox) lleva el
> centinela del año 9999, que corresponde a producción. El código de emisión asigna bien la
> vigencia; es una fila sembrada a mano.

Suites: backend **1669 passed, 2 skipped**.

---

## 2026-08-13 — F18 y F19: el partner puede disputar, y el cliente tiene por dónde hacerlo

Alcance: `backend/apps/soporte_cliente/{permissions,views}.py`,
`frontend/src/app/modules/{soporte-cliente,suscripciones}/` (+ pruebas).
SRS §3.7 x §3.4.2.

**F18 — `PartnerIntegracion` recibía 403 al abrir un ticket.** El spec de Soporte listaba
como reportador solo al **Cliente**; el SRS dice que el partner puede registrar una disputa
sobre su factura. Resuelto a favor del SRS: es el mismo actor —quien recibe el servicio y
reclama—, solo que su relación con TSI pasa por la API en vez del portal, y la lectura
contraria dejaba la disputa de facturación sin nadie que pudiera abrirla desde su lado.
`ROLES_REPORTADORES = {Cliente, PartnerIntegracion}`, y la tabla de actores del spec ahora lo
recoge.

**Lo que casi se cuela con ese cambio:** el acotamiento de las vistas se decidía con
`roles == {ROL_CLIENTE}`. Admitir al partner sin tocar esa igualdad lo habría dejado **fuera
del filtro de propiedad**: viendo tickets de otros clientes y notas internas. Se sustituyó por
`es_solo_reportador(roles)` —"no tiene ningún rol de atención"— en las tres vistas que lo
usaban, con prueba dedicada: un partner de otro cliente recibe 403.

**F19 — la capacidad existía y el cliente no tenía puerta.** El formulario de «Registrar
nuevo ticket» no tenía campo `idfactura` y el detalle de factura no ofrecía disputar, así que
RF-O83.2 —y la exclusión del cobro que acababa de arreglarse en B41— eran inalcanzables desde
la UI. Añadidos:

- **«Disputar este cargo»** en el detalle de factura, que es donde el cliente está mirando el
  importe. Solo cuando queda cobro pendiente; si ya está en disputa, en su lugar se explica
  que el cobro está detenido, porque ofrecer el botón solo llevaría al 422 de RN-TIC-008.
- **Selector «Factura en disputa»** en el formulario, que llega preseleccionado desde ese
  enlace y lista solo facturas disputables.
- El texto dice **qué hace**, no qué es: "el cobro automático de ese importe se detiene hasta
  que se resuelva el ticket". Es la razón por la que alguien rellena el campo.
- El error del backend se muestra tal cual: antes un 422 de "esa factura ya tiene una disputa
  abierta" se convertía en "Error al registrar el ticket" y el cliente reintentaba a ciegas.

De paso, el tipo `EstadoPagoFactura` del frontend **no conocía `'En disputa'`**: el backend ya
podía dejar la factura en ese estado y la UI lo pintaba como estado desconocido, sin explicar
por qué el cobro se había detenido. Añadido, con badge informativo (no de error: está detenido
a propósito).

Verificado contra el stack real desde el navegador: el detalle de factura ofrece disputar y
enlaza con la factura; el formulario llega preseleccionado y envía `idfactura`; el 422 de
disputa duplicada se ve con su motivo real. Con el usuario partner: POST de ticket **201**
(antes 403), ve el suyo, **403** en el de otro cliente y su listado solo trae su `idcliente`.

Suites: backend **1665 passed, 2 skipped**; frontend **640 SUCCESS** (629 antes).

---

## 2026-08-13 — F17 y B41 corregidos: la credencial la emite quien la custodia, y la disputa congela el cobro

Alcance: `backend/apps/partners/services/promocion_produccion_service.py`,
`backend/apps/soporte_cliente/services/` (+ pruebas y contratos).
SRS §3.4.1 (onboarding de partners) y §3.4.2 x §3.7 (facturación x tickets).

**F17 — la aprobación emitía una credencial productiva que nadie podía usar.**
`PromocionProduccionService._aprobar()` llamaba a `EmisionCredencialService.emitir(...)`
y devolvía el `client_secret` en la respuesta del **Administrador**. Pero el delta
BE-DELTA-02 y la Clarification Q2 del frontend dicen textualmente lo contrario: el
secreto lo ve **quien lo custodia**, el partner, desde su portal; mostrárselo al Admin
lo obligaría a transmitirlo por un canal inseguro, que es justo lo que evita RN-PON-005.
El delta se implementó a medias: la consola descarta el secreto (FR-UI-009) y ningún
endpoint lo recupera después, así que **se generaba y se perdía**, dejando al partner con
una credencial de producción activa e inservible.

Corregido: la aprobación promueve y notifica, nada más. Devuelve
`credencial_pendiente_de_emision` (el nombre pedido) en lugar de `credencial`. Las dos
pruebas que aseveraban la emisión **codificaban el defecto**, no la regla: se reescribieron
contra Q2 —ahora comprueban que no hay `client_secret` en la respuesta y que no existe
todavía ninguna credencial de producción—. Alineados también `backend/spec.md` (la línea
que decía «Al aprobar se emite la credencial de producción») y el OpenAPI del módulo, que
contradecían a su propio delta.

**B41 — abrir una disputa no excluía la factura del cobro automático.**
`api-monitoring-and-billing` RF-APM-014 dice que una factura marcada en disputa **por
`gestion-tickets-soporte`** queda excluida del cobro y que «este módulo no abre ni resuelve
disputas: solo respeta la exclusión». Nadie ejecutaba ese marcado: el spec de Soporte
impone una sola disputa abierta por factura (RN, línea 198) pero **no menciona `estado_pago`
en ninguna parte**. Resultado: el cliente abría un ticket por un cargo y se le seguía
reintentando ese mismo cargo mientras lo discutía.

Corregido con `DisputaFacturaService` (nuevo): al registrar un ticket con `idfactura` se
republica la fila completa de `Fact_Factura` con `estado_pago = 'En disputa'`, y al cerrarse
el reclamo vuelve a `'Pendiente'`. Dos decisiones que importan:

- **No se inventó un flag propio.** Se usa `estado_pago` porque es la columna que ya
  consultan *todos* los cobradores —`TarificacionExcedenteService.en_disputa()`,
  `CobroService`, el job de dunning y la mora de suscripción— y todos exigen `'Pendiente'`.
  La exclusión sale gratis y no hubo que tocar ninguno de ellos.
- **La liberación va en los dos caminos de cierre**, no solo en la confirmación del cliente:
  un ticket auto-cerrado a los 5 días (RN-TIC-004) habría dejado la factura excluida del
  cobro para siempre. Y no pisa una factura que la resolución ya dejó `Pagada` o ajustada
  —RF-APM-014 dice «pagada o con monto ajustado según la resolución»—.

El marcado ocurre **después** de crear el ticket: si se marcase antes y la creación fallara,
la factura quedaría congelada sin reclamo que la respalde.

Cerrada además la brecha documental que originaba el defecto: `gestion-tickets-soporte/backend/spec.md`
ahora asigna explícitamente esa responsabilidad (RN-TIC-DISPUTA).

Verificado contra el stack real desde el navegador: `ana.torres.cliente` abre un ticket con
`idfactura` → Pinot pasa la factura a `En disputa` conservando `monto_total` y el resto de
columnas (la tabla es upsert: se republica la fila entera); el agente la resuelve, la
cliente confirma el cierre desde su portal y la factura vuelve a `Pendiente`.

Suites: backend **1661 passed, 2 skipped** (1655 antes, +6 nuevas). Frontend sin cambios.

**Hallazgo derivado, no corregido (F19):** el formulario de «Registrar nuevo ticket» del
portal del cliente **no tiene campo `idfactura`**, y el detalle de factura en
`suscripciones/historial-facturas` no ofrece «disputar». La capacidad existe en el backend
(y ahora congela el cobro), pero el cliente no tiene por dónde ejercerla desde la UI —el
mismo patrón «permiso concedido, puerta inexistente» de §6—. Anotado en `REVISION-SRS-ESTADO.md`.

---

## 2026-08-13 — Partners §3.4.2: B40 corregido (el job de excedente moría), B41 y F18 abiertos

Alcance: `backend/apps/partners/services/tarificacion_excedente_service.py` (+ pruebas).
SRS §3.4.2.

**B40 — la facturación de excedente no ocurría nunca.** El servicio agendaba y consultaba los
reintentos por una columna **`proximo_reintento` que no existe en `Fact_Factura`** (verificado
contra `database/esquemas.json`: la tabla tiene `reintentos` y `resultado_ultimo_reintento`).
Al escribir, Pinot descartaba el campo en silencio; al leer, **rechazaba la consulta entera**,
así que `run_facturacion_excedente_job` **abortaba con `RuntimeError` en cada ejecución**.
Efecto: ninguna factura de excedente se emitía y ningún reintento se recogía — justo el
"ingreso real no cobrado" que el SRS declara inaceptable. Es el mismo error que el código ya
documentaba haber cometido con la columna `monto` y que se creía aislado.

Corregido **sin tocar el esquema**: el vencimiento se **deriva** de `reintentos` +
`fecha_actualizacion`, que sí se persisten, y ya no se publica el campo fantasma.

**Tres pruebas codificaban el defecto**, incluido el ayudante `_factura()`, que fabricaba
filas con `monto` y `proximo_reintento` —columnas inexistentes— y por eso el doble las
aceptaba tan felizmente. Reescritas contra el esquema real, más una regresión que **asevera el
payload publicado** para que no vuelva a colarse una columna fantasma.

**Verificado contra el stack real:** el job completa (`evaluados: 4, emitidas: 0, ya emitidas:
2, omitidas: 2`), y **no duplica**: una segunda ejecución sobre el mismo período no emite nada,
que es la regla de no duplicación de RF-APM-012. La **cola de excepciones** muestra la factura
con los tres reintentos agotados, su último resultado y la acción sugerida —"Emitir la factura
manualmente"—, que es el "pendiente de emisión manual" del SRS.

**B41 — abrir una disputa no marca la factura, así que no la excluye del cobro.** Comprobado:
el ticket se crea y queda vinculado (`idfactura`), pero `Fact_Factura.estado_pago` sigue en
`Pendiente`. El mecanismo de exclusión existe —`en_disputa()` filtra los reintentos de las que
estén `En disputa`— pero **nadie escribe ese estado**, de modo que una factura en disputa se
sigue reintentando. SRS §3.4.2: *"Abrir la disputa marca la factura como en disputa, lo que la
excluye explícitamente de los intentos de cobro automático"*. **No corregido por falta de
margen en esta sesión**; queda anotado como lo siguiente a atacar.

**F18 — el partner no puede abrir la disputa.** `TicketsView` exige rol `Cliente`, `Soporte` o
`Administrador`: con el rol `PartnerIntegracion` responde **403**. El SRS dice que *"el partner
puede registrar una disputa sobre un consumo o una factura"*. Puede ser un permiso que falta o
una decisión de que la disputa la abra la cuenta cliente; **queda para decidir**.

**Regla verificada con un rol autorizado:** una segunda disputa sobre la misma factura se
rechaza con `422 "La factura ya tiene una disputa abierta"`. Matiz: el SRS pide que además
**indique cuál es el ticket existente** "para que continúe la conversación ahí", y el mensaje
no lo nombra.

Suites: **backend 1654 passed, 2 skipped**; frontend sin cambios (629).

---

## 2026-08-13 — Partners §3.4.1: ruta de onboarding recorrida entera + hallazgo F17 (pendiente de decisión)

Alcance: verificación, sin cambio de código. Datos sembrados para poder recorrerla. SRS §3.4.1.

**Entorno sembrado** (no había forma de probar la ruta: el usuario partner demo resuelve al
partner que ya está en producción):

- Suscripción del cliente `Rescate Andino Norte` (920003) reactivada a `Activa` —estaba
  Cancelada de una pasada anterior—, con lo que pasó a ser cliente elegible.
- Partner **Rescate Andino API** (`idpartner 970002`) registrado desde la consola sobre ese
  cliente.
- Usuario **`api.rescateandino@demo.tsi.com` / `password123`** (idusuario 9010, rol
  `PartnerIntegracion`) vinculado al cliente por `Dim_Usuario_Cliente`. Se eligió el vínculo
  y **no** `admin_local_id` a propósito: sobrescribirlo habría desplazado a Teresa, que es la
  administradora local de ese cliente y se usa en las pruebas de Suscripciones.

**La ruta obligatoria se cumple, sin atajos** (SRS: *Registrado → Plan asignado → Pruebas
activo → Pendiente de aprobación → Producción activa*):

- **Sin plan no hay pruebas**: la interfaz ni siquiera ofrece el formulario, y el backend
  responde `409 sin_plan` — *"El partner no tiene plan de acceso asignado; no puede emitir
  credenciales"*.
- **Sin pruebas no hay producción**: `409 ruta_invalida` — *"La solicitud requiere estar en
  «Pruebas activo»; el partner está en «Registrado». No se puede solicitar producción sin
  haber pasado por el entorno de pruebas"*.
- **El cupo se deriva del plan del cliente**: al asignar plan quedó Básico, 1.000/mes y
  30/minuto, que es lo contratado por ese cliente.
- **La activación la ejecuta una persona**: el partner solicita; el Administrador resuelve
  desde la cola. El rechazo **exige motivo** (mínimo 15 caracteres) y avisa de que ese texto
  se le envía al contacto técnico.
- **El rechazo devuelve a «Pruebas activo», no a «Registrado»**, y **su credencial de pruebas
  sigue activa** — comprobado en la API y en Pinot—, que es justo donde el SRS quiere que
  corrija lo que motivó el rechazo.
- **No hay tope de reintentos**: la segunda solicitud se aceptó sin objeción.
- **Aprobada**, el partner queda en `Producción activa` y **las credenciales de los dos
  entornos coexisten**.

**F17 — el secreto de la credencial productiva no llega a nadie. Requiere decisión.** Al
aprobar, `PromocionProduccionService` **emite** la credencial de producción y devuelve su
secreto en la respuesta… **del Administrador**, que la consola deliberadamente no muestra
(*"no es de quien aprueba"*, FR-UI-009). Los endpoints del partner filtran `client_secret`
(`_CAMPOS_SENSIBLES`), así que **el secreto se genera y se descarta**: el partner termina con
una credencial productiva activa que no puede usar. La propia consola dice al aprobar *"lo
verá únicamente el partner al emitirla"*, cuando ya está emitida.

Hay salida —revocarla entrega un reemplazo y ese sí muestra su secreto—, pero es "revoca la
credencial que nunca usaste". **No se corrigió porque la salida correcta es una decisión de
producto**: o la aprobación no emite y el partner emite después (que es lo que la copia de la
consola promete), o el partner recibe el secreto en un paso de revelación única. Queda
anotado en el documento de revisión.

Alcance: `frontend/.../pages/cola-acceso/` (nueva), `frontend/.../detalle-partner.page.ts`,
`frontend/.../mi-integracion.page.ts`, `frontend/.../partner-api.service.ts`,
`frontend/.../models/partner.types.ts`, `frontend/.../partners.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts` (+ specs). SRS §3.4.3.

**Encargo del responsable:** construir las pantallas que `partner-access-management/frontend`
declaraba pendientes. Eran las que impedían ejercitar §3.4.3 desde la interfaz.

**1. Panel de suspensiones del Administrador** (RF-PAC-005 + RF-PAC-009 b), en
`/partners/consola/suspensiones`. Lista suspendidos y partners en ciclo de mora con sus días
y su último aviso, y permite reactivar. Sin él, la reactivación —que **solo** un Administrador
puede hacer y que el sistema **nunca** ejecuta solo (RN-PAC-009)— no tenía por dónde empezar:
había que ir partner por partner.

**2. Suspender y reactivar desde la ficha del partner.** Al construir el panel apareció que la
cola solo lista morosos y suspendidos, de modo que un Administrador **no podía suspender por
las otras causas que el SRS nombra** —vencimiento de contrato, petición del cliente—. La
acción vive también en el detalle del partner, visible solo para Administrador.

**3. El partner suspendido entiende por qué** (RN-PAC-016). El portal solo decía "Tu acceso
está suspendido. Contacta al administrador."; ahora muestra **motivo, fecha, días de mora e
historial de acceso**, y aclara que puede seguir consultando su pantalla y su consumo. El
endpoint `estado-acceso` ya existía y nadie lo llamaba; solo se pide cuando hace falta
explicar una suspensión.

**Verificado de punta a punta contra Pinot**, que era el objetivo: la **regla de cascada** no
podía probarse antes.

1. Suspendido *Integradora Andina* desde la ficha → *"Credenciales desactivadas: **2**"*.
2. Como partner, el portal muestra el motivo, la fecha y el historial —y no un mensaje seco—.
3. Reactivado desde el panel → *"Credenciales restituidas: **2**. Quedan **1** sin restituir a
   propósito: fueron revocadas por seguridad y resucitarlas sería un riesgo."*
4. En Pinot: `tablero-interno` y el reemplazo `plataforma-siniestros` vuelven a `activo = true`;
   la credencial **revocada** por el partner sigue `activo = false`. **Ninguna credencial
   comprometida resucitó**, que es el tie-breaker de seguridad del spec.
5. La bitácora registra `suspension_manual` y `reactivacion` con `ejecutado_por = Administrador`
   y sus estados anterior/nuevo.

También se formateó la fecha de suspensión, que salía como ISO crudo en la pantalla del
partner (misma familia que F4/F6).

Suites: **backend 1654 passed, 2 skipped** (sin cambios); **frontend 629 SUCCESS** (eran 616).

---

## 2026-08-13 — Partners y API §3.4: construida la revocación de autoservicio (alcance pendiente, no defecto)

Alcance: `frontend/.../partner-api.service.ts`, `frontend/.../models/partner.types.ts`,
`frontend/.../mi-integracion.page.ts` (+ spec). SRS §3.4.1, §3.4.2 y §3.4.3.

**Qué faltaba y por qué no es un defecto.** El endpoint
`POST /api/v1/credenciales/{id}/revocar` está implementado y probado en el backend —con su
doble guarda de propiedad, su idempotencia y su reemplazo inmediato— y **ninguna pantalla lo
llamaba**: el portal del partner solo ofrecía emitir y regenerar. A diferencia de F9/F12/F13/F15,
**esto estaba declarado**: `partner-access-management/frontend/spec.md` es un *stub* explícito
—"pendiente de especificar tras cerrar la capa backend"— que enumera las tres superficies que
faltan. Es alcance conocido sin construir, de la familia de §7.3, no una puerta que alguien
olvidara poner.

Se construyó igualmente **una** de esas tres superficies, la de revocación, porque la regla
que implementa es de seguridad y el SRS §3.4.3 la hace autoservicio a propósito: *"es reactiva
ante un incidente de seguridad, donde esperar autorización sería el peor comportamiento
posible"*. Un partner con una credencial filtrada no tenía forma de cortarla. **Las otras dos
siguen sin construir** y quedan anotadas: el estado de acceso propio accesible estando
suspendido (RN-PAC-016) y el panel de suspensiones del Administrador (RF-PAC-005) —sin él, la
regla de cascada de suspensión y reactivación no puede ejercitarse desde la interfaz.

Corregido: botón **Revocar** por credencial vigente, con confirmación en 2 pasos en tono
destructivo que explica que las demás credenciales seguirán operando, y el secreto del
reemplazo entregado en la pantalla que ya existía para eso —una sola vez, nunca por la URL—.
No se ofrece sobre credenciales vencidas, que se **regeneran**, no se revocan.

**Verificado contra el stack real.** Revocada `plataforma-siniestros` (producción) del partner
Integradora Andina: la credencial 11 quedó `activo = false`, se emitió la **22 con el mismo
nombre y entorno** y su secreto se mostró una vez; `tablero-interno` (sandbox) siguió intacta.
Por API se comprobaron las dos guardas: revocar una ya inactiva responde **409
"La credencial ya estaba inactiva"**, y una credencial ajena responde **404**.

**Reglas de §3.4 que ya cumplían, comprobadas en el navegador:**

- **Credenciales de pruebas y producción coexisten**: el portal muestra las dos secciones y
  dice explícitamente que activar producción no elimina el acceso de pruebas.
- **Superar la cuota no bloquea**: con el consumo al **150 %** del cupo, la pantalla informa
  *"Tu servicio no se interrumpe: el excedente se factura al cierre del período"* y estima el
  excedente. Es la regla que el SRS pide no "corregir" por error.
- **Separación de entornos**: el consumo se presenta acotado a **Producción**.
- **Autodiagnóstico**: los errores del partner se listan con su código, y los `429` aparecen
  marcados como *"No cuenta como consumo facturable"*.
- **Registro de partner por nombre de cliente**: el combobox se alimenta de clientes elegibles
  —con suscripción vigente y sin partner previo—, de modo que la regla "un solo partner por
  cliente" se previene en vez de explicarse con un 409.

**Nota de entorno, no defecto.** El portal era inalcanzable al empezar: `partner.demo@demo.tsi.com`
es administrador local del cliente `E2E Onboarding`, que una pasada anterior dio de baja, y el
guard de B9 rechazaba su login —correctamente—. Se reactivó ese cliente para poder recorrer el
módulo; queda anotado en el documento de revisión.

Suites: **backend 1654 passed, 2 skipped** (sin cambios); **frontend 619 SUCCESS** (eran 616).

---

## 2026-08-13 — §3.6.1 fusión de duplicados: B37, B38 y B39

Alcance: `backend/apps/accidentes/services/fusionar_reportes_service.py`,
`frontend/.../registro-accidente.page.ts`, `frontend/.../duplicado-fusion.dialog.ts`
(+ pruebas de servicio, de página y de integración). SRS §3.6.1.

La regla: *"El sistema o el operador fusionan el duplicado con el caso real: el duplicado queda
marcado como fusionado y apuntando al caso padre, que continúa su flujo normal sin alteración.
El duplicado no se borra: queda con trazabilidad completa hacia el caso que lo absorbió."*
Ninguna de las tres partes se cumplía.

**B37 — el diálogo proponía fusionar el caso real consigo mismo.** El 409 de duplicado devuelve
`idaccidente_similar` (el caso ya registrado) y `idaccidente_principal_sugerido` (el más
antiguo de los candidatos). Con un solo candidato —el caso normal— **ambos son el mismo caso**,
y `confirmarFusion` fusionaba `idaccidente_similar` como duplicado contra el id sugerido. Al
confirmar, el accidente vivo quedaba **apuntándose a sí mismo** (`idaccidenteorigen` = él
mismo), **desactivado** y en `FUSIONADO`: el caso real desaparecía del flujo. En la prueba en
vivo solo se salvó porque el guard lo rechazó por otro motivo (B39), no porque nada lo
impidiera. Añadida la guarda explícita en el servicio.

**B38 — el segundo reporte no llegaba a existir.** El 409 rechaza el alta, así que el reporte
duplicado nunca se creaba: la fusión operaba sobre el caso preexistente y el aviso nuevo se
perdía sin dejar rastro. El SRS pide justo lo contrario —"no se borra: queda con trazabilidad
completa"—. Ahora, al confirmar la fusión, el frontend **registra el reporte forzando la
advertencia** y fusiona **ese** caso contra el padre elegido.

**B39 — no se podía fusionar en el caso normal.** El servicio exigía `BORRADOR` o `REPORTADO`
**a los dos** casos. Pero el duplicado llega minutos después, cuando el caso real ya está
buscando unidad o asignado: exigirle ese estado al **padre** bloqueaba la fusión precisamente
cuando hace falta. Verificado en vivo antes del arreglo: `409 "Fusión no permitida para el
estado actual"`. Ahora la restricción de "sin despacho" recae sobre el **duplicado** —que es lo
que dice §3.6.1— y el padre solo se rechaza si está `CERRADO`, `DESCARTADO` o `FUSIONADO`.

**Una prueba que ejercitaba el defecto sin verlo.** `test_deshacer_when_fusionado_restores_activo`
llamaba a `seed_accidente()` dos veces **sin id**, así que ambos casos eran `ACC-SEED-1`: la
prueba fusionaba un caso consigo mismo y pasaba en verde. Se le dieron ids distintos.

**Verificado de punta a punta contra Pinot.** Registrado el caso padre (que el worker despachó
hasta `BUSCANDO_UNIDAD`) y después un segundo aviso en el mismo punto y hora: el diálogo se
abrió, y al fusionar el duplicado **quedó registrado** con `idaccidenteorigen` apuntando al
padre, `activo = false` y estado `FUSIONADO`; el padre siguió en `BUSCANDO_UNIDAD`, activo y
sin `idaccidenteorigen`. También se reescribió el texto del diálogo, que hablaba de "ID del
caso padre" sin explicar qué se fusionaba con qué.

Suites: **backend 1654 passed, 2 skipped**; **frontend 616 SUCCESS**.

---

## 2026-08-13 — §3.6.4 cerrada: F15, la escalada en sitio estaba en la pantalla equivocada

Alcance: `frontend/.../detalle-accidente.page.{html,ts}`,
`frontend/.../mi-seguimiento.page.{html,ts}`. SRS §3.6.4.

**F15 — la escalada de severidad no la podía hacer nadie.** El panel «Escalar severidad» vivía
en el **detalle del accidente**, que `accidentesLecturaGuard` reserva a Operador, Técnico y
Administrador; pero el endpoint `POST /accidentes/{id}/escalar-severidad` exige el rol
**Unidad** con unidad vinculada (`IsUnidadSeguimiento`). Resultado comprobado en el navegador:
el operador rellena el panel, confirma y recibe **403**; la unidad —el actor que el SRS pone
en el sitio: *"ya en el lugar, la Unidad puede escalar la severidad del caso con lo que
efectivamente observa"*— no tenía ninguna pantalla desde donde hacerlo. Cuarta vez que aparece
el mismo patrón en Emergencias (F9, F12, F13, F14): la capacidad existe, la puerta está en la
habitación equivocada.

Corregido: el panel pasa a **Mi seguimiento**, visible cuando la unidad ya registró su llegada.
En el detalle del accidente queda una nota que explica que la severidad en sitio la actualiza
la unidad y que los cambios se ven en el historial del expediente.

**Verificado contra el stack real** con `LOTE-A3` sobre `ACC-1786589824363-3100`: la escalada
pasó la severidad de **Grave a Fatal** con 3 heridos, y `Fact_HistorialSeveridadAccidente`
guardó el cambio con `idusuario = 9006` —el usuario de la unidad—, que es la constancia de que
la escalada ocurrió **en sitio** y no desde central.

**Cancelación de caso con unidad despachada, verificada** (cerraba §3.6.4): con la grúa en el
sitio, «Cancelar caso (falsa alarma)» retiró la unidad, **la devolvió a `Activa`**, registró
el motivo en `Dim_NotaAccidente` y cerró el caso por vía corta (`horafin`,
`duracionminutos = 602`, `activo = false`) **sin pedir documentación de evidencia**, tal como
describe el SRS.

Suites sin cambios: **backend 1651**, **frontend 615**.

---

## 2026-08-12 — §3.6.4 en trayecto: F14 (la constancia no se veía), B35 y B36

Alcance: `backend/apps/seguimiento/services/gps_senal_perdida_service.py`,
`backend/apps/despacho/services/{monitoreo_despacho_service,consulta_candidatas_service}.py`,
`backend/core/repositories/accidentes/nota_accidente_repository.py`, `backend/conftest.py`,
`frontend/.../monitoreo-despacho.page.html`, `frontend/.../despacho.types.ts` (+ pruebas).
SRS §3.6.4.

**Lo que ya cumplía, comprobado contra el stack real** (caso `ACC-1786589824363-3100`):

- **Rastreo en tiempo real**: la unidad envía su posición y `Dim_HistorialUbicacionUnidadEmergencia`
  acumula la **trayectoria** (dos puntos con coordenadas y marcas distintas), con el
  acotamiento de un envío cada 10 s.
- **Pérdida de señal**: el job la detecta pasado el umbral (60 s) y **la unidad sigue
  asignada** — `activo = true` —, que es justo lo que pide el SRS: "se perdió visibilidad de
  dónde está, no la responsabilidad sobre el caso".
- **Aborto de misión**: se registra, la unidad vuelve a `Activa` y **se dispara una nueva
  asignación** sobre el mismo caso, que no se abandona.
- **Expediente del cliente**: `ana.torres.cliente@demo.tsi.com` ve sus casos cerrados acotados
  a su zona contratada (condado 1), incluido el que se cerró en esta pasada.

**F14 — la constancia de señal perdida no se veía en ninguna parte.** El aviso se escribía en
`Dim_NotaAccidente`, pero **solo el expediente lee esas notas y el expediente exige el caso
CERRADO**: durante la emergencia —el único momento en que sirve— no aparecía ni en el detalle
del accidente ni en el monitoreo ni en la galería (que filtra a notas de campo). El SRS dice
que la pérdida de señal "deja constancia **visible para el operador**", y el propio
`FR-UI-017` del spec ya lo pedía. Añadido `alertas` al estado de monitoreo y una sección
**"Avisos del caso"** en la pantalla del operador, con la nota de que la unidad sigue
asignada.

**B35 — un aviso por ciclo, no por incidencia.** El job corre cada 30 s y **creaba una nota
idéntica en cada pasada**: en la prueba real se acumularon 17 avisos del mismo despacho en
diez minutos. Una unidad fuera de cobertura media hora habría enterrado el expediente —el
mismo que consulta el cliente— bajo sesenta avisos iguales. Ahora se avisa una vez por
interrupción: si ya hay un aviso posterior a la última posición conocida, el ciclo no repite.
Si la unidad reaparece y vuelve a perderse, sí se emite un aviso nuevo.

**B36 — la unidad que abortaba recibía el mismo caso otra vez.** Verificado en vivo: `LOTE-A2`
abortó por avería y la reasignación automática le devolvió el caso a **ella misma** (despacho
4312). El SRS define la reasignación como el mismo proceso "con una unidad **nueva**", y el
efecto práctico es que una unidad averiada podía recibir el caso indefinidamente. La consulta
de candidatas excluía a quien **rechazó** pero no a quien **abortó**. Corregido y comprobado:
tras el segundo aborto, el caso pasó a la unidad 18.

**Al doble le faltaban dos consultas** (§3 del handoff): la de la última alerta con `LIKE` y la
de listado de alertas. Sin enseñárselas, las pruebas de B35 no habrían visto nada.

Suites: **backend 1651 passed, 2 skipped**; **frontend 615 SUCCESS**.

---

## 2026-08-12 — §3.6.4 Cierre de casos: F13 (no existía ninguna acción de cierre), B33 y B34

Alcance: `backend/apps/seguimiento/services/{finalizar_atencion_unidad_service (nuevo),cerrar_caso_service}.py`,
`backend/apps/seguimiento/views/{mi_seguimiento_views,urls}.py`,
`backend/core/repositories/despacho/estado_accidente_despacho_repository.py`,
`frontend/.../monitoreo-despacho.page.{html,ts}` (+ spec nuevo),
`frontend/.../mi-seguimiento.page.{html,ts}`, `frontend/.../mi-seguimiento-api.service.ts`,
`frontend/.../seguimiento.types.ts`, y las pruebas que codificaban el comportamiento anterior.
SRS §3.6.4.

**Decisión de producto (usuario, 2026-08-12): lectura literal del SRS.** La unidad cierra su
propia parte; el cierre del caso lo hace el Operador y **solo cuando todas las unidades se han
retirado**; el retiro forzado desde central es la excepción y queda registrado como tal.

**F13 — no existía ninguna acción de cierre en toda la aplicación.** `cerrarCaso`,
`cancelarCaso` y `forzarRetiro` estaban implementadas en el backend y en el cliente de API,
y **ningún componente las llamaba**: solo las pruebas. Es decir, **un caso no podía cerrarse
desde la interfaz**, lo que explica que el entorno acumule casos vivos y ninguno cerrado. Las
pruebas de esas rutas pasaban en verde porque ejercitan el cliente HTTP, no la pantalla.
Construido en el monitoreo del caso: cerrar (con resultado y observaciones), cancelar por
falsa alarma, y **forzar retiro por unidad**, con la confirmación en 2 pasos del
`design-system.md` y el aviso explícito de que el retiro forzado no es una finalización normal.

**Nueva capacidad: la unidad termina su parte.** No existía forma de hacerlo — la unidad solo
podía registrar llegada o abortar—, así que la regla "todas las unidades retiradas" no tenía
camino normal por el que cumplirse. Añadido
`POST /api/v1/mi-seguimiento/despachos/{iddespacho}/finalizar` y el botón
**"Finalizar mi atención"** en *Mi seguimiento*. El retiro queda con `retiro_forzado = false`.

**B33 — el cierre retiraba a todos en silencio y como retiro normal.** `CerrarCasoService`
retiraba por su cuenta cualquier despacho que siguiera activo. Efecto: la regla que el SRS
llama la más estricta —*"un caso solo pasa a cerrado cuando **todas** las unidades se han
retirado. No existe el cierre parcial"*— **no llegaba a aplicarse nunca**, y las unidades que
seguían trabajando se registraban como finalización normal, borrando la distinción que el SRS
exige respecto del retiro forzado. Ahora el cierre responde 409 explicando cuántas unidades
faltan y qué hacer.

**B34 — el caso retrocedía de `EN_ATENCIÓN` a `ASIGNADO`.** `publish_asignado_if_first_confirmed`
solo comprobaba que el estado actual no fuera ya `ASIGNADO`. Al sumar una unidad de apoyo a un
caso que ya se estaba atendiendo, su confirmación reescribía el estado hacia atrás: **el
expediente decía que nadie había llegado mientras la primera unidad llevaba horas en el
sitio**. El SRS dice "si es el **primer** despacho confirmado del caso". Visto en el historial
del caso real durante esta prueba.

**Pruebas que codificaban el defecto.** Cuatro aseveraban el auto-retiro (una se llamaba
literalmente `test_cerrar_when_en_atencion_auto_retira_y_cierra`). Contrastadas con el SRS y
reescritas para aseverar la regla: el cierre se rechaza mientras quede una unidad, y el caso
cierra cuando se retiran todas. El resto solo usaba el cierre como andamiaje: se les añadió el
paso de retiro, que además ejercita el endpoint nuevo.

**Verificado de punta a punta en el navegador y contra Pinot** con
`ACC-1786569480560-3023` y dos unidades:
1. Con las dos en el caso, cerrar responde *"No se puede cerrar: 2 unidad(es) siguen sin
   retirarse"* y el caso sigue abierto.
2. `LOTE-A2` finaliza su parte desde su pantalla → despacho 4305 con `retiro_forzado = false`.
3. El Operador fuerza el retiro de `LOTE-A3` → despacho 4310 con `retiro_forzado = **true**`,
   y al completarse el conjunto **el caso se cierra solo**.
4. `Fact_Accidente` queda con `horafin`, `duracionminutos = 339` y `activo = false`; las dos
   unidades vuelven a `Activa`. La evidencia adjunta no intervino en ningún momento del
   cierre, que es la regla de no bloqueo de §3.6.3.

Suites: **backend 1648 passed, 2 skipped**; **frontend 615 SUCCESS**.

---

## 2026-08-12 — §3.6.3 Evidencia en Sitio: F9/F12 (puertas que no existían), B31 y B32

Alcance: `frontend/.../mi-seguimiento.page.{html,ts,spec.ts}`,
`frontend/.../galeria-evidencias.page.{html,ts}` (+ spec nuevo),
`frontend/.../monitoreo-despacho.page.html`,
`backend/apps/despacho/services/{mi_despacho_service,rechazar_despacho_service,confirmar_despacho_service,asignacion_manual_service}.py`
(+ pruebas). SRS §3.6.2, §3.6.3 y §3.6.4.

**Lo que ya cumplía, comprobado contra el stack real** (unidad `LOTE-A2`, caso
`ACC-1786569480560-3023`):

- La unidad adjunta **fotografía y nota de campo**, en línea y en diferido.
- **Captura sin conexión conservando la hora de captura**, que es la regla central del
  módulo. Verificado en Pinot, no solo en pantalla: la nota guardada offline quedó con
  `fechahora = 00:59:14Z` (captura) y `fecha_actualizacion = 01:01:25Z` (subida), **131 s de
  diferencia**; la foto, 95 s. La nota registrada en línea tiene ambas marcas iguales. La
  hora que se conserva es la del sitio, no la de la señal.
- **Cada unidad adjunta la suya de forma independiente**: con la ambulancia `LOTE-A2` y la
  grúa `LOTE-A3` en el mismo caso, `Dim_NotaAccidente` guarda tres notas atribuidas a
  `idusuario` 9005 y 9006, sin pisarse.

**F9 — la unidad no tenía forma de llegar a la evidencia.** El permiso estaba dado (la
galería admite el rol `Unidad`) pero **no había ninguna puerta**: la barra de navegación de
la unidad tiene tres entradas y ninguna lleva ahí; `Mi despacho` y `Mi seguimiento` no
contienen un solo enlace; y el único enlace de toda la aplicación vive en el detalle del
accidente, que es pantalla de Operador y a la unidad le responde **"Acceso denegado"**.
Peor: la propia galería remataba con *"Volver al accidente"* → acceso denegado, un callejón
sin salida. Es la familia de B6. Corregido: enlace **"Evidencia del caso"** en Mi seguimiento
—junto al despacho y en el aviso de llegada— y enlace de vuelta según el rol.

**F12 — la asignación manual tampoco tenía puerta.** `/despacho/asignacion/:idaccidente`
existe y funciona, pero **nada en la aplicación enlazaba a ella**: solo se alcanzaba
escribiendo la URL. El SRS la exige como red de seguridad —*"esta vía permanece disponible
aunque la asignación automática falle"*— y es además la vía para sumar una segunda unidad.
Corregido con el botón **"Asignar unidad"** en el monitoreo del caso. **El requisito ya estaba
escrito**: `FR-UI-006` del spec de frontend pedía exactamente ese CTA. Es un caso claro de
requisito documentado y no construido, que ninguna prueba detectaba porque la ruta sí existe.
Lo mismo aplica a `FR-UI-007` (coordinar unidad adicional), que sigue sin CTA propio — hoy se
resuelve con el mismo botón, y queda anotado en §7 del documento de revisión.

**B31 — la unidad veía como pendientes despachos ya vencidos.** El vencimiento cierra el
despacho (`activo = false`) pero **no toca la notificación**, que se queda `Notificada` para
siempre; `listar_pendientes` solo miraba el estado de la notificación. Resultado comprobado
en vivo: `LOTE-A3` tenía **tres despachos "pendientes" del mismo caso**, todos muertos, y al
responder uno recibía `404 "Notificación no encontrada"` — mentira doble, porque la
notificación existe y lo que venció es el despacho. En la pantalla donde la unidad decide a
qué caso va, eso es ruido peligroso. Ahora la cola descarta los que no tienen despacho
activo, y confirmar/rechazar uno vencido responde **409 "Este despacho ya venció por falta de
respuesta y fue reasignado"**.

**B32 — con la unidad ya en el sitio no se podía pedir apoyo.** `AsignacionManualService`
solo admitía `REPORTADO`, `BUSCANDO_UNIDAD` y `ASIGNADO`: en cuanto la primera unidad
registraba su llegada y el caso pasaba a `EN_ATENCIÓN`, **ninguna otra unidad podía sumarse**
—ni por asignación manual ni por el endpoint de coordinación, que delega en el mismo
servicio—. El SRS §3.6.4 dice lo contrario con todas las letras: *"si tras la escalada hace
falta apoyo adicional, el despacho de la unidad extra se ejecuta en el módulo de Despacho"*,
y §3.6.2 describe la coordinación de varias unidades sobre un caso. Corregido admitiendo
`EN_ATENCIÓN`; `CERRADO`, `DESCARTADO` y `BORRADOR` siguen rechazándose. Verificado en el
navegador: con el caso en atención, la grúa `LOTE-A3` se despachó y confirmó sobre él.

Suites: **backend 1642 passed, 2 skipped** (eran 1638); **frontend 611 SUCCESS** (eran 608).

---

## 2026-08-12 — F7/F8: el aviso de error culpaba a la conexión, y el modal no existía para nadie que no mirara

Alcance: `frontend/src/app/shared/notifications/alert-host.component.ts`,
`…/confirm-dialog-host.component.ts` (+ sus specs, nuevos),
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`
(+ spec), `.specify/docs/design/design-system.md` (§11, nueva). Detectados al preparar la
prueba en navegador de B27.

**F7 — el error de validación se presentaba como problema de red.** Registrar un accidente con
fecha futura devuelve `400 {"detail": "Fecha futura no permitida"}`, y la pantalla mostraba
*"No se pudo registrar el accidente. Verifica la conexión e inténtalo de nuevo."*. El detalle
que el backend sí envía se descartaba, así que el operador no sabía qué corregir y se le
mandaba a revisar la red por un campo mal escrito. Ahora el Alert muestra el detalle en los
errores 4xx; el mensaje de conexión se reserva a fallo de red y 5xx, que es cuando puede serlo.

**F8 — el Alert modal no se anunciaba como diálogo.** Era un `div` `fixed inset-0` que cubría
la pantalla y **capturaba todos los clics**, sin `role`, sin `aria-modal`, sin foco y sin
Escape: para un lector de pantalla o una navegación por teclado, la aplicación simplemente
dejaba de responder, sin nada que explicara por qué. Se descubrió en vivo — los clics de la
prueba de B27 iban al overlay invisible y parecía que el formulario estaba roto. Corregido en
los **dos** hosts, que compartían el defecto: `role="alertdialog"` / `role="dialog"`,
`aria-modal`, título y mensaje asociados, foco al abrir y cierre con Escape. En el diálogo de
confirmación el foco inicial va al botón **no destructivo** y **Escape equivale a cancelar**,
nunca a confirmar. La regla queda escrita en `design-system.md` §11, que es la autoridad.

**Verificado en el navegador** contra el stack real: el 400 de fecha futura ahora dice
*"No se pudo registrar el accidente: Fecha futura no permitida"*, el diálogo expone
`role="alertdialog"` con el foco en Aceptar y Escape lo cierra; el de confirmación de
"Descartar borrador" abre con el foco en **Cancelar** y Escape conserva el borrador.

**Suite de frontend: 608 SUCCESS** (eran 599; 9 pruebas nuevas). **Corrección importante al
estado anterior: la suite sí se puede ejecutar en esta máquina.** `.specify` y
`REVISION-SRS-ESTADO.md` §7.4 la daban por no ejecutable desde el 2026-08-12 por un fallo de
arranque de Karma con Edge; en esta sesión completó dos corridas seguidas sin tocar
configuración. La sospecha registrada entonces —procesos `msedge` del usuario abiertos— queda
reforzada: es un problema de entorno, no del proyecto.

---

## 2026-08-12 — B27 (CORREGIDO) + B28/B29: la asignación automática de despacho ya se ejecuta

Alcance: `backend/apps/despacho/consumers/runner.py` (nuevo),
`backend/apps/despacho/management/commands/run_kafka_consumers.py` (nuevo),
`backend/apps/despacho/consumers/accidente_reportado_consumer.py`,
`backend/core/repositories/despacho/despacho_repository.py`, `backend/config/settings.py`,
`backend/conftest.py`, `docker/accidentes.yml`,
`specs/003-operational/Emergencias/despacho-inteligente/backend/spec.md` (RF-DES-012).
SRS §3.6.2.

**Decisión de arquitectura (usuario, 2026-08-12).** El consumidor corre como **worker aparte
en `docker-compose`** —management command + servicio propio con `restart: unless-stopped`—,
no como hilo dentro de `runserver`. Alcance: los **dos** handlers ya registrados; el
consumidor de aborto queda fuera, no está inscrito en `apps.py`.

**B27 — el proceso que faltaba.** `register_consumer` inscribía los handlers en un
diccionario que nadie leía. Ahora `ConsumerRunner` los consume:
`python manage.py run_kafka_consumers`, servicio `despacho-worker`. Detalle de la política de
entrega en RF-DES-012 del spec: `auto_offset_reset=latest` (un worker nuevo **no** reprocesa
el historial e intenta despachar accidentes viejos), confirmación de offset manual y
posterior al proceso (*at-least-once*), y un handler que falla se registra sin detener el
bucle ni bloquear la partición —un mensaje envenenado no puede impedir el despacho del
accidente siguiente—.

**B28 — el handler no reconocía ningún evento real.** Al ir a probarlo apareció un segundo
defecto que el proceso muerto tapaba: `AccidenteReportadoConsumer` leía `event["estado"]`,
pero `EstadoAccidenteRepository.append_estado` publica **`idtipoestadoincidente`**, la FK al
catálogo. Con el worker en marcha habría registrado "ignorando evento no REPORTADO: None"
para cada accidente del sistema: la mitad de B27 habría seguido rota, ahora en silencio y con
un proceso vivo aparentando funcionar. El handler resuelve la FK.

**Por qué la suite no lo veía, y qué se cambió del doble.** El test alimentaba el handler con
un dict escrito a mano (`{"estado": "REPORTADO"}`) que ningún productor emite: la prueba
codificaba el defecto. Ahora el evento se construye **publicándolo con el repositorio real** y
tomándolo de `mock_kafka`. Al hacerlo apareció que el doble mentía en un segundo nivel:
guardaba la **referencia** al payload, y `append_estado` añade `payload["estado"]` *después*
de publicar, así que las pruebas veían un campo que jamás viaja por Kafka. El doble ahora
guarda una copia, como hace el productor real al serializar a JSON dentro de `publish()`.

**Idempotencia (consecuencia de at-least-once).** `AsignacionInteligenteService.ejecutar` no
tenía guarda: reprocesar un evento creaba un segundo despacho. El handler ahora no asigna si
el caso **ya tiene despacho activo**, lo que cubre también que el Operador haya despachado a
mano entretanto. La comprobación lee de Pinot: no cubre el reintento dentro de la ventana de
ingesta de 5–15 s, y así queda escrito en el spec en vez de aparentar que sí.

**~~B29~~ — RETIRADO el 2026-08-12, no era un defecto.** Se registró que `list_all_active()`
consultaba `Fact_Despacho WHERE activo = true` sin `LIMIT` y que por tanto el ciclo de
vencimientos solo veía diez despachos. **Es falso**: `PinotClient.query` añade
`LIMIT DEFAULT_QUERY_LIMIT` (10 000) a toda consulta que no declare uno —
`_with_explicit_limit`, ya presente en el repositorio desde antes de esta revisión—, así que
la consulta nunca estuvo bajo el recorte implícito a 10. El `LIMIT` explícito que se añadió
queda porque documenta la intención en el propio SQL, pero **no arregla nada**: no había nada
roto. La afirmación de daño ("el resto no vencía nunca") era incorrecta.

Conviene revisar con este criterio los hallazgos anteriores de la misma familia (B11, B13,
B16, B20, B25): si esa guarda del cliente ya existía cuando se registraron, sus consecuencias
también pudieron quedar sobredimensionadas. Los cambios en sí —bajar el filtro y el tope al
SQL— siguen siendo correctos y más eficientes que filtrar en Python.

**Registro de actividad.** No había `LOGGING` en `settings.py`: los loggers `tsi.*` no
llegaban a ninguna parte porque la raíz está en WARNING. Para la API se notaba poco; para un
worker sin pantalla ni respuesta HTTP, era una caja negra. Añadido un handler de consola para
`tsi` (nivel por `TSI_LOG_LEVEL`), y `PYTHONUNBUFFERED=1` en el servicio. El logger
**propaga a la raíz a propósito**: `caplog` de pytest captura ahí, y varias pruebas aseveran
el contenido del rastro de auditoría; cortar la propagación las deja sin ver nada.

**B30 — encender el registro reventó una tarea periódica.** `run_evaluacion_reglas_demo`
hacía `logger.info("evaluacion_reglas_demo", extra=result)` con
`result = {"created": …, "skipped": …}`, y **`created` es un atributo reservado de
`LogRecord`**: `logging` lanza `KeyError` al construir el registro. No se notaba porque el
logger `tsi` no tenía nivel INFO y la llamada salía antes de llegar ahí. En cuanto el nivel
sube —que es justo lo que se hace al diagnosticar un problema en producción— **la tarea
falla**. El resultado va ahora anidado bajo `resultado`. Se auditaron los demás `extra=` del
backend: los otros nueve pasan claves de dominio sin colisión.

**Verificado contra el stack real, en el navegador.** Como Operador se registró
`ACC-1786569480560-3023` sin tocar nada más. Sin intervención humana, el worker creó el
despacho **4305** sobre `LOTE-A2`, y la pantalla de monitoreo muestra el caso en
`BUSCANDO_UNIDAD` con su intento *"Ambulancia Lote A2 — Pendiente — Automatico"*. Después se
ejecutó el ciclo de vencimientos sobre `ACC-1786567280611-1700`: cuatro despachos vencidos
produjeron **cuatro reasignaciones automáticas** (4306–4309), y el expediente conserva los
intentos en `Timeout` junto a los nuevos. Antes, ese caso se quedaba encallado en
`BUSCANDO_UNIDAD` para siempre. Reiniciando el worker se comprobó el apagado limpio y que
**no reprocesa** el historial ni duplica el despacho 4305.

Suite backend: **1638 passed, 2 skipped** (eran 1629; 9 pruebas nuevas del runner y del
consumidor). Sin cambios de frontend.

---

## 2026-08-12 — B12/B13: ninguna mejora de plan podía completarse

Alcance: `backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/core/repositories/suscripciones/solicitud_cambio_plan_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo (B12).** Detectado al probar el cambio de plan desde el navegador (SRS §3.3.1,
"una mejora de plan se autoaprueba"). `POST /api/v1/suscripciones/solicitudes-cambio-plan`
para subir de Básico a Profesional devolvía **404 "Solicitud no pendiente"**.

**Causa.** `CambioPlanService.solicitar()` creaba la solicitud y, si era mejora, llamaba
acto seguido a `aprobar(idsolicitud=...)`, que empieza por
`self.solicitudes.find_by_id(idsolicitud)`. La escritura acababa de salir por Kafka y Pinot
tarda 5-15 s en exponerla, así que la relectura devolvía vacío y la propia guarda de
`aprobar` rechazaba la solicitud recién creada. Es la trampa de "nunca releer algo recién
escrito dentro de la misma operación", esta vez dentro de una sola petición HTTP.
`SolicitudCambioPlanRepository.update()` tenía el mismo `find_by_id` al principio, así que
aunque se hubiera superado la primera guarda, el cambio de estado se habría perdido igual.

**Efecto verificado.** **Ninguna mejora de plan podía completarse.** El cliente veía un
error, la suscripción seguía en el plan viejo y quedaba una solicitud `Pendiente` huérfana
en `Fact_Solicitud_Cambio_Plan`. Como `solicitar()` rechaza con 409 si ya hay una pendiente,
a partir de ese momento el cliente **no podía pedir ningún cambio de plan**, ni mejora ni
reducción: el primer intento de mejora lo dejaba bloqueado indefinidamente.

**Hallazgo (B13), en el mismo repositorio.** `find_pendiente()` y `list()` hacían
`SELECT * FROM Fact_Solicitud_Cambio_Plan` sin `LIMIT` y filtraban en Python, bajo el
`LIMIT 10` implícito de Pinot. Con más de diez solicitudes en el sistema, la guarda de
"una sola solicitud pendiente por cliente" podía dejar de ver la pendiente y aceptar una
segunda, y a la bandeja del Administrador dejaban de llegar solicitudes sin ningún error.

**Cambio de código.** `aprobar()` se dividió en la entrada pública —que sigue releyendo y
validando, porque ahí el id viene de la URL— y `_aprobar(sol, idadmin)`, que trabaja sobre
la fila ya en memoria. La auto-aprobación de la mejora llama a `_aprobar` con el registro
recién creado, sin releer nada. Se añadió `update_from(current, changes)` al repositorio
para republicar la fila completa —la tabla es upsert— a partir de una copia en memoria;
`update()` se mantiene y ahora delega en él. `rechazar()` usa también `update_from`, con lo
que hace una consulta menos. `find_pendiente()` y `list()` pasan el filtro a SQL con
`LIMIT` explícito.

**Por qué no lo cazó la suite.** `test_upgrade_auto_aprueba` pasaba en verde porque el
doble en memoria refleja cada escritura en `PINOT_STORE` al instante: la relectura siempre
encontraba la fila. La regresión añadida
(`test_upgrade_auto_aprueba_aunque_pinot_aun_no_exponga_la_solicitud`) anula `find_by_id`
con `patch.object` para reproducir el retardo real, y falla contra el código anterior.

**Verificación.** `python -m pytest` → **1613 passed, 2 skipped**. En el navegador contra
el stack real: la mejora Básico→Profesional responde **201** con `estado: "Aprobada"`, y en
Pinot la suscripción queda `idplan=2, precio=149.0, nivel='Profesional'` y la solicitud
`Aprobada`; "Mi suscripción" muestra Profesional · $149.00. La reducción
Profesional→Básico queda `Pendiente` con el aviso de que debe aprobarla un Administrador.
El rechazo desde la bandeja del Administrador persiste `Rechazada` con su motivo.

---

## 2026-08-12 — B27 (CRÍTICO, no corregido): la asignación automática de despacho nunca se ejecuta

> **Corregido el mismo 2026-08-12** — ver la entrada «B27 (CORREGIDO) + B28/B29» más arriba.
> Este hallazgo se conserva porque describe el daño y porque al construir el worker
> aparecieron dos defectos más que este proceso muerto tapaba.

Alcance: hallazgo, sin cambio de código. SRS §3.6.2.

**Hallazgo.** Se registró un accidente como Operador, con una unidad declarada `Activa` en la
zona y la región en producción — todos los prerrequisitos del SRS cumplidos. Pasados varios
minutos, `GET /accidentes/{id}/despacho` seguía devolviendo `estado_caso: "REPORTADO"` e
`intentos: []`. **No se creó ningún despacho automático.**

**Causa.** La asignación automática la dispara un consumidor de Kafka:
`AccidenteReportadoConsumer` / `handle_accidente_reportado`, que `DespachoConfig.ready()`
inscribe con `register_consumer(...)` sobre el topic de estado de accidente. Pero ese registro
es **un diccionario en memoria que nadie lee**: `get_consumer_handlers()` no tiene ningún
llamador en todo el backend, no hay bucle de consumo, no hay management command y el
contenedor arranca solo `python manage.py runserver`. El handler está escrito, probado y
registrado — y jamás se invoca.

**Efecto.** El SRS §3.6.2 dice: *"El sistema **asigna automáticamente** la unidad más
adecuada, evaluando las unidades disponibles y su distancia al punto del accidente. Crea el
despacho, marca su origen como automático y notifica a la unidad."* Eso no ocurre nunca. Todo
caso queda en `REPORTADO` esperando que un operador despache a mano. En un departamento donde
"una demora tiene consecuencias sobre vidas humanas", el automatismo que debería ganar esos
segundos no existe en ejecución.

**Lo que sí funciona y lo salva parcialmente.** La vía manual está operativa y el SRS la
exige precisamente como red de seguridad: *"Esta vía permanece disponible aunque la
asignación automática falle — nunca debe existir una situación donde el sistema no pueda
despachar porque el algoritmo no responde."* Verificado: el despacho manual crea el caso con
`origen: "Manual"`, notifica a la unidad y mueve el caso a `BUSCANDO_UNIDAD`.

**Matiz importante: el motor automático no está roto, solo no se dispara.** Al rechazar un
despacho, la reasignación se ejecuta **de forma síncrona** desde el propio servicio de
rechazo, y ahí sí funciona: creó un despacho nuevo sobre otra unidad con
`origen: "Automatico"`. O sea que el algoritmo de selección, la creación del despacho y la
notificación están operativos y probados en vivo. Lo que falta es exclusivamente **el proceso
que consuma los eventos de Kafka**.

**Segunda consecuencia, más dañina que la primera.** El otro handler registrado en ese mismo
diccionario muerto es `handle_despacho_timeout`, que es quien reasigna cuando una unidad **no
responde**. Verificado: al ejecutar el ciclo de vencimientos, el despacho queda marcado
`Timeout` correctamente… y ahí se acaba. **No se reasigna a nadie y el caso se queda en
`BUSCANDO_UNIDAD` indefinidamente**, sin más intentos y sin aviso. Es peor que la falta de
asignación inicial: en el arranque el operador sabe que tiene que despachar a mano, pero aquí
puede creer que hay una unidad en camino hasta que se le ocurra mirar. El SRS define la
reasignación como "el punto de entrada único de toda reasignación del sistema, sin importar
si el disparador fue un rechazo, un vencimiento o un aborto" — hoy solo entra por el rechazo.

**Por qué no se corrigió aquí.** Es el mismo patrón que **G1** del 2026-07-15 ("jobs
periódicos sin agendar": los servicios existían y nadie los invocaba), que se resolvió
añadiendo management commands. Pero un consumidor de Kafka no es un job: necesita bucle de
sondeo, gestión de offsets, política de reintentos y decidir cómo se supervisa el proceso
(¿worker aparte en `docker-compose`?, ¿un `runserver` con hilo?, ¿qué pasa si muere?). Eso es
una decisión de arquitectura y despliegue, no un arreglo de una línea, y hacerla a la carrera
sería peor que dejarla escrita. **Queda como el punto más importante que atender en
Emergencias**, con la ventaja de que todo el dominio ya está construido: solo falta el
proceso que consuma.

---

## 2026-08-12 — Verificado sin cambios: despacho manual, confirmación y las reglas de flota con despacho activo

Alcance: ninguno (solo pruebas). SRS §3.6.2 y §3.5.1.

Con un accidente `REPORTADO`, una unidad con acceso propio y su disponibilidad declarada, se
recorrió la cadena completa:

- **Despacho manual**: crea el despacho con `origen: "Manual"`, lo entrega
  (`push` y `sms`) y mueve el caso a `BUSCANDO_UNIDAD`.
- **La unidad ve su pendiente** en `mi-despacho/pendientes`, con severidad, descripción,
  coordenadas y ETA.
- **Confirmación**: el despacho queda `Confirmado`, el caso pasa a **`ASIGNADO`** —primer
  despacho confirmado— y la unidad a **`En Misión`**, que el SRS define como el único estado
  que no declara nadie sino que fija el sistema al confirmarse un despacho.
- **El intento se conserva** en el historial del caso con su origen y estado.
- **Rechazo**: sin motivo responde 400 "motivo requerido" —el SRS lo exige—; con motivo, el
  despacho queda `Rechazado` conservando el texto, y **se dispara la nueva búsqueda**
  (`reasignacion_iniciada: true`), que crea un despacho sobre otra unidad con
  `origen: "Automatico"`.
- **Vencimiento**: el ciclo de timeouts marca el despacho como `Timeout` sin borrarlo.
- **Los tres desenlaces conviven en el historial.** Un mismo caso terminó mostrando el
  intento rechazado (con su motivo) y el vencido, uno detrás de otro, tal como pide el SRS
  para poder analizar después qué unidades rechazan sistemáticamente.
- **Escalado a zonas vecinas**: encuentra unidades de condados contiguos y marca el despacho
  con `origen: "Escalado_zona"`, como pide el SRS.
- **Constancia cuando no hay capacidad**: agotadas todas las unidades de las zonas vecinas,
  la llamada responde `{"message": "Sin unidades en condados vecinos", "alerta_registrada":
  true, "nota": "Escalamiento registrado"}`. Es la constancia explícita que exige el SRS —
  "el sistema no falla en silencio ante la ausencia total de unidades"—, y además queda
  registrada, no solo devuelta.
- **Varios despachos sobre un mismo caso** conviven con estado propio e independiente: el
  caso de prueba acumuló seis intentos (manual, automático por reasignación y tres
  escalados) sin que unos pisaran a otros.

Y con ese despacho activo se cerraron las cuatro reglas de Red Operativa §3.5.1 que faltaban:

- **Baja con despacho activo, por el proveedor** → 403: "solo un Administrador puede ejecutar
  la baja forzada. Espere al cierre del caso."
- **Edición de campo crítico con despacho activo** → 409 "se requiere confirmación
  explícita"; un campo no crítico (capacidad) se edita sin problema.
- **Baja forzada por Administrador**: sin `forzar` → 409 pidiéndolo explícitamente; con
  `forzar` → ejecuta, y en `Fact_BajaUnidad` queda **`tipobaja: "Forzada_con_reasignación"`
  con el `idaccidente` del caso en curso**, que es la traza del impacto que pide el SRS.
- **Unidad de baja excluida de todo despacho**: tras la baja forzada, la consulta de
  candidatas del caso devuelve `candidatas: []`. "Sin excepción alguna", como dice el SRS.

---

## 2026-08-12 — B26: una falsa alarma no se podía descartar nunca

Alcance: `backend/apps/accidentes/services/descartar_caso_service.py`,
`backend/core/repositories/despacho/despacho_repository.py`,
`backend/apps/accidentes/tests/services/test_descartar_caso_service.py`,
`backend/apps/accidentes/tests/api/test_descartar_caso_contract.py`.

**Hallazgo.** Primer defecto de Emergencias (SRS §3.6.1). Se registró un accidente como
Operador y se intentó descartarlo como falsa alarma **sin que existiera ningún despacho**:
respondió 409 "Solo se puede descartar en BORRADOR".

**Causa.** El SRS condiciona el descarte a un hecho concreto: *"El operador puede descartar
el caso registrando el motivo. Esto **solo es posible mientras no exista ningún despacho
creado**."* La guarda implementaba otra condición —estar en `BORRADOR`— que es más estricta y
distinta. Y ahí está el detalle que lo vuelve grave: el registro **se autoconfirma** a
`REPORTADO` cuando no hay advertencias (`RegistroAccidenteService`: nace en BORRADOR y pasa a
REPORTADO si `not validation.has_advertencias`). O sea que un accidente registrado
limpiamente —el caso normal— saltaba a REPORTADO en el acto y **ya nunca podía descartarse**.

**Efecto.** La falsa alarma solo era descartable en el caso raro de que el registro hubiera
disparado alguna advertencia (posible duplicado, fuera de cobertura) y se hubiera quedado en
borrador. En el camino habitual, el operador que confirma que el aviso era falso no tiene
forma de cerrarlo: el caso se queda REPORTADO, vivo y a la espera de despacho.

**Cambio de código.** La guarda ahora implementa la condición del SRS: se admite descartar en
`BORRADOR` o `REPORTADO`, y se rechaza si `DespachoRepository.list_by_accidente()` devuelve
algo. El mensaje de conflicto distingue los dos motivos ("no se puede descartar un caso en
CERRADO" vs. "el caso ya tiene despachos creados"). De paso, `list_by_accidente` llevaba
`SELECT *` sin `LIMIT`: con el recorte implícito a 10 de Pinot, un caso con varias unidades
coordinadas —una grúa sumándose a una ambulancia, que el SRS §3.6.2 contempla— habría perdido
despachos del agregado sin aviso.

**Tests que codificaban el defecto.** `test_descartar_when_not_borrador_raises` y
`test_descartar_when_reportado_returns_409` daban por buena la guarda vieja. Se reescribieron
contra la regla del SRS: REPORTADO **sin** despacho ahora se descarta (200), con despacho da
conflicto, y un caso CERRADO sigue rechazándose.

**Verificación.** `python -m pytest` → **1629 passed, 2 skipped**. Contra el stack real, el
mismo accidente que antes devolvía 409 ahora responde "Caso descartado exitosamente" con
estado `DESCARTADO`.

---

## 2026-08-12 — Verificado sin cambios: regla de origen del dato en el registro

Alcance: ninguno (solo pruebas). SRS §3.6.1.

El formulario de registro de accidente pide ubicación y hora, descripción, severidad,
vehículos involucrados, heridos, víctimas, fallecidos y origen del reporte. **No pide clima,
fotografías, conductores ni implicados**, que es exactamente lo que el SRS prohíbe capturar
desde la central ("la central no inventa lo que no ve"); esos datos quedan para el personal
en sitio. El propio servicio lo deja anotado en un comentario. Regla cumplida.

> **Anotado, no corregido:** el formulario muestra "Calle seleccionada (idcalle)" — un nombre
> de columna en pantalla, §8 del design-system. Añadido a §7.1.

---

## 2026-08-12 — B25: el conteo de cobertura podía despublicar sola una región que sí tenía unidades

Alcance: `backend/core/repositories/red_operativa/cobertura_region_read_repository.py`.

**Hallazgo.** Revisando §3.5.2. Las tres consultas de
`CoberturaRegionReadRepository` —los estados de la región, sus condados y las unidades
activas de esos condados— iban **sin `LIMIT`**, bajo el recorte implícito a 10 filas de Pinot.

**Por qué aquí es grave.** En otros sitios el `LIMIT 10` implícito hace desaparecer datos de
una pantalla. Aquí alimenta la **única acción que el SRS permite al sistema tomar sin
revisión humana**: despublicar una región al llegar a cero cobertura. Con más de diez
condados, `_condados_de_la_region` devolvía solo diez; si esos diez no tenían unidades pero
los demás sí, el conteo daba **0** y la región se despublicaba sola teniendo cobertura real.
Una zona que podía atender casos dejaba de recibirlos, sin que nadie lo decidiera. El error
va en la dirección peligrosa: subcontar nunca da un falso "hay cobertura", pero sí un falso
"no hay ninguna".

**Cambio de código.** `LIMIT` explícito en las tres consultas
(`LIMITE_CONDADOS = 1000`, `LIMITE_UNIDADES = 10000`), con el porqué escrito en el módulo.

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**. Contra el stack real, la
región `Centro` sigue contando sus 7 unidades activas y rechazando la despublicación con 409.

---

## 2026-08-12 — F6: el historial de validaciones imprimía la fecha como epoch

Alcance: `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/validacion/validacion.page.ts`.

La columna FECHA/HORA del historial de intentos mostraba `1786559771844`. Mismo caso que F4
en métodos de pago: el epoch en milisegundos llega crudo a la plantilla. Corregido con
`| date: 'medium'` (`CommonModule` ya estaba importado). Verificado en el navegador: los tres
intentos de la región de prueba se leen ahora como "Aug 12, 2026, 1:36:11 PM".

---

## 2026-08-12 — Verificado sin cambios: protocolo de validación de región (dos actores)

Alcance: ninguno (solo pruebas). SRS §3.5.2.

- **Dos actores en secuencia, no indistintos.** El Administrador ejecuta el protocolo, pero
  al intentar registrar el resultado como *Aprobada* recibe **"Solo el Director Tecnológico
  puede aprobar una región para producción"**. Con el Director Tecnológico
  (`roberto.paredes.director@demo.tsi.com`) la aprobación sí procede y la región pasa a
  `Producción`.
- **El rechazo deja la región en validación.** Tras un resultado *Rechazada*, el estado
  queda `En_Validación`, no inactiva ni en producción.
- **Los intentos se acumulan.** Dos validaciones rechazadas seguidas sobre la misma región
  producen los intentos 1 y 2, **cada uno con su motivo**, y la aprobación del Director
  añade el 3 sin borrar los anteriores. El historial es consultable desde la pantalla.
- **El motivo se pide solo al rechazar**: el campo aparece al marcar *Rechazada*, que es el
  "detalle del criterio incumplido" del SRS.
- **Rechazo definitivo** existe como acción aparte, para la región que no continúa.
- **Cobertura cero.** El guardarraíl funciona: sobre una región con unidades activas, la
  despublicación automática responde 409 diciendo cuántas hay. La rama de **cero cobertura**
  no se pudo ejercitar contra el stack real —el entorno demo tiene un único estado y dos
  condados, así que dejar una región sin cobertura exigía desactivar la flota entera y
  arruinar el escenario de Emergencias—; está cubierta por
  `test_despublicacion_automatica_service.py`.

> **Cuidado al montar una región de prueba.** Una región creada sobre el mismo `idestado` que
> otra **comparte sus condados y, por tanto, su cobertura**: la región nueva reportaba las 7
> unidades de `Centro`. No es un defecto del conteo — se comprobó — sino una propiedad del
> modelo (región → estado → condados → unidades) que hace falta tener presente para no
> interpretar mal una prueba.

---

## 2026-08-12 — Verificado sin cambios: carga en lote y declaración de disponibilidad

Alcance: ninguno (solo pruebas). SRS §3.5.1.

**Carga en lote (todo o nada).**

- **Puerta del plan.** Con un cliente en plan Básico (`carga_lote_habilitada = false` en su
  suscripción) la importación responde 403 "El plan contratado no habilita la carga en lote
  de unidades". La capacidad se lee de la **suscripción**, no del plan en vivo, que es lo que
  exige R-04 del SRS.
- **Una fila mala tumba el archivo entero.** Con tres filas donde la tercera repetía una placa
  existente: `{"insertadas": 0, "usuarios_creados": 0, "fallidas": [{"fila": 3, "motivo": "Ya
  existe una unidad con placa TSI-001"}]}`. Comprobado en Pinot que **no quedó nada**: ni las
  dos unidades válidas ni sus usuarios. El proveedor recibe qué fila falló y por qué, como
  pide el SRS.
- **El reintento desde cero funciona.** Corregido el archivo, la misma carga responde
  `{"insertadas": 3, "usuarios_creados": 3, "fallidas": []}`.
- **Y de paso valida B23 en el caso más duro.** Esas tres altas asignan el rol `Unidad` tres
  veces seguidas dentro de una sola operación: en Pinot quedaron con claves **distintas**
  (`idusuariorol` 9003, 9004 y 9005) y la fila de la administradora de cliente siguió
  intacta. Antes del arreglo, este lote la habría vuelto a dejar sin roles.

**Disponibilidad — la declara siempre la propia unidad.**

- El endpoint es `POST /api/v1/mi-unidad-emergencia/disponibilidad`, de alcance propio por
  diseño: no admite nombrar otra unidad, así que la vía para que un tercero la declare "en su
  nombre" no existe estructuralmente.
- **Terceros rechazados con 403**, incluido el **Administrador** y el propio proveedor dueño
  de la unidad. Es la regla estricta del SRS ("no existe una vía por la cual un tercero la
  declare en su nombre"), ya cerrada en la decisión #12 con
  `IsUnidadEmergenciaSelfStrict` y confirmada ahora contra el stack.
- **La unidad sí puede**: con el acceso creado en su alta (rol `Unidad`), declara `Activa` y
  luego `Fuera de servicio`, y cada cambio queda en el historial con estado anterior, estado
  nuevo y marca de tiempo.
- **El alta no establece la disponibilidad.** La unidad recién creada arranca en
  `Fuera de servicio` y solo pasa a `Activa` cuando ella misma lo declara, tal como dice el
  SRS.
- **Una unidad sin correo no puede declarar nada** por construcción: sin usuario no hay login
  ni token, y este endpoint exige rol `Unidad` sobre la sesión propia. No hace falta una
  guarda adicional.

> **Observado al entrar como unidad.** El login de la unidad responde
> `requiresPasswordChange: true` sobre su credencial temporal, que es el circuito de B5. Para
> poder probar la disponibilidad se le fijó una contraseña conocida a la unidad `LOTE-A1`
> (usuario 9004) — ver §2.4 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — B23: asignar un rol a un usuario le quitaba el rol a otro

Alcance: `backend/core/repositories/cuentas_clientes/role_repository.py`,
`backend/conftest.py`,
`backend/apps/cuentas_clientes/tests/repositories/test_role_repository.py`.

**Hallazgo.** Detectado de rebote: al ir a probar la restricción de flota propia, la cuenta
`teresa.beltran@demo.tsi.com` —que había entrado sin problemas un rato antes en la misma
sesión— empezó a responder "Credenciales inválidas o usuario inactivo". Su usuario estaba
activo, su credencial `Activo`, y el hash correspondía a la contraseña. Ejecutando el
servicio dentro del contenedor, el fallo real era **"Usuario sin roles asignados"**: había
perdido su fila en `Dim_Usuario_Rol`.

**Causa.** `RoleRepository.assign_role_to_user()` publicaba el payload **sin
`idusuariorol`**, que es la clave primaria de la tabla. Como Pinot no almacena NULL, la fila
aterrizaba con el defecto para INT (`Integer.MIN_VALUE`), y al ser una tabla **upsert por esa
clave**, todas las asignaciones caían en la misma fila: **cada rol nuevo sobrescribía al
anterior**. En la práctica solo podía existir una asignación hecha por esta vía en todo el
sistema.

**Efecto verificado.** Registrar una unidad de emergencia con correo —que asigna el rol
`Unidad` al usuario nuevo— **le quitó el rol a Teresa y la dejó fuera del sistema**. Ni ella
ni nadie tenía forma de relacionar una cosa con la otra: el usuario simplemente deja de poder
entrar, con un mensaje de credenciales inválidas que apunta al sitio equivocado. Afecta a
todo usuario cuyo rol se asignara por esta vía: altas de unidad con correo, autorregistro,
alta de cliente.

**Cambio de código.** `assign_role_to_user()` genera la clave con `_next_user_role_id()`
(`MAX(idusuariorol) + 1`, acotado a positivos para que las filas huérfanas con
`Integer.MIN_VALUE` no arrastren el contador), y es **idempotente**: si la asignación ya
existe la devuelve sin volver a publicar, para no consumir claves ni duplicar filas.

**Por qué no lo cazó la suite.** `test_assign_role_to_user_publishes_event` comprobaba que se
publicara el evento con `idusuario` e `idrol` — nunca que la fila tuviera clave primaria, que
es justo lo que Pinot necesita para no pisar la anterior. El doble tampoco modela el upsert.
Las regresiones nuevas aseveran que dos asignaciones a usuarios distintos reciben claves
**distintas y positivas**, y que repetir la misma no publica de nuevo. Hubo que enseñarle al
doble las dos consultas nuevas (`MAX(idusuariorol)` y el filtro por `idusuario`+`idrol`).

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**. Contra el stack real: tras
reasignarle el rol, Teresa vuelve a entrar, y su fila queda con `idusuariorol = 9002` en vez
del centinela.

> **Queda una fila huérfana** con `idusuariorol = Integer.MIN_VALUE` (usuario 9003, rol
> `Unidad`), creada antes del arreglo. Funciona —las lecturas filtran por `idusuario`— y con
> el contador ya en positivo nadie volverá a pisarla, pero conviene sanearla si se hace
> limpieza de datos. Ver §7.4.

---

## 2026-08-12 — B24: la baja de una unidad ajena revelaba que estaba en misión

Alcance: `backend/apps/red_operativa/services/baja_unidad_service.py`,
`backend/apps/red_operativa/tests/services/test_baja_unidad_service.py`.

**Hallazgo.** Probando la regla del SRS §3.5.1 "solo puede operar sobre unidades de su propia
organización". La pertenencia **sí se valida** en editar, ver y dar de baja —los tres
responden 403 "La unidad no pertenece a este proveedor"—, pero en la baja se comprobaba
**después** del despacho activo. Con una unidad ajena que además estuviera en misión, la
respuesta era "La unidad tiene un despacho activo; solo un Administrador puede ejecutar la
baja forzada": se denegaba la operación, correcto, pero de paso se le revelaba a otra
organización el estado operativo de una unidad que no es suya.

**Cambio de código.** Para quien no es Administrador, la pertenencia se comprueba antes de
mirar el despacho. La exención del Administrador quedó **acotada a la baja forzada**: sin
despacho activo la baja es gestión ordinaria de flota y se le sigue exigiendo pertenencia,
porque el SRS dice que la intervención de TSI es "la única excepción al autoservicio del
proveedor". Ese matiz lo cazó un test existente
(`test_dar_de_baja_when_admin_raises`) cuando una primera versión del arreglo le dio al
Administrador una exención general — el test tenía razón y el arreglo se acotó.

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**, con la regresión
`test_baja_de_unidad_ajena_con_despacho_responde_por_pertenencia`. Contra el stack real, con
la sesión de otro proveedor, la baja de una unidad ajena en misión responde ahora "La unidad
no pertenece a este proveedor".

---

## 2026-08-12 — Verificado sin cambios: alta de unidad con acceso y flota propia

Alcance: ninguno (solo pruebas). SRS §3.5.1.

- **Alta con correo**: responde 201 con `usuario_creado: true` e `invitacion_enviada: true`,
  y en Pinot quedan el usuario con su correo y `activo`, una **credencial temporal** en
  estado `Cambio contraseña` —así entra al circuito de cambio obligatorio de B5— y la
  asignación del rol `Unidad` (idrol 7).
- **Alta sin correo**: la unidad queda en el catálogo con `idusuario = null` y
  `usuario_creado = false`.
- **Solo flota propia**: con la sesión de otro proveedor, **ver**, **editar** y **dar de
  baja** una unidad ajena responden 403 "La unidad no pertenece a este proveedor".

---

## 2026-08-12 — B22: la placa dejaba de ser única en cuanto una unidad se daba de baja

Alcance: `backend/core/repositories/red_operativa/unidad_emergencia_repository.py`,
`backend/apps/red_operativa/services/{registro_unidad_service,importacion_lote_unidad_service}.py`,
`backend/conftest.py`,
`backend/apps/red_operativa/tests/{services/test_registro_unidad_service,api/test_reactivar_unidad_contract}.py`.

**Hallazgo.** Primer defecto de Red Operativa (SRS §3.5.1), detectado al probar la unicidad
de placa desde el formulario de alta. Registrar una unidad con la placa de otra **activa**
responde 409, correcto. Pero con la placa de una unidad **dada de baja** respondía **201**, y
quedaban dos unidades con la misma placa.

**Por qué importa.** El SRS dice "la placa es el identificador único de negocio… antes de
registrar, el sistema verifica que no exista ya una unidad con esa placa", sin distinguir por
estado. Y añade que "reactivar una unidad es posible; el registro de su baja previa permanece
como historial": al reactivar la antigua quedaban **dos unidades activas con la misma placa**.
Es además el identificador con el que las pantallas de flota y despacho nombran a la unidad
(design-system §8), así que el duplicado las vuelve ambiguas justo donde importa.

**El matiz que costó encontrar.** La comprobación no puede ser simplemente "existe la placa
en cualquier estado". La carga en lote es todo-o-nada y, como Pinot no tiene transacciones,
su *rollback* compensa **desactivando** lo ya insertado; el módulo trata lo inactivo como
liberado, y hace lo mismo con el correo ("reusa usuario inactivo… para no bloquear gmail").
Con la regla estricta, un lote que fallara dejaba sus placas bloqueadas para siempre y el
reintento —que el SRS exige que funcione— se rompía. Lo detectó
`test_importar_when_credencial_falla_gmails_quedan_reutilizables`.

**Cambio de código.** Se distingue la **baja de negocio** del **rastro de un lote
compensado**, usando un dato que ya existe: toda baja real registra motivo y tipo en
`Fact_BajaUnidad` (verificado contra el stack: una baja por el flujo normal escribe su fila
con `tipobaja = "Normal"`). `RegistroUnidadService._validar_placa_libre()` rechaza si la placa
pertenece a una unidad activa, o a una inactiva **con baja registrada** —en ese caso el
mensaje dice qué hacer: "Reactívala en vez de registrar una nueva"—, y la admite si la unidad
inactiva no tiene baja. La carga en lote llama al mismo método, así que las dos vías comparten
criterio. Se añadió `find_by_placa()` al repositorio, que busca en cualquier estado.

**Por qué no lo cazó la suite.** El doble de `conftest.py` aplicaba el filtro `activo` a
**toda** consulta por placa, mirase lo que mirase el SQL, así que `find_by_placa` recibía solo
las activas y la prueba no podía ver el fallo. Se corrigió el doble para que respete la
cláusula (`ACTIVO = TRUE` solo cuando la consulta la lleva), en la línea de lo que ya se hizo
con el JOIN de B1.

**Test que codificaba el defecto.** `test_post_reactivar_when_placa_duplicada_returns_409`
daba por bueno que el alta duplicada pasara (201) y esperaba que el choque se detectara
**al reactivar**. Como reactivar es opcional, lo normal era quedarse con el duplicado sin que
nadie lo notara. Se reescribió: ahora comprueba que el **alta** se rechaza y que la unidad
original sigue pudiendo reactivarse sin conflicto.

**Verificación.** `python -m pytest` → **1623 passed, 2 skipped**. Contra el stack real: dar
de baja una unidad por el flujo normal escribe su `Fact_BajaUnidad`, y el intento posterior de
registrar otra con esa placa responde 409 con el mensaje que indica reactivar.

> **Dato sucio detectado de paso.** Las unidades inactivas que ya había en el entorno demo
> (`HUMO-99`, `ABC-123`, `NUEVA-X1`…) **no tienen registro de baja**: `Fact_BajaUnidad` estaba
> vacía. Se desactivaron por script o por pruebas antiguas, no por el flujo del producto. Sus
> placas siguen siendo reutilizables, que es el tratamiento correcto para un rastro sin baja.

---

## 2026-08-12 — B21: una suscripción se facturaba una sola vez en su vida

Alcance: `backend/apps/suscripciones/services/renovacion_service.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo.** Detectado al preparar la prueba del ciclo de mora. Se venció el ciclo de una
suscripción y se ejecutó `run_renovacion_job`: respondió `{'renovadas': 1}`, la suscripción
recorrió el ciclo… y **no se emitió ninguna factura nueva**. El cliente seguía con la única
factura de su alta.

**Causa.** `GeneracionFacturaService.periodo_actual()` deriva el período de
`Fact_Suscripcion.fecha_inicio`, y la renovación solo avanzaba `fecha_fin`. Con
`fecha_inicio` clavada en la fecha del alta, **todo ciclo calculaba el mismo período**, la
guarda de "no duplicar factura del mismo período" encontraba la factura original y devolvía
esa en vez de crear una; como ya estaba `Pagada`, `ejecutar_batch()` ni siquiera la contaba
como creada.

**Efecto.** El SRS §3.3.1 dice "a fin de cada ciclo, el sistema genera automáticamente la
factura de cada suscripción activa". En la práctica se facturaba **el primer ciclo y ninguno
más**: el servicio se renovaba indefinidamente y no se volvía a cobrar nunca. Es una fuga de
ingresos silenciosa — ningún error, ningún estado raro, simplemente no aparecen facturas.

**Cambio de código.** La renovación avanza `fecha_inicio` al arranque del ciclo nuevo (el
`fecha_fin` anterior), junto con `fecha_fin`. `Fact_Suscripcion.fecha_inicio` pasa a
significar "inicio del ciclo vigente", que es lo que necesitan sus dos únicos consumidores:
`periodo_actual()` y los `ORDER BY fecha_inicio DESC` que eligen la suscripción más reciente.
No se pisa la antigüedad del cliente, que vive en otro campo y otra tabla
(`Dim_Cliente.fecha_inicio_contrato`).

**Verificación.** `python -m pytest` → **1622 passed, 2 skipped**, con la regresión
`test_cada_ciclo_renovado_factura_su_propio_periodo`. Contra el stack real, tras vencer el
ciclo y renovar, el cliente pasa a tener **dos** facturas, una por ciclo, con períodos
distintos.

---

## 2026-08-12 — Verificado sin cambios: mora, reintentos, suspensión y reactivación

Alcance: ninguno (solo pruebas). SRS §3.3.1.

Recorrido completo del ciclo de mora contra el stack real, forzando el fallo de la pasarela
con `BILLING_SIMULATOR_FAIL_RATE=1` e inyectando `now` en `run_dunning(now=...)` para situarse
en D+3 y D+5 sin tocar datos:

1. **Emisión con cobro fallido.** La factura del período nace `Pendiente` con
   `reintentos = 1` y `SIM_DECLINED` — el intento del día 0.
2. **D+3 → segundo intento**, `reintentos = 2`. **D+5 → tercero**, `reintentos = 3`.
3. **Agotados los reintentos**, la factura queda `Fallida` y la suscripción **`Suspendida`**.
4. **Acceso mínimo conservado.** En pantalla: "Estado: Suspendida · Acceso: DENEGADO", pero
   el cliente conserva "Métodos de pago" y "Reintentar cobro". "Cambiar plan" no aparece
   (F5 + la guarda B15). Es exactamente lo que pide el SRS: pierde el acceso operativo pero
   no queda "atrapado sin poder pagar".
5. **Reactivación.** "Reintentar cobro" responde 200 con
   `{estado_pago: "Pagada", estado_suscripcion: "Activa", resultado_ultimo_reintento:
   "Exitoso"}`, y Pinot confirma la factura `Pagada` y la suscripción `Activa`. **Este paso
   es el que validaba el arreglo B19 contra el sistema real**: antes, la relectura devolvía
   la factura todavía `Fallida` y la regularización se saltaba el cobro en silencio.
6. **Tras cancelar no se emite nada más.** Con la suscripción `Cancelada`, tanto
   `run_facturacion_mensual_job` como `run_renovacion_job` responden 0.

> **Anotado como deuda, no corregido.** `Fact_Factura` usa `fecha_emision` como
> `comparisonColumns` del upsert, mientras que el resto de tablas del proyecto usa
> `fecha_actualizacion`. `fecha_emision` no cambia nunca tras la emisión, así que todas las
> actualizaciones de una factura se comparan con el mismo valor y su orden depende de cuál
> llegue antes, sin protección contra un escritor rezagado. Hoy funciona porque las
> escrituras conservan `fecha_emision` y Pinot acepta el valor igual; se detectó porque un
> intento de *retrasar* `fecha_emision` fue rechazado por out-of-order. Ver §7.4.

---

## 2026-08-12 — B17–B20/F5: el ciclo de facturación y mora no funcionaba de punta a punta

Alcance: `backend/core/repositories/suscripciones/factura_repository.py`,
`backend/apps/suscripciones/services/{alta_suscripcion_service,mora_suscripcion_service}.py`,
`backend/apps/suscripciones/jobs/{facturacion_mensual_job,dunning_job}.py`,
`backend/apps/suscripciones/tests/{repositories/test_factura_repository,services/test_alta_suscripcion_service,services/test_mora_suscripcion_service}.py`,
`frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.html`.

**Origen.** Al probar la contratación desde cero con un cliente nuevo
(`teresa.beltran@demo.tsi.com`) y ejecutar el ciclo de facturación contra el stack real.
Cuatro defectos encadenados; ninguno se veía desde la suite.

**B17 — la factura no llegaba a existir.** `run_facturacion_mensual_job` informaba
`{'facturas': 1}` y `Fact_Factura` seguía vacía. `desglose_cargos` está declarada como
columna **STRING de valor único**, y el servicio publicaba la lista de conceptos tal cual:
Pinot descartaba la fila entera con `Cannot read single-value from Collection`. Cuarta
aparición del descarte silencioso, esta vez por forma del dato y no por tipo. Corregido en el
repositorio, que es la frontera con Pinot: `_desglose_json()` serializa al escribir —también
en `update_from`, porque la tabla es upsert y republica la fila entera— y `_hidratar()`
devuelve la lista al leer, que es como la recorre la pantalla de facturas.

**B18 — contratar con método de pago ya registrado daba 500.** `AltaSuscripcionService`
emitía la factura y la cobraba con `CobroService().intentar(factura["id_factura"])`, que la
relee de Pinot. Es el mismo patrón de B14, en la ruta de alta. Teresa no lo disparó porque
contrató **sin** método; cualquier cliente que ya tuviera uno recibía un 500 al contratar.

**B19 — el cliente suspendido no podía regularizar nunca.** `MoraSuscripcionService.
regularizar()` reabre la factura a `Pendiente` y la cobra. Como la cobraba por id, Pinot
devolvía todavía la versión anterior con `estado_pago = "Fallida"`, y el cobro salía por su
guarda de "no está Pendiente" sin intentar nada; el servicio interpretaba el resultado como
fallo y volvía a marcarla `Fallida`. La suscripción se quedaba **Suspendida para siempre** —
exactamente lo que el SRS §3.3.1 quiere evitar cuando dice que el cliente "conserva el acceso
mínimo necesario para regularizar su situación, de lo contrario quedaría atrapado sin poder
pagar".

**B20 — el ciclo de mora solo miraba diez facturas.** `run_dunning` recorría
`SELECT * FROM Fact_Factura` sin `LIMIT`, y `factura_vigente_fallida()` hacía lo mismo. Bajo
el `LIMIT 10` implícito de Pinot, el resto de facturas del sistema no se reintentaban ni
suspendían nunca, y la factura fallida de un cliente concreto podía no aparecer, dejándolo
suspendido sin nada que regularizar.

**Cambio de código.** Se añadió `CobroService.intentar_factura(factura, ...)` en la entrega
anterior (B14) y ahora la usan **todos** los llamadores que ya tienen la fila: alta,
facturación mensual, mora y el job de dunning. `intentar(id_factura)` se conserva para quien
solo tiene el id. Las dos consultas sin `LIMIT` pasan a filtrar en SQL con `LIMIT` explícito,
usando los nombres de parámetro que el doble de `conftest.py` ya reconoce, para que la suite
ejercite la misma consulta que corre en producción.

**F5 — se ofrecían acciones imposibles.** Con la suscripción Cancelada o Suspendida, "Mi
suscripción" seguía mostrando el botón "Cambiar plan", que desde B15 responde siempre 409. Se
condiciona a `estado === 'Activa'`, igual que ya se hacía con "Reintentar cobro" y con el
bloque de cancelación.

**Por qué no lo cazó la suite.** El doble refleja cada escritura al instante y no valida la
forma del dato contra el esquema. Las regresiones nuevas no le preguntan: aseveran que el
payload publicado lleva `desglose_cargos` como **cadena** y que el llamador lo recibe como
lista, y anulan `find_by_id` con `patch.object` para reproducir el retardo real en el alta y
en la regularización de mora.

**Verificación.** `python -m pytest` → **1621 passed, 2 skipped**. Contra el stack real, el
ciclo completo: Teresa contrata Básico desde cero (`201`, suscripción `Activa` $49 en Pinot),
registra una tarjeta, y `run_facturacion_mensual_job` emite y cobra —
`FAC-202608-00000001`, período `2026-08`, base 49.00, impuestos 0.00, total 49.00,
`estado_pago = Pagada`, `resultado_ultimo_reintento = Exitoso`, con el desglose bien formado.
Al reejecutar el job responde `{'facturas': 0}` y el cliente sigue con **una sola** factura:
la regla de no duplicar período se cumple. La pantalla "Facturas" muestra la emisión y el
detalle desglosa "Suscripcion plan Básico — $49.00".

> **Falta todavía.** El camino de **mora con cobro fallido** —reintentos a D+3 y D+5,
> suspensión al agotarlos y reactivación al regularizar— no se ha recorrido contra el stack
> real: exige forzar el fallo de la pasarela y mover fechas de emisión. Sigue en §7.2.

---

## 2026-08-12 — B15/B16: un cliente suspendido por impago podía subirse de plan

Alcance: `backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/apps/suscripciones/services/alta_suscripcion_service.py`,
`backend/core/repositories/suscripciones/suscripcion_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo (B15).** Probando la regla del SRS §3.3.1 "no se admite cambiar de plan sobre una
suscripción **suspendida o cancelada**". Se suspendió la suscripción de Ana Torres y se pidió
una mejora de plan: respondió **201** y, por ser mejora, se **autoaprobó y se aplicó**.

**Causa.** `CambioPlanService.solicitar()` solo comprobaba que existiera suscripción vía
`find_activa_by_cliente()`, que filtra por `activo`, no por `estado`. Suspender por mora
(`MoraSuscripcionService.suspender_por_factura`) cambia únicamente `estado` a `"Suspendida"`
y deja `activo = True`, así que la suscripción suspendida pasaba la comprobación. La guarda
que el SRS declara obligatoria sencillamente no existía.

**Efecto.** Un cliente suspendido por falta de pago podía **mejorarse solo a un plan más
caro**, con aplicación inmediata, mientras no estaba pagando. Es la misma familia que B9 del
2026-08-11 (se podía iniciar sesión con la organización dada de baja): una regla que el SRS
enuncia como obligatoria y que no estaba escrita en ninguna parte del código.

**Hallazgo (B16), destapado al mirar el repositorio.** `find_activa_by_cliente()` hacía
`SELECT * FROM Fact_Suscripcion` sin `LIMIT` y filtraba en Python, bajo el `LIMIT 10`
implícito de Pinot. Es la consulta más central del módulo —la usan el alta, el cambio de
plan, "Mi suscripción", el cobro y la mora—, así que en cuanto existan suscripciones de once
clientes, a algunos les respondería "Sin suscripción activa": sin plan, sin factura y sin
acceso, sin ningún error de por medio.

**Cambio de código.** `solicitar()` exige `estado == "Activa"` y responde **409** con un
mensaje en lenguaje del negocio ("No se puede cambiar de plan con la suscripción
suspendida"). La guarda va en el servicio y no en `find_activa_by_cliente`, porque hay
flujos que **sí** necesitan la suscripción suspendida: regularizar la mora y mostrar el
estado en pantalla. El repositorio pasa el filtro a SQL con `LIMIT` explícito y documenta que
devuelve también las suspendidas. De paso, el alta decía "Ya existe una suscripción
activo=true": se reescribió a "Esta cuenta ya tiene una suscripción vigente" — el mensaje
filtraba el nombre de una columna al usuario.

**Verificación.** `python -m pytest` → **1617 passed, 2 skipped**, con la regresión
parametrizada `test_no_se_cambia_de_plan_sobre_suscripcion_no_activa` (Suspendida y
Cancelada), que además comprueba que el plan **no** cambió. Contra el stack real, la misma
petición que antes devolvía 201 y aplicaba la mejora ahora devuelve 409. La regla de **una
sola suscripción activa por cliente** se verificó en la misma pasada: el alta sobre un
cliente que ya tiene suscripción responde 409. Con la suscripción ya **Cancelada**, la misma
petición de cambio de plan responde igualmente 409.

**Verificado sin cambios — cancelación (SRS §3.3.1).** Se canceló la suscripción de Ana
Torres desde la pantalla: queda `Cancelada` con motivo y fecha, `renovacionautomatica` pasa a
`false`, y **el servicio no se corta** — `fecha_fin` intacta y "Acceso: Permitido" en
pantalla, con el aviso "Conservarás acceso hasta la fecha de fin". Coincide con el SRS. Falta
comprobar que a partir de ahí **no se emite ninguna factura más**, que exige llegar al cierre
del período.

> **Detalle de interfaz anotado, no corregido.** Con la suscripción Cancelada o Suspendida,
> "Mi suscripción" sigue ofreciendo el botón "Cambiar plan", que ahora siempre responde 409.
> La regla ya está aplicada en el backend; lo que falta es no ofrecer la acción. Anotado en
> §7.1 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — B14: el job de renovación reventaba al cobrar la factura recién emitida

Alcance: `backend/apps/suscripciones/services/cobro_service.py`,
`backend/apps/suscripciones/services/renovacion_service.py`,
`backend/core/repositories/suscripciones/factura_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo.** Detectado al verificar contra el stack real que una reducción programada se
aplica al renovar (decisión #27, abajo). `python manage.py run_renovacion_job` terminaba con
`ValueError: factura no encontrada`.

**Causa.** Tercera aparición del mismo patrón en esta jornada.
`RenovacionService.ejecutar_batch()` emitía la factura del período nuevo y acto seguido
llamaba a `CobroService.intentar(factura["id_factura"])`, que arranca con
`facturas.find_by_id(...)`. La factura acababa de salir por Kafka, Pinot todavía no la
exponía, y el método levantaba la excepción. `FacturaRepository.update()` tenía además el
mismo `find_by_id` al principio, así que el resultado del cobro tampoco se habría guardado.

**Efecto.** La excepción no estaba capturada, así que **abortaba el batch entero**: las
suscripciones que quedaran después de la primera renovada en la misma corrida no se
renovaban, y como el job es la vía por la que se recorre el ciclo y se emite la factura,
el ciclo de facturación no avanzaba.

**Cambio de código.** Se añadió `CobroService.intentar_factura(factura, ...)`, que opera
sobre la factura ya en memoria; `intentar(id_factura)` se mantiene para los llamadores que
solo tienen el id (reintento manual, mora) y ahora delega en ella tras leerla. La renovación
usa `intentar_factura` con la factura que acaba de emitir. En el repositorio se añadió
`update_from(current, changes)` —mismo criterio que en solicitudes de cambio de plan— y las
dos escrituras del cobro (pago exitoso y fallo) pasan a usarla, con lo que dejan de releer.

**Verificación.** `python -m pytest` → **1615 passed, 2 skipped**, con la regresión
`test_renueva_aunque_pinot_aun_no_exponga_la_factura`, que anula `find_by_id` para
reproducir el retardo. Contra el stack real, `run_renovacion_job` pasa de reventar a
responder `{'renovadas': 1}`. No se generó factura nueva en esa corrida porque ya existía
una del mismo período para esa suscripción — el comportamiento correcto según el SRS
("nunca se emite una factura duplicada para el mismo período y la misma suscripción").

> **No cubierto todavía.** La emisión de factura, la mora, los reintentos y la suspensión
> siguen sin recorrerse de punta a punta; siguen en §7.2 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — Decisión #27: la reducción de plan aplica al cierre del ciclo

Alcance: `database/esquemas.json`, `database/migra_plan_programado.py` (nuevo),
`backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/apps/suscripciones/services/renovacion_service.py`,
`backend/apps/suscripciones/views/suscripcion_views.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`,
`frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.html`,
`frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts`.

**Origen.** Al probar el cambio de plan (ver B12 arriba) se detectó que el SRS §3.3.1 dice
dos cosas incompatibles: que "una mejora de plan se autoaprueba y **aplica de inmediato**"
y, dos párrafos después, que "todo cambio de plan aplica a partir del **siguiente ciclo** de
facturación". El sistema aplicaba todo de inmediato, de modo que una reducción aprobada a
mitad de ciclo le retiraba al cliente, en el acto, un nivel de servicio que ya había pagado
hasta el fin del período; y como la factura se emite al cerrar con el precio que la
suscripción tenga en ese momento, el cliente pagaba el ciclo entero al precio bajo aunque
hubiera disfrutado medio ciclo del plan alto — justo el prorrateo que la regla prohíbe.

**Decisión (2026-08-12, opción 1).** La **mejora** sigue aplicando de inmediato; la
**reducción** aprobada queda **programada** y la aplica el job de renovación al recorrer el
ciclo. Es la única lectura que no contradice ninguna de las dos frases del SRS en el caso
que perjudica al cliente. Detalle y alternativas descartadas en `decisiones-pendientes.md`
#27.

**Cambio de código.** Columna `idplan_programado` (INT, centinela `0` = sin cambio
programado) en `Fact_Suscripcion`, con migración aditiva y respaldo previo.
`CambioPlanService._aprobar()` bifurca según el sentido del cambio: la mejora copia los
campos del plan; la reducción solo anota el plan programado y no toca plan, precio, nivel ni
severidades. En ambos casos la solicitud queda `Aprobada`: lo que se difiere es la
aplicación, no la decisión. `RenovacionService` aplica el cambio programado en la **misma
escritura** que recorre el ciclo y limpia la marca, antes de generar la factura, de modo que
el período nuevo se factura ya al precio nuevo. `GET /suscripciones/mia` devuelve
`plan_programado_nombre` —el nombre, no el id (design-system §8)— y "Mi suscripción" avisa
al cliente de la fecha en que se aplicará; sin ese aviso vería su plan actual sin saber que
el cambio ya está aprobado.

**Verificación.** `python -m pytest` → **1614 passed, 2 skipped**, con dos regresiones
nuevas: que la reducción aprobada **no** cambia el plan vigente, y que la renovación **sí**
lo aplica y limpia la marca. En el navegador contra el stack real: el Administrador aprueba
la reducción de Ana Torres a Básico y Pinot conserva `idplan=2, precio=149.0,
nivel='Profesional'` con `idplan_programado=1`; la pantalla sigue mostrando Profesional ·
$149.00 más el aviso *"Tu cambio al plan Básico ya está aprobado y se aplicará el Jun 26,
2027, al terminar el ciclo que ya pagaste."*

---

## 2026-08-12 — B10/B11/F4: el método de pago no llegaba a existir

Alcance: `core/pinot/tiempo.py`,
`backend/core/repositories/suscripciones/metodo_pago_repository.py`,
`backend/apps/suscripciones/tests/repositories/test_metodo_pago_repository.py`,
`frontend/src/app/modules/suscripciones/pages/metodos-pago/`,
`frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts`.

**Hallazgo (B10).** Detectado al probar el registro de método de pago desde el navegador
(SRS §3.3.1, RF-SUSF-002). La pantalla confirmaba "Método registrado. El PAN no se
almacena…", pero la lista seguía diciendo "Aún no hay métodos" indefinidamente. No era el
retardo de lectura tras escritura: `Dim_MetodoPago` tenía `totalDocs: 0`.

**Causa.** `MetodoPagoService.registrar()` pasaba la expiración del formulario tal cual
(`"12/30"`, formato MM/AA) y el repositorio la publicaba sin convertir. En el esquema,
`fechaexpiracion` es un `dateTimeFieldSpec` **LONG** con formato `1:MILLISECONDS:EPOCH`.
Pinot descartó la fila entera: `NumberFormatException: For input string: "12/30"` en
`pinot-server`. Es el mismo patrón de B3/B4 sobre una columna distinta — la API respondía
201 y el registro no existía.

**Efecto.** Ningún cliente podía registrar un método de cobro. Como el alta de método es
también lo que dispara la regularización de una suscripción suspendida por mora
(`MoraSuscripcionService.regularizar`), un cliente en mora **no tenía forma de
regularizar**.

**Hallazgo (B11), en el mismo fichero.** `list_by_cliente()` hacía
`SELECT * FROM Dim_MetodoPago` sin `LIMIT` y filtraba por cliente en Python. Pinot aplica
un `LIMIT 10` implícito sobre la tabla entera, así que en cuanto hubiera métodos de once
clientes, a algunos les desaparecería el suyo de la pantalla sin ningún error.

**Cambio de código.** Se añadió `mes_anio_a_ms()` a `core/pinot/tiempo.py`, junto a
`ahora_ms()` y `SIN_FECHA`, que convierte `MM/AA` (o `MM/AAAA`) al último milisegundo del
mes de expiración — una tarjeta `12/30` es válida hasta el final de diciembre de 2030 — y
devuelve `SIN_FECHA` ante cualquier valor ausente o ilegible, que es el caso de PayPal y
transferencia. El repositorio sella `fechaexpiracion` en `create()` y también en
`update()`, porque la tabla es upsert y republica la fila entera; al releer desde Pinot el
epoch puede volver como cadena numérica, y eso no se reinterpreta como `MM/AA`. El listado
pasa el filtro a SQL con `WHERE idcliente` y `LIMIT` explícito.

**F4 — La expiración se imprimía como epoch crudo.** Corregido el efecto colateral en
pantalla: la tabla mostraba `1924991999999`. Se añadió `expiracion()` en
`metodos-pago.page.ts`, que devuelve `MM/AAAA` y `—` para el centinela; el tipo
`MetodoPago.fechaexpiracion` pasó a `number | string | null`.

**Por qué no lo cazó la suite.** El doble en memoria de `conftest.py` no valida tipos
contra el esquema: aceptaba la cadena sin protestar. La regresión añadida no consulta al
doble, sino que asevera el **payload publicado a Kafka** — que `fechaexpiracion` sea `int`
y valga exactamente `1924991999999` para `12/30`, y que los valores ilegibles (`None`,
`""`, `"sin-fecha"`, `"13/30"`) caigan en `SIN_FECHA`.

**Verificación.** `python -m pytest` → **1612 passed, 2 skipped** (1607 previos + 5 nuevos).
En el navegador, con el stack real: al guardar una tarjeta `12/30` la fila aparece en Pinot
con `fechaexpiracion = 1924991999999` y la pantalla muestra `12/2030 · Activo`. Al registrar
después un PayPal, la consulta a Pinot devuelve la tarjeta con `activo = False` y el PayPal
con `activo = True` y `SIN_FECHA`, y la pantalla los muestra como `Inactivo` y
`Activo · —`: se confirma la regla del SRS de que reemplazar el método **desactiva** el
anterior en vez de borrarlo.

> **Suite de frontend no ejecutable en esta máquina.** `npx ng test` no completó ninguna
> corrida: Karma lanza Edge, ejecuta entre 6 y 296 de las 599 specs —**ninguna falla**— y
> entonces el lanzador aborta con `ChromeHeadless failed 2 times (cannot start)` y cierra
> el servidor. Ocurre igual sin los cambios de esta entrada, con timeouts ampliados y con
> perfil aislado, y hay 17 procesos `msedge` del usuario abiertos. Queda como deuda en
> §7.4 de `REVISION-SRS-ESTADO.md`. `npx tsc --noEmit` pasa, pero no valida plantillas: lo
> de esta entrada se verificó en el navegador contra el contenedor reconstruido.

---

## 2026-08-11 — B1: la asignación automática de prospectos usaba un JOIN que Pinot rechaza

Alcance: `backend/apps/ventas_crm/services/asignacion_automatica_service.py`,
`backend/conftest.py`.

**Hallazgo (B1).** Detectado al probar el registro público de prospectos desde el
navegador (SRS §3.1.1, "Inmediatamente después, el prospecto se asigna a un ejecutivo
comercial"). `POST /api/v1/ventas-crm/prospectos` devolvía **500** contra el entorno real.

**Causa.** `AsignacionAutomaticaService.asignar()` resolvía el ejecutivo con un JOIN de
tres tablas (`Dim_Usuarios` ⋈ `Dim_Usuario_Rol` ⋈ `Dim_Rol`). Pinot no admite JOIN entre
tablas en el motor de consulta de este proyecto y lo rechaza en el parser
(`errorCode 150`, `SQLParsingError ... compileToJoin`).

**Por qué no lo cazó la suite.** `backend/conftest.py` tenía una rama del doble en memoria
que reconocía literalmente `"JOIN DIM_USUARIO_ROL"` y devolvía el resultado correcto. La
suite pasaba en verde sobre una consulta que ningún Pinot real podría ejecutar — el caso
exacto de "confianza falsa" que ya advertía la documentación del doble.

**Efecto verificado.** El prospecto llegaba a crearse y luego la petición reventaba, así
que el visitante veía "No se pudo registrar" sobre un prospecto que sí existía; el segundo
intento con el mismo correo respondía "gmail ya registrado". Tras el arreglo, el registro
público responde "Registro enviado" y el prospecto queda asignado.

**Cambio de código.** La resolución rol → usuarios se hace en dos consultas, reutilizando
`RoleRepository.list_user_ids_for_role()` (idiom ya vigente en el resto del código) y
filtrando después los usuarios activos con `idusuario IN (...)`. Se eliminó la rama del
JOIN en `conftest.py` y se añadió el soporte genérico de `Dim_Usuarios ... IDUSUARIO IN`,
de modo que la suite ejercite las mismas consultas que corren en producción.

**Verificación.** `python -m pytest` → 1596 passed, 2 skipped. Registro público
comprobado click a click en el navegador contra el stack Docker.

---

## 2026-08-11 — D1/F1: identificadores internos en pantalla y límites de plan sin valor

Alcance: `.specify/docs/design/design-system.md` (§8, nueva),
`backend/apps/red_operativa/views/unidad_views.py`,
`frontend/src/app/modules/red-operativa/alta-unidades/` (detalle y contrato),
`frontend/src/app/modules/suscripciones/pages/{catalogo-planes,plan-detalle}/`.

**D1 — Regla global: no se muestran identificadores internos.** Detectado al revisar el
detalle de una unidad, que mostraba "Usuario login: 12" a quien administra la flota. Un id
no le permite al usuario verificar nada, y pedirle que lo escriba le obliga a conocer la
clave primaria de una tabla. Se añadió la §8 al `design-system.md` — que es la autoridad
de diseño — con los cuatro casos (mostrar nombre, combobox contra la tabla catálogo,
identificadores que sí son lenguaje de negocio como el número de caso o la placa, y qué
hacer cuando no hay nombre). La sección incluye la lista de pantallas que todavía
incumplen, para que la regla no se lea como ya cumplida.

**Efecto verificado.** `GET /unidades/{id}` devuelve ahora `usuario_nombre` resuelto contra
`Dim_Usuarios` (nombres + apellidos, con el correo como respaldo), y el detalle pinta ese
nombre en vez del id; sin acceso asignado muestra "Sin acceso asignado". El `idusuario`
sigue viajando en la respuesta: la regla es sobre lo que se pinta, no sobre el transporte.

**F1 — El catálogo de planes imprimía `undefined`.** "Demo sin tarifa" se mostraba como
"undefined unidades · undefined usuarios · 10000 API/mes". `limitesTexto()` interpolaba
las cuatro claves de límites sin comprobar su presencia, y ese plan solo traía las de API.
Ahora se omiten las claves ausentes y, si no queda ninguna, se muestra "Sin límites".
Corregido en las dos copias de la función (catálogo y detalle de plan).

**Dato corregido desde la propia UI (no es cambio de código).** Los planes `Magnifico` y
`Demo sin tarifa` se habían creado sin severidades ni carga en lote — el formulario sí
captura ambas, se guardaron sin marcar. Se editaron desde la pantalla de edición de planes:
`Magnifico` (Empresarial) quedó con Baja · Media · Alta y carga en lote, y `Demo sin tarifa`
(Profesional) con Baja · Media, carga en lote y los límites de unidades y usuarios que le
faltaban. El formulario ya valida "Selecciona al menos una severidad".

---

## 2026-08-11 — B2: el catálogo de planes usaba una escala de severidades que no existía

Alcance: `backend/core/repositories/suscripciones/severidad_repository.py` (nuevo),
`backend/apps/suscripciones/{services/catalogo_plan_service.py,views/plan_views.py,urls.py}`,
`backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`,
`backend/apps/partners/services/consumo_datos_service.py`,
`backend/scripts/seed_planes_publicos.py`, `backend/conftest.py`,
`database/migra_severidades_plan_a_idseveridad.py` (nuevo),
`frontend/src/app/modules/suscripciones/` (form, catálogo, detalle, tipos y servicio),
specs de `subscriptions-and-billing` (spec, data-model, contrato `v1.2.0`),
`decisiones-pendientes.md` #23 (cerrada).

**Hallazgo (B2).** El formulario de plan ofrecía tres severidades escritas en duro —
`Baja`, `Media`, `Alta` — que no correspondían a ninguna fila de `Dim_Severidad`, cuyo
contenido real es `Leve`, `Moderado`, `Grave`, `Fatal`. Dos vocabularios para la misma
cosa, unidos por un diccionario puente (`SEVERIDADES_POR_NIVEL`) en Partners.

**Por qué importaba.** El gating de alcance de Partners es fail-closed: una equivalencia
mal elegida no produce un error visible, produce **cero resultados**, que el partner
interpreta como "no hubo accidentes". Además la lista escrita en el componente incumplía
el requisito de configurabilidad del SRS §6 — añadir una severidad exigía tocar código.

**Decisión de negocio (usuario, 2026-08-11).** Migrar ahora al catálogo real, y que un plan
que cubría `Alta` **siga cubriendo Grave y Fatal**: nadie pierde cobertura respecto de lo
contratado.

**Cambio.** `severidades_desbloqueadas` guarda `idseveridad` en `Dim_Plan` y en
`Fact_Suscripcion`. La validación lee los ids activos de `Dim_Severidad` en vez de una
constante. Nuevo `GET /api/v1/suscripciones/severidades` que alimenta el selector del
formulario. El portal público recibe los **nombres ya resueltos**, no ids — una vitrina sin
autenticar no muestra claves primarias (§8 del `design-system.md`). El puente de Partners
quedó borrado, y el vocabulario retirado ya no se reinterpreta: si una fila sin migrar se
colara, da conjunto vacío y falla cerrado, que es el comportamiento correcto.

**Migración de datos.** `database/migra_severidades_plan_a_idseveridad.py` reescribe las dos
tablas releyendo y republicando la fila entera (son upsert por clave primaria: publicar un
registro parcial borraría el resto de columnas). Ejecutada sobre el entorno local: 6 filas.

**Por qué la suite no lo cazaba.** `conftest.py` no tenía `Dim_Severidad` y sus planes de
prueba guardaban el vocabulario viejo, así que la escala paralela se validaba contra sí
misma. Se añadió la tabla al doble y se migraron los datos de prueba.

**Verificación.** `python -m pytest` → 1596 passed, 2 skipped. `ng test` → 589 SUCCESS.
En el navegador: el portal público y el catálogo interno muestran Leve/Moderado/Grave/Fatal;
el formulario de plan lista las cuatro severidades del catálogo; editar el plan Profesional
lo carga con Leve y Moderado marcados; y guardar el plan 4 persistió `[1, 2]` en `Dim_Plan`.

---

## 2026-08-11 — B3: `fecha_actualizacion` en ISO-8601 hacía que Pinot descartara las escrituras

Alcance: `backend/core/pinot/tiempo.py` (nuevo), once repositorios de
`core/repositories/{cuentas_clientes,red_operativa}/`,
`backend/tests/regression/test_fecha_actualizacion_epoch_ms.py` (nuevo).

**Hallazgo (B3).** Detectado al probar el autorregistro de clientes (SRS §3.2.2,
tercera puerta de entrada). El formulario respondía **201 Created** y mostraba
"Solicitud en revisión", pero `Dim_Cliente` seguía con dos filas antiguas: el
registro no existía. Lo mismo ocurría con la conversión de prospecto a cliente.

**Causa.** Las 58 tablas del proyecto declaran `fecha_actualizacion` como `LONG`
con formato `1:MILLISECONDS:EPOCH`, y en la mayoría es además la **columna de
tiempo** de la tabla y la columna de comparación del upsert. Once repositorios la
sellaban con `datetime.now(timezone.utc).isoformat()` — una cadena. Pinot no
rechaza esas filas con un error: **las descarta en silencio**. El escritor recibe
su payload de vuelta, la vista responde 201 y el usuario cree que guardó.

**Segundo efecto, peor.** `ClienteRepository._next_id()` calcula
`MAX(idcliente)+1` leyendo de Pinot. Como ninguna fila llegaba, dos altas
consecutivas —la conversión de un prospecto y un autorregistro— recibieron el
**mismo** `idcliente`. Si las filas hubieran llegado, la segunda habría pisado a
la primera sin dejar rastro, porque la tabla es upsert por clave primaria.

**Cambio.** Nuevo `core/pinot/tiempo.ahora_ms()` como única forma de sellar el
campo, y las 25 llamadas a `isoformat()` sustituidas por ella en los once
repositorios: cliente, credencial, onboarding, preferencias, rol, accesos de
servidor y usuario (Cuentas y Clientes); baja de unidad, región operativa, estado
de región y validación de región (Red Operativa). Es decir, toda la capa de
identidad y todo el ciclo de vida de regiones y bajas de unidad.

**Por qué la suite no lo cazaba.** El doble en memoria de `conftest.py` guarda lo
que le publiquen sin validar tipos, así que ningún test de servicio podía verlo.
Se añadió `tests/regression/test_fecha_actualizacion_epoch_ms.py`, que lee el
código fuente y falla si algún repositorio vuelve a usar `isoformat()` para este
campo, más una segunda prueba que verifica la premisa contra `esquemas.json`.

**Verificación.** `python -m pytest` → 1598 passed, 2 skipped. En el navegador:
un autorregistro nuevo aparece en `Dim_Cliente` con `fecha_actualizacion` en
epoch-ms, sale en la bandeja del Administrador y, al aprobarlo, queda en `Activo`
con `estado_onboarding` en `Pendiente`.

---

## 2026-08-11 — F2: nueve pantallas nunca repintaban lo que cargaban

Alcance: `.specify/docs/design/design-system.md` (§9, nueva),
`frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/{baja,perfil,preferencias,transferencia}`,
`.../incorporacion-clientes/pages/{aprobacion-solicitudes,onboarding-wizard}`,
`.../red-operativa/incorporacion-regional/pages/{catalogo,reevaluacion,validacion}`.

**Hallazgo (F2).** La bandeja de solicitudes de cliente mostraba "No hay
solicitudes pendientes" y el botón congelado en "Actualizando…" mientras
`GET /api/v1/cuentas-clientes/solicitudes` devolvía **200 con la solicitud**.
Verificado en los registros de Django: la petición salía y respondía.

**Causa.** `app-shell.component` es `OnPush`. Estas nueve páginas guardan su
estado en campos planos y no llamaban nunca a `markForCheck()` ni usaban signals.
Un ancestro OnPush que no está marcado como sucio corta el recorrido de detección
de cambios antes de llegar al hijo, aunque el hijo use la estrategia por defecto.
La página de autorregistro, con el mismo estilo de código, sí funcionaba — porque
vive **fuera** del shell, en una ruta pública.

**Cambio.** Las nueve páginas inyectan `ChangeDetectorRef` y llaman a
`markForCheck()` en cada callback asíncrono, que es el idiom que ya seguían las
páginas de `alta-unidades`. La regla quedó escrita en la §9 del `design-system.md`,
que es la autoridad de diseño, con el aviso de que un 200 en la pestaña de red no
es evidencia de que la pantalla funcione.

**Verificación.** `ng test` → 589 SUCCESS. En el navegador, tras reconstruir el
contenedor del frontend: la bandeja lista la solicitud pendiente con su razón
social y el flujo de aprobación se completa.

---

## 2026-08-11 — B4/F3: el usuario no nacía y el botón de cerrar sesión quedaba fuera del borde

Alcance: `backend/core/pinot/tiempo.py`,
`backend/core/repositories/cuentas_clientes/user_repository.py`,
`backend/tests/regression/test_fecha_actualizacion_epoch_ms.py`,
`frontend/src/app/shared/layout/app-shell.component.ts`.

**B4 — `fechanacimiento: ""` sobre una columna LONG.** Continuación de B3, detectado al
intentar entrar con la cuenta recién autorregistrada. El alta respondía 201 y la credencial
se creaba, pero el usuario **no existía** en `Dim_Usuarios`: `UserRepository.create`
publicaba `"fechanacimiento": data.get("fechanacimiento", "")` y esa columna es
`LONG 1:MILLISECONDS:EPOCH`. Igual que con `fecha_actualizacion`, una cadena en una columna
LONG hace que Pinot descarte la fila entera sin avisar. El resultado para el usuario era
"Credenciales inválidas o usuario inactivo" sobre una cuenta que el sistema decía haber
creado. Se publica ahora `core.pinot.tiempo.SIN_FECHA` (el centinela `Long.MIN_VALUE` que
ya llevan las filas sembradas) y se añadió una tercera prueba de regresión que recorre los
repositorios buscando **cualquier** columna dateTime publicada como cadena vacía.

**F3 — El botón de cerrar sesión era inalcanzable por debajo de ~1070px.** El grupo derecho
del header estaba marcado para no encogerse y contenía el correo y los roles sin límite de
ancho. Con un correo largo el contenido medía 1068px dentro de un contenedor de 1024, y
como el documento no tiene scroll horizontal, los últimos 44px —el botón de cerrar sesión—
quedaban simplemente cortados. A 1024px, resolución de portátil corriente, **no había forma
de cerrar sesión**. Descubierto porque varios clics "fallaban" y resultó que el botón no
estaba donde el árbol de accesibilidad decía: estaba fuera de la ventana.

El header se rehízo para adaptarse **encogiendo, no recortando**: cada grupo puede
reducirse, los textos largos se truncan de forma fluida, y lo único que nunca se encoge son
los controles accionables. El correo completo y los roles quedan en el `title` del bloque de
identidad. En pantallas muy estrechas se ocultan los elementos que no informan al truncarse
—el rótulo de marca, el correo, el avatar y el selector de región, que está deshabilitado—
y el botón conserva su icono con etiqueta accesible.

**Verificación.** Barrido de 320, 375, 768, 900, 1024, 1280, 1440 y 1600 px comprobando por
DOM que ningún elemento del header sobresale del borde: sin desbordes en ninguno.
`ng test` → 589 SUCCESS. `python -m pytest` → 1599 passed, 2 skipped.

---

## 2026-08-11 — B5: no existía forma de definir la contraseña definitiva (CU-O04)

Alcance: `backend/apps/cuentas_clientes/services/cambio_password_service.py` (nuevo),
`backend/apps/cuentas_clientes/views/password_reset_views.py`,
`backend/apps/cuentas_clientes/views/urls.py`,
`backend/apps/cuentas_clientes/tests/services/test_cambio_password_service.py` (nuevo),
`frontend/src/app/modules/cuentas-clientes/auth/{pages/password-reset.page.ts,services/password-reset.service.ts}`,
spec `RF-AUT-006b` y contrato `auth-rbac.openapi.yaml`.

**Hallazgo (B5).** Detectado al entrar por primera vez con la cuenta recién aprobada. El
login funcionaba y el sistema forzaba el cambio de contraseña, tal como exige el SRS §3.2.1
—"obliga a definir una contraseña definitiva antes de permitir cualquier otra acción"—,
pero la pantalla a la que redirigía era la de **recuperación**, que solo sabe enviar otra
contraseña temporal. El usuario quedaba en un bucle cerrado: pedir temporal → entrar con
temporal → que le pidan pedir otra temporal. Nunca podía activar su cuenta.

**Alcance real del fallo.** Afectaba a **todo** usuario nacido con credencial temporal: los
tres caminos de alta de cliente (conversión desde el embudo, entrada directa y
autorregistro), el reenvío de invitación, la recuperación de contraseña olvidada y cada
unidad de emergencia dada de alta con correo. Es decir, ninguna cuenta creada por el sistema
podía llegar a usarse; solo funcionaban las cuentas sembradas por script.

**Por qué estaba así.** El paso estaba especificado —`FR-UI-007` dice "pantalla
`password-reset` para solicitud (correo) **y cambio de contraseña definitiva**", y el
catálogo lo recoge como CU-O04— pero nunca se implementó: no había endpoint en el contrato,
la pantalla solo traía la mitad del flujo, y `CredentialRepository.activate_credential()`
existía sin que nadie la llamara. La etapa `cambio_password` del asistente de incorporación
tampoco cambia la contraseña: solo marca la etapa como completada.

**Cambio.** Nuevo `POST /api/v1/auth/password-change`, autenticado, que exige la contraseña
vigente además de la nueva —sin eso, un token robado bastaría para apropiarse de la cuenta—,
rechaza menos de 8 caracteres y rechaza repetir la vigente, y deja `estadocredencial` en
`Activo`. La pantalla muestra ahora el formulario de contraseña nueva cuando el cambio es
forzado, y al terminar cierra la sesión abierta con la temporal para que el usuario entre
con la definitiva. Se documentó como `RF-AUT-006b` en el spec y se añadió al contrato.

**Verificación.** `python -m pytest` → 1603 passed, 2 skipped (4 nuevas de CU-O04).
`ng test` → 589 SUCCESS. En el navegador, recorrido completo: entrar con la temporal →
la pantalla pide la definitiva → guardar → `Dim_Credencial` queda en `Activo` → volver a
entrar con la definitiva ya no fuerza ningún cambio.

---

## 2026-08-11 — B6: la incorporación guiada no era alcanzable

Alcance: `backend/apps/cuentas_clientes/services/auth_service.py`,
`frontend/src/app/modules/cuentas-clientes/auth/{services,guards,pages}`,
spec `FR-UI-007` y `FR-UI-022`, contrato `auth-rbac.openapi.yaml` (`LoginData.cuenta`).

**Hallazgo (B6).** Con la cuenta ya aprobada y la contraseña definitiva puesta, el cliente
aterrizaba en "Mis tickets". El asistente de incorporación —que existe, funciona y muestra
las tres etapas del SRS §3.2.2— **solo se alcanzaba escribiendo la URL**: no había entrada
en el menú del cliente ni redirección tras el login. En la práctica la incorporación no
llegaba a ocurrir nunca, y con ella se quedaban sin hacer el perfil corporativo y las
preferencias operativas de las que dependen los avisos y los informes del cliente.

**Cambio.** El login devuelve ahora `cuenta` con `idcliente`, `estadoOnboarding` y
`onboardingPendiente`, resuelto con `ClienteRepository.find_by_admin_local`. Es `null` para
los usuarios internos de TSI. Con ese dato, tanto el login como la resolución de la raíz `/`
llevan al asistente por delante del home del rol: hasta completar la incorporación la cuenta
no está lista para operar. Un `returnUrl` explícito conserva prioridad, para no romper los
enlaces profundos.

**Nota sobre el contrato.** Es una ampliación aditiva de `LoginData`; los clientes que no
lean el campo no se ven afectados.

**Verificación.** `python -m pytest` → 1603 passed, 2 skipped. `ng test` → 594 SUCCESS
(5 nuevas). En el navegador: Teresa Beltrán inicia sesión y aterriza directamente en la
configuración inicial de su cuenta, en la etapa "Cambio de contraseña".

**Higiene de datos del entorno.** Las cuentas 920002 y 920003 compartían `admin_local_id`
porque, mientras B3/B4 estaban vivos, Pinot descartaba las escrituras y `_next_id()`
reutilizó el mismo identificador. Con dos cuentas para el mismo administrador local,
`find_by_admin_local` (LIMIT 1) resolvía de forma arbitraria. La cuenta huérfana se marcó
como `Rechazado_Anulado` —el estado de anulación del propio producto, que esa consulta ya
excluye— en vez de borrarla (R-01 del SRS). No es un defecto del sistema: es residuo de los
fallos ya corregidos.

---

## 2026-08-11 — B7: las preferencias operativas capturaban 2 de las 4 dimensiones del SRS

Alcance: `frontend/src/app/modules/cuentas-clientes/shared/preferencias-operativas-form.component.ts`
(nuevo, con sus pruebas), `.../incorporacion-clientes/pages/onboarding-wizard/`,
`.../gestion-cuenta/pages/preferencias/`, spec `FR-UI-013` y `FR-UI-014`.

**Hallazgo (B7).** Detectado al completar la incorporación guiada de una cuenta nueva. El
SRS §3.2.2 y §3.2.3 enumeran cuatro preferencias operativas —umbrales de alerta, canales de
notificación, zonas geográficas de interés y destinatarios de reportes— y la UI solo pedía
el canal y el teléfono. La pantalla de Gestión de Cuenta pedía todavía menos, y el canal
como campo de texto libre en vez de un selector. `Dim_Preferencias_Cliente` y el endpoint
ya soportaban las cuatro: era la interfaz la que nunca las preguntaba.

**Efecto verificado.** Tras completar la incorporación, la fila quedaba con
`umbrales_alerta {}`, `zonas_geograficas []` y `destinatarios_reportes ''`, sin forma de
corregirlo desde ninguna pantalla. `zonas_geograficas` no es un dato decorativo: decide qué
expedientes puede consultar el cliente (§3.6.4) y qué puede leer un partner consumidor de
datos —`ConsumoDatosService.zonas_contratadas()` es **fail-closed**, así que vacío significa
cero resultados, y el partner lo interpreta como "no hubo accidentes"—.

**Decisión de negocio (usuario, 2026-08-11).** El "umbral de alerta" es el **tiempo máximo
de llegada de la unidad**: el cliente fija unos minutos y se le avisa si un caso suyo los
supera. Se guarda como `{"tiempo_llegada_max_min": N}`.

**Cambio.** Un único componente `app-preferencias-operativas-form` con las cuatro
dimensiones, compartido por la incorporación y la gestión de cuenta —antes cada pantalla
capturaba un subconjunto distinto—. Las zonas se eligen con un selector encadenado país →
estado → condado alimentado del catálogo geográfico y se muestran como etiquetas con su
nombre; en ningún momento se escribe ni se enseña un identificador. El canal pasó de texto
libre a selector, y el teléfono solo se pide cuando el canal lo necesita.

**De paso.** La etapa de perfil corporativo llegaba vacía y obligaba a reescribir la razón
social y el nombre comercial que la cuenta ya había declarado, contra el principio del SRS
de heredar lo capturado "sin volver a digitarlos". Ahora se precarga. Y el encabezado de
preferencias muestra la razón social en lugar de `Cliente #920003`.

**Verificación.** `ng test` → 599 SUCCESS (5 nuevas sobre la serialización, incluidos los
centinelas `'null'` de Pinot). En el navegador, sobre la cuenta Rescate Vial Andino:
umbral 25 min, canal "ambos", zonas Cuauhtemoc y Benito Juarez, dos destinatarios. En base:
`umbrales_alerta {"tiempo_llegada_max_min":25}`, `zonas_geograficas [1,2]`,
`destinatarios_reportes` con ambos correos.

---

## 2026-08-11 — B8/B9: la pertenencia a la organización no se comprobaba en ningún sitio

Alcance: `backend/core/repositories/cuentas_clientes/cuenta_usuario_repository.py`,
`backend/apps/cuentas_clientes/services/{transferencia_propiedad_service.py,auth_service.py}`,
sus pruebas, y las pantallas de gestión de cuenta del frontend.

Ambos hallazgos salieron de la misma raíz: la pertenencia de un usuario a una organización
cliente vive en `Dim_Usuario_Cliente` —que Seguimiento y Soporte ya consultan para resolver
a qué cuenta pertenece alguien—, pero Cuentas y Clientes la deducía del `admin_local_id`.
Con ese criterio una organización tiene como mucho una persona, cuando el plan contratado
limita precisamente el «número máximo de usuarios» de la organización.

**B8 — Se podía transferir la cuenta a alguien de otra empresa.** El SRS §3.2.3 exige
designar a otro responsable «de su misma organización». `_cliente_role_users()` listaba a
**todo usuario activo con rol Cliente del sistema entero**, y el guardián de la operación,
`_is_eligible_transfer_target()`, solo comprobaba que estuviera activo y tuviera ese rol.
La comprobación de pertenencia no existía, pese a que el mensaje de error ya decía «Usuario
no pertenece a la cuenta». Verificado en el navegador: la lista de candidatos para
**Rescate Vial Andino** ofrecía a la responsable de **Empresa Demo Torres**.

Se añadieron `list_miembros`, `es_miembro` y `list_cuentas_del_usuario` al repositorio,
leyendo `Dim_Usuario_Cliente` e incluyendo al administrador local aunque le falte la fila de
vínculo. La lista de candidatos y el guardián usan ahora la pertenencia real. Tras el
arreglo, la lista solo ofrece a los miembros de la propia cuenta y el endpoint responde
`404 "Usuario no pertenece a la cuenta"` ante un intento entre organizaciones.

**Deliberadamente fuera de alcance:** `user_belongs_to_cliente`, que gobierna **quién entra**
a las pantallas de la cuenta, se dejó como estaba. Ampliarlo dejaría entrar a más gente y eso
es una decisión de permisos, no una corrección.

**B9 — Se podía iniciar sesión con la organización dada de baja.** El SRS §3.2.1 es
explícito: el login falla si la persona fue desactivada **y si la organización a la que
pertenece fue dada de baja**, y llama a ambas validaciones obligatorias. La segunda no
existía. La baja marcaba la cuenta como `Dado de baja` y expulsaba las sesiones abiertas,
pero nada impedía abrir una nueva: el personal de un cliente cuyo contrato terminó seguía
entrando y operando con normalidad.

El login comprueba ahora las cuentas del usuario y lo rechaza si todas están dadas de baja.
Quien no pertenece a ninguna cuenta cliente —el personal interno de TSI— no se ve afectado.

**Verificación.** `python -m pytest` → 1607 passed, 2 skipped (4 nuevas). `ng test` → 599
SUCCESS. Contra el sistema en marcha, tras dar de baja la cuenta E2E: el usuario de esa
organización pasó de **200 a 401**, un cliente con cuenta activa sigue en 200 y el
Administrador interno también.

**De paso.** Se retiraron los identificadores crudos de las pantallas de perfil,
transferencia, baja e incorporación, que ahora nombran la cuenta por su razón social
(§8 del `design-system.md`).

**Comprobado y correcto, sin cambios.** La baja es lógica: la fila del cliente conserva su
razón social y su historial de incorporación, y las sesiones quedan en `Expulsado`, no
borradas. El cliente no puede abrir la pantalla de baja —es del Administrador (SRS §3.2.3)—
y el control de acceso lo impide correctamente.
