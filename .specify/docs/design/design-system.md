# Sistema de Diseño (UX/UI) — TSI
**Ubicación de este archivo:** `docs/diseno/design-system.md`
**Última actualización:** 2026-07-12 (v5 — corrección de IDs de caso de uso en ejemplos de Toast/Snackbar/Alert para alinear con la numeración vigente de los specs de Emergencias: CU-O39 abortar misión, CU-O32 descartar caso, CU-O41 fusionar reportes, CU-O44 forzar cierre, CU-O42 cancelar con unidad despachada; "sin unidades disponibles" ya no es un CU independiente, es una alerta dentro de CU-O34)

---

## 1. Filosofía

La interfaz de TSI debe comunicar **confianza, velocidad y precisión**, como un centro de control de tráfico aéreo o sala de monitoreo. Profesionalismo institucional, con carácter propio (no plantilla genérica ni "hecho por IA"). La información crítica debe ser legible en fracciones de segundo. Microinteracciones suaves y jerarquía visual robusta.

**Lenguaje visual global:** el sistema usa esquinas redondeadas de forma consistente en todos los componentes — botones, inputs, cards, tablas, modales, badges, tooltips, tabs y navegación — pero con una redondez **sutil y contenida** (radios en el rango 6-12px según el componente, nunca por debajo de este mínimo ni acercándose a formas muy suaves tipo app de consumo). El objetivo es evitar dos extremos: la dureza visual de esquinas a 0-2px (que se lee fría y genérica) y la suavidad excesiva de radios grandes (que se lee informal, poco apta para un centro de control de emergencias). La redondez debe sentirse como un detalle de coherencia del sistema, no como una decisión estética protagonista. La tipografía y el espaciado deben leerse como parte de ese mismo sistema coherente en cada pantalla, no como decisiones aisladas.

El diseño se apoya en 5 principios de psicología de diseño, que deben poder rastrearse en cualquier pantalla nueva que se construya (ver sección 2).

## 2. Principios de UX aplicados

Toda pantalla o componente nuevo debe poder justificarse con al menos uno de estos principios. Se recomienda anotarlo en el PR/spec del componente.

| Principio | Qué exige | Aplicación en TSI |
|---|---|---|
| **Ley de Hick** | Menos opciones visibles a la vez = decisión más rápida | En pantallas de despacho/emergencia, máximo 3-4 acciones primarias visibles; el resto va en un menú secundario ("Más acciones") |
| **Principios de Gestalt** (proximidad, similitud) | Agrupar visualmente lo que está relacionado | KPIs relacionados en la misma card; separación de 24px+ entre grupos no relacionados; mismo estilo visual = misma categoría de dato |
| **Ley de Fitts** | Objetivos frecuentes/críticos deben ser grandes y estar cerca del punto de acción | Botón "Abortar/Confirmar" en despacho: mínimo 44x44px, ubicado donde el ojo ya está mirando, nunca en una esquina lejana |
| **Ley de Jakob** | La gente espera que tu app funcione como las apps que ya conoce | Campana de notificaciones arriba-derecha, Toast inferior-derecha, Snackbar inferior-izquierda, sidebar a la izquierda, búsqueda arriba-centro/derecha — no reinventar patrones de navegación |
| **Carga cognitiva** | No mostrar todo a la vez | Progressive disclosure: detalles secundarios en modales/expandibles, no todos en la vista principal. Máximo 6-8 bloques de información simultáneos por vista |
| **Resiliencia de captura en campo** | Ningún dato ingresado por el usuario debe perderse por una interrupción de red | Todo formulario que capture datos en campo (evidencia, notas, ubicación) debe degradar con gracia ante pérdida de conexión: conservar lo ya escrito/adjuntado y reintentar o informar claramente el estado, nunca descartar silenciosamente. El detalle de implementación (qué se guarda, cuándo reintenta, qué ve el usuario) se define en el spec de cada caso de uso |

**Regla de validación rápida:** antes de dar por cerrado un diseño, revisar qué principio de esta tabla se está aplicando en cada decisión de layout. Si no hay respuesta, probablemente sea decoración sin propósito.

## 3. Paleta de colores

Paleta migrada de la base negro/rojo a un sistema **dual claro/oscuro** con acento azul eléctrico, decidido tras evaluar 3 direcciones (azul, violeta, teal) — se eligió azul por transmitir monitoreo/tecnología sin ninguna cercanía a los colores semánticos de alerta (rojo/naranja/ámbar/verde), evitando así cualquier ambigüedad bajo estrés.

**Tokens base — estructura**

| Token | Modo oscuro | Modo claro | Uso |
|---|---|---|---|
| `bg-page` | `#14161F` | `#F5F7FB` | Fondo general de la aplicación |
| `bg-surface` | `#1C1F2B` | `#FFFFFF` | Fondo de cards, formularios, contenedores |
| `border-default` | `#2A2D3A` | `#E1E5EE` | Líneas divisorias, bordes de input, separadores |
| `text-primary` | `#E8E9EF` | `#1A1D29` | Texto principal, títulos |
| `text-secondary` | `#8A8DA0` | `#5A5E70` | Texto secundario, placeholders, labels |
| `accent-primary` | `#2E6FF2` | `#2E6FF2` | Header, botones primarios, navegación activa, marca (se mantiene igual en ambos modos — validado con contraste suficiente sobre ambos fondos) |
| `accent-hover` | `#245BC7` | `#245BC7` | Estado hover de elementos con `accent-primary` |

**Tokens semánticos — alertas y estados**

| Rol | Fondo oscuro | Texto/ícono oscuro | Fondo claro | Texto/ícono claro |
|---|---|---|---|---|
| Crítico (Nivel 1) | `#4A1B0C` | `#F09595` | `#FCEBEB` | `#A32D2D` |
| Alta (Nivel 2) | `#412402` | `#FAC775` | `#FAEEDA` | `#854F0B` |
| Media / advertencia (Nivel 3) | `#3B2E05` | `#F0D889` | `#FEF9E7` | `#92730A` |
| Éxito / seguro | `#173404` | `#97C459` | `#EAF3DE` | `#3B6D11` |
| Información | `#1C2430` | `#9DB1CC` | `#EEF2F8` | `#3D4E68` |

**Punto de color crudo (referencia, no usar directamente en componentes):** los estados usan la misma familia de matiz en ambos modos (rojo, naranja, ámbar, verde) — lo que cambia es la posición en la rampa: fondo oscuro-saturado + texto claro en modo oscuro, fondo claro-pastel + texto oscuro-saturado en modo claro. Ningún componente debe usar hex "a mano"; siempre referenciar el token semántico (ej. `alerta-critica-bg`, `alerta-critica-texto`) para que el cambio de tema sea automático.

**Regla de uso:** `bg-page`/`bg-surface` dominan como base estructural (~55-60% de la interfaz). `accent-primary` se usa con intención en botones primarios, navegación activa y marca — nunca como color de alerta, precisamente para eliminar cualquier ambigüedad entre "acción de marca" y "estado crítico" (a diferencia de la paleta anterior negro/rojo, donde ambos compartían el mismo hex). Naranja para despacho urgente, ámbar para advertencias, verde para éxito. Nunca usar colores pastel o saturados sin propósito fuera de los tokens ya definidos.

**Por qué el acento ya no comparte hex con las alertas:** en la paleta anterior, el rojo de marca y el rojo crítico usaban el mismo valor, diferenciados solo por contexto (fondo+borde+ícono). Con azul como acento, esa ambigüedad desaparece estructuralmente: ningún estado de alerta usa tonos azules, así que no hace falta ningún contexto adicional para diferenciarlos — es una mejora de legibilidad bajo estrés, no solo estética.

**Sobre el azul de "obligación" (ISO 3864):** dado que ahora el acento primario del sistema **es** azul (por identidad de marca/monitoreo, no por severidad), se descarta definitivamente reservar un azul adicional para "obligación" según la norma — generaría confusión entre "esto es una acción de marca" y "esto es obligatorio" usando el mismo matiz. Toda acción obligatoria del usuario sigue comunicándose mediante el nivel de severidad ya cubierto por la paleta de alertas (ej. aceptar una asignación es urgente/alto, no neutro).

**Tema oscuro/claro — alcance:** ambos temas son completos e intercambiables por el usuario (no solo un sidebar oscuro sobre contenido claro como en la versión anterior). Justificación: operadores en salas de control suelen trabajar en penumbra o en turnos nocturnos, y no se conoce de antemano la edad ni sensibilidad visual de cada usuario — ofrecer ambos como opción real cubre ambos casos sin forzar una decisión única para todos los roles (operador, unidad de emergencia, técnico de campo).

El mapa (Leaflet) también sigue esta regla: tiles claros de OpenStreetMap en modo claro, tiles oscuros de CartoDB Dark Matter en modo oscuro, cambiando en vivo junto con el resto de la interfaz.

## 4. Tipografía

La tipografía debe reforzar la misma sensación de suavidad del sistema: pesos no demasiado rígidos, buen interlineado (line-height 1.4-1.6 en cuerpo de texto), y letras que respiren dentro de sus contenedores redondeados — nunca texto pegado al borde de una card o botón.

| Elemento | Especificación |
|---|---|
| Fuente principal | **Inter** (variable), pesos 400, 500, 600, 700 |
| H1 (títulos de página) | 28px, peso 700, color `text-primary` |
| H2 (encabezados de sección) | 20px, peso 600, color `text-primary` |
| H3 (subencabezados) | 16px, peso 600, color `text-primary` |
| Cuerpo principal | 14px, peso 400, color `text-primary`, line-height 1.5 |
| Cuerpo secundario | 14px, peso 400, color `text-secondary`, line-height 1.5 |
| KPIs y labels | 12px, peso 500, mayúsculas, letter-spacing 0.5px, color `text-secondary` |
| Monoespaciada | **JetBrains Mono** 13px solo para códigos, IDs de API y coordenadas |

## 5. Componentes globales

**Radios de esquina (regla global, aplica a TODA la app):**
- Botones e inputs: 6-8px
- Cards, modales, contenedores medianos: 8-10px
- Avatares: full-round (999px) — se mantiene porque es un patrón universal (Ley de Jakob) y no afecta la percepción de seriedad institucional
- Badges y chips de estado: 6-8px (no full-round) — un chip de estado ("Confirmado", "En_sitio") es información operativa, no un elemento decorativo, y debe leerse con la misma sobriedad que el resto del sistema
- Tablas: esquinas del contenedor general en 8px (las celdas internas quedan rectas por legibilidad de datos, pero el marco exterior sigue la regla)
- Nunca usar 0-2px en ningún componente de la interfaz — esto es lo que se busca evitar deliberadamente ("muy cuadrado")

**Header:** Fondo `bg-surface`, altura 64px, borde inferior `border-default`. Logo a la izquierda. A la derecha: saludo/contexto de usuario, avatar circular con iniciales (fondo `accent-primary`), notificaciones (campana con contador en color de alerta correspondiente), selector de región. Barra de búsqueda global centrada con input redondeado (Ley de Jakob: patrón esperado).

**Navegación lateral (sidebar):** Fondo `bg-surface`, ancho 240px, borde derecho `border-default`. Items con ícono 24x24px, contenedor de item con radio 8-10px al hacer hover/activo (no un rectángulo pegado al borde). Item activo: fondo con opacidad baja de `accent-primary` (ej. `rgba(46,111,242,0.1)`), borde izquierdo 4px `accent-primary`, texto `accent-primary` en bold. Agrupaciones por Gestalt dentro de cada sidebar, separadas por 24px mínimo.

**Regla de sidebar por rol:** cada rol del sistema (operador, unidad de emergencia, técnico de campo) tiene su **propio sidebar**, compuesto únicamente por los módulos a los que ese rol tiene acceso — nunca un sidebar único con ítems ocultos u ocultos/deshabilitados por permisos. Esto reduce carga cognitiva (Ley de Hick) y evita que un usuario descubra la existencia de módulos fuera de su alcance. El listado concreto de qué módulos ve cada rol se define en `module-map.md`; este documento solo fija el patrón visual y estructural del sidebar, no su contenido.

**Regla de sidebar con múltiples roles (multi-rol):** un usuario puede tener más de un rol asignado (`Dim_Usuario_Rol`, ver `architectural-patterns.md` sección 3). Cómo se refleja eso en el sidebar depende de si los roles pertenecen al mismo departamento o a departamentos distintos (agrupación de referencia: `actors.md`, sección "Actores por Departamento"):

- **Mismo departamento** (ej. Director de Operaciones + Operador de Emergencias, ambos en Gestión de Emergencias): los módulos de ambos roles se **fusionan en un solo sidebar**, sin selector adicional — es una ampliación natural de opciones dentro del mismo contexto de trabajo (Ley de Hick: no se duplica la navegación por algo que el usuario percibe como "seguir en lo mismo, con más permisos").
- **Departamentos distintos** (ej. Director de Operaciones en Emergencias + Gerente de Ventas en Ventas y CRM): el sidebar **no se fusiona**. En su lugar, el header muestra un selector explícito de rol/departamento (junto al avatar de usuario, mismo patrón de ubicación que el selector de región ya definido en "Header"), y el sidebar se reemplaza por completo al cambiar de selección — cada contexto de trabajo mantiene su propio sidebar íntegro, sin mezclar KPIs ni módulos de departamentos que no comparten propósito.

**Layout general de la aplicación (aplica a cualquier pantalla, no solo dashboards):**
- Grid principal: sidebar fija + área de contenido con cards de esquinas redondeadas (12-16px)
- Bloques de KPIs con indicadores circulares de progreso (ring charts) donde tenga sentido mostrar métricas — máximo 3-4 rings visibles a la vez (Ley de Hick + carga cognitiva)
- Listados de eventos/actividad agrupados por proximidad temporal, en cards individuales redondeadas, no en tablas densas cuando el contenido es narrativo
- Máximo 6-8 bloques de información simultáneos por vista, en cualquier módulo del sistema (despacho, analítica, administración, etc.)

**Botones:** Primario `accent-primary` texto blanco, hover `accent-hover`, radio 8-10px. Secundario borde `accent-primary` texto `accent-primary` sobre fondo transparente/claro. Crítico destructivo: color de alerta crítica (texto/ícono del token `alerta-critica`) con ícono de advertencia explícito + confirmación en 2 pasos (nunca solo el color para distinguirlo de un botón primario normal — y ahora, al no compartir hex con el acento de marca, la distinción es aún más clara). Advertencia: color de alerta media, texto sobre ese fondo. Deshabilitado opacidad 0.5. Padding 10px 20px. Área mínima de toque 44x44px (Ley de Fitts) en acciones críticas.

**Estado "en carga" (acciones críticas — ej. Asignar unidad, Confirmar despacho):** al activarse la acción, el botón se deshabilita para evitar doble-submit, el texto cambia a su forma en gerundio (ej. "Asignar unidad" → "Asignando…"), y se agrega un spinner de 16px a la izquierda del texto, dentro del propio botón — nunca un spinner flotante aparte. El fondo mantiene `accent-primary` con opacidad ~0.8 (distinta del disabled real en 0.5, para diferenciar "procesando" de "no disponible"). Si no hay respuesta del backend en 10-15s, el botón vuelve a su estado normal y dispara el feedback de error correspondiente (Toast o Alert según gravedad) — nunca queda cargando indefinidamente.

**Formularios:** Inputs borde `border-default`, radio 8-10px, padding 10px 14px, fondo `bg-surface`. Foco borde `accent-primary` + sombra `0 0 0 3px rgba(46,111,242,0.15)`. Labels `text-secondary`, 14px, peso 500.

**Validación semántica en formularios:**
- **Error:** borde y texto de ayuda en color de alerta crítica, ícono de error. Campo obligatorio faltante o dato inválido.
- **Advertencia:** borde y texto de ayuda en color de alerta media/ámbar. Posible conflicto (ej. unidad asignada a más de 15 minutos).
- **Válido:** borde y texto en color de éxito, ícono de verificación. Confirmación opcional de campo correcto.

**Toasts / Notificaciones (feedback al usuario):**

**Definición (importante, no confundir con Snackbar ni Alert — ver comparación abajo):** un Toast es una confirmación **pasiva y no intrusiva** de que una acción se completó. No requiere ninguna acción del usuario, no interrumpe su flujo de trabajo, y siempre se desvanece solo tras un tiempo determinado — incluso el tipo Crítico. El usuario puede opcionalmente cerrarlo antes con una X pequeña si lo desea, pero esta X es un atajo de conveniencia, no una condición obligatoria: el toast desaparece igual sin que nadie lo toque. Un Toast **nunca** lleva botón de acción (ni "Deshacer" ni nada similar) — si la acción es reversible, corresponde a un Snackbar. Si un evento requiere que el operador reconozca o actúe obligatoriamente (ej. "sin unidades disponibles en zona", alerta dentro de CU-O34), ese evento no es un Toast — corresponde a un Alert.

Todos los toasts comparten: esquinas redondeadas 8px (consistente con la regla general de la sección 5), sombra suave (nunca fuerte), borde izquierdo 4px de color semántico, ícono correspondiente, X de cierre opcional en la esquina superior derecha del toast (ícono pequeño, sutil, `text-secondary`), auto-dismiss siempre activo.

**Posición y comportamiento:** esquina **inferior derecha** de la pantalla, apilados de abajo hacia arriba cuando hay más de uno (el más reciente aparece abajo, empujando a los anteriores hacia arriba). Animación de entrada suave (slide + fade desde la derecha). Esta posición se elige deliberadamente distinta a la de la campana de notificaciones del header (arriba-derecha, ver sección "Header"): separa lo persistente/revisable a demanda (campana) de lo efímero/pasivo (toast), siguiendo el mismo patrón que usan sistemas operativos y apps de escritorio (Ley de Jakob).

| Tipo | Token de fondo/borde | Auto-dismiss | Cuándo usarlo |
|---|---|---|---|
| Crítico | `alerta-critica` | 6-8s | Confirmación de error grave o acción destructiva ya ejecutada (no para errores que requieran acción del usuario — eso es un Alert) |
| Urgente / Alta | `alerta-alta` | 5-6s | Despacho urgente confirmado, notificación resuelta |
| Advertencia / Media | `alerta-media` | 4-6s | Conflicto posible ya registrado, advertencia no bloqueante |
| Éxito | `exito` | 4-6s | Caso cerrado, guardado exitoso, confirmación |
| Informativo | `informacion` | 4-6s | Mensajes neutros, actualizaciones de estado sin urgencia |

Cada token resuelve automáticamente a los valores de fondo/texto definidos en la sección 3 según el tema activo (claro u oscuro) — nunca hardcodear el hex del modo actual en el componente.

**Responsividad:** en Mobile (<640px), el toast ocupa el ancho disponible con márgenes laterales de 16px (no flotante de ancho fijo como en desktop), manteniendo la misma esquina inferior. En Tablet/Desktop conserva un ancho fijo (~360-400px).

---

**Snackbar (informa + acción inmediata reversible):**

**Definición:** un Snackbar informa que una acción se completó **y** ofrece una vía de escape inmediata (ej. "Deshacer") para acciones rápidas que el operador podría haber ejecutado por error. A diferencia del Toast, demanda un poco más de atención y sí es interactivo: incluye un botón de acción de texto, y puede descartarse manualmente (deslizando en mobile, con X en desktop). Si no se toca, desaparece solo tras unos segundos igual que un Toast — la diferencia no es la persistencia, es que ofrece una acción contextual.

**Cuándo usarlo en TSI:** acciones rápidas y reversibles en el momento inmediato:
- CU-O39 (Abortar misión en tránsito) → "Despacho abortado. [Deshacer]"
- CU-O32 (Descartar caso antes de despacho) → "Caso descartado. [Deshacer]"
- CU-O41 (Fusionar reportes duplicados) → "Reportes fusionados. [Deshacer]"

**Estilo:** fondo `text-primary` invertido respecto al tema activo (siempre el extremo más oscuro de la escala neutra, independiente del tema, para diferenciarse visualmente de los Toasts que usan fondos claros semánticos — el Snackbar no comunica severidad, comunica una acción de sistema), texto siempre claro sobre ese fondo, botón de acción en `accent-primary` (sin fondo, tipo link, alineado a la derecha del texto). Esquinas 8px. Sombra suave. Auto-dismiss 5-7s (más tiempo que un Toast promedio, porque el usuario necesita margen para decidir si deshace o no) si no hay interacción.

**Posición:** esquina **inferior izquierda** en Desktop/Tablet — deliberadamente opuesta al Toast (derecha) para que ambos puedan convivir en pantalla sin superponerse ni confundirse. En Mobile: ancho completo, anclado abajo, por encima de cualquier navegación inferior fija.

**Responsividad:** igual patrón que el Toast — ancho fijo (~360-420px, algo más ancho que el toast por el botón de acción) en Tablet/Desktop, ancho completo con márgenes de 16px en Mobile.

---

**Alert (bloqueante, requiere reconocimiento obligatorio):**

**Definición:** un Alert comunica información crítica que el usuario **debe** atender antes de continuar. Es disruptivo por diseño — bloquea parcial o totalmente la interacción hasta que se resuelve, y no desaparece por sí solo. Requiere una acción explícita del usuario (botón "Aceptar", "Confirmar", "Cancelar", etc.).

**Cuándo usarlo en TSI:**
- Sin unidades disponibles en zona ni zonas vecinas (alerta dentro de CU-O34, Escalar caso a zona) — el operador debe decidir el siguiente paso, no puede perderse en un fade de segundos.
- Fallo real de conexión/guardado al registrar un accidente (RF-REG-001).
- Confirmación antes de una acción irreversible real: forzar cierre de caso desde central (CU-O44), cancelar caso con unidad ya despachada (CU-O42).
- Advertencia de sesión por expirar u otras interrupciones que de verdad necesitan decisión inmediata.

**Dos formatos, según el nivel de bloqueo necesario:**
1. **Modal de Alert** (bloqueo total) — overlay oscuro semitransparente sobre toda la pantalla, diálogo centrado con esquinas 10-12px, fondo `bg-surface`, título (H3, `text-primary`), mensaje descriptivo (14px, `text-secondary`), y 1-2 botones de acción siguiendo el estilo de botones ya definido (primario `accent-primary`, secundario con borde). Para acciones destructivas: el botón de confirmación destructiva debe ser el secundario visualmente débil y el de cancelar/volver el más prominente, o bien requerir un paso adicional de confirmación explícita (ya definido en la sección de Botones: "confirmación en 2 pasos").
2. **Banner de Alert** (bloqueo parcial, sección específica) — franja horizontal anclada arriba de una sección o vista (no de toda la pantalla), fondo semántico igual que Toast/Snackbar (token `alerta-critica` para crítico), pero con botón de acción visible y sin auto-dismiss. Útil para CU-O44: el operador sigue viendo el resto del panel de despacho, pero el banner permanece hasta que resuelve la situación.

**Colores semánticos (reutilizan los mismos tokens que Toast, para coherencia del sistema):** Crítico → token `alerta-critica`, Advertencia → token `alerta-media`, Informativo → token `informacion`. Cada uno resuelve automáticamente a los valores de la sección 3 según el tema activo.

**Posición:** modal centrado (pantalla completa con overlay) o banner superior de la sección afectada — nunca en esquinas flotantes, ya que su naturaleza es interrumpir, no convivir con otros elementos.

**Responsividad:** el modal en Mobile ocupa el ancho completo con márgenes de 16px y se centra verticalmente; los botones de acción pasan a apilarse verticalmente (ancho completo) en vez de en línea, para asegurar el área mínima de toque de 44x44px. El banner mantiene ancho completo en todos los breakpoints.

---

**Tabla comparativa — cuándo usar cada componente de feedback:**

| | Toast | Snackbar | Alert |
|---|---|---|---|
| Interacción | Ninguna | Opcional (botón de acción) | Obligatoria |
| Se cierra solo | Sí, siempre | Sí, si no se interactúa | No |
| Bloquea la interfaz | No | No | Sí (parcial o total) |
| Posición | Inferior derecha | Inferior izquierda | Centro (modal) o banner de sección |
| Ejemplo en TSI | "Caso cerrado" | "Despacho abortado. [Deshacer]" | "Sin unidades disponibles en zona" |

**Tablas operativas:** para datos tabulares por naturaleza (historial de despachos, listado de unidades disponibles, expedientes — CU-O23, CU-O43, etc.), no para listados narrativos de actividad (esos siguen en cards, ver sección de Layout).

- Densidad media: padding de celda 12px vertical / 16px horizontal — balance entre ver varias filas de un vistazo y no perder legibilidad.
- Encabezado de tabla: fondo `bg-surface` (modo claro) / superficie elevada (modo oscuro), texto `text-primary`, 12px, peso 500, mayúsculas (mismo tratamiento que labels de KPI para coherencia tipográfica).
- Filas: fondo `bg-page`/`bg-surface` alternado cada fila para lectura horizontal — zebra striping sutil, opcional), nunca coloreadas completas según severidad/estado — el estado se comunica únicamente mediante un badge/chip dentro de su celda correspondiente (radio 6-8px, ver sección 5), nunca tiñendo la fila entera. Esto evita ruido visual en tablas con muchas filas y mantiene el color como refuerzo, no como decoración de fondo.
- Columna de acción: ícono de ojo (ver detalle), no botón de texto — más compacto, no compite con los datos, y es un patrón reconocido (Ley de Jakob) en tablas de dashboards. Debe llevar `aria-label="Ver detalles"` y tooltip al hover para accesibilidad. Área de toque mínima 44x44px aunque el ícono visual sea de ~18-20px (Ley de Fitts).
- Bordes entre filas: `border-default`, 1px, solo horizontal (sin líneas verticales entre columnas, para no sobrecargar).

**Patrón CRUD operativo: Lista → Workpanel**

Patrón estándar para cualquier módulo del sistema que gestione registros con operaciones de creación, consulta, edición y eliminación (casos de accidente, cuentas de cliente, unidades, usuarios, etc.). El formulario de creación/edición **no** se resuelve con un modal: se resuelve con un **workpanel**, es decir, una vista de detalle que vive como contenido de la propia pantalla y no como overlay flotante. La razón es que estos formularios suelen ser extensos y el usuario necesita mantener contexto, poder volver y poder refrescar sin perder lo que estaba viendo — condiciones que un modal no cumple bien.

**1. Lista (punto de entrada del módulo)**

- Botón primario **"Nuevo [registro]"** en la parte superior de la vista, siempre visible (Ley de Fitts: es la acción de creación más frecuente del módulo).
- El identificador del registro se muestra como **texto plano** en `JetBrains Mono` (ver sección 4), **nunca como link**. Abrir un registro es siempre una acción explícita mediante los íconos de acción, nunca un click ambiguo sobre la fila o sobre el ID — esto elimina la duda de "¿si hago click aquí, veo o edito?".
- Columna de acciones con **dos íconos Tabler de propósito distinto y no intercambiable**:

| Ícono (Tabler) | Modo que abre | `aria-label` |
|---|---|---|
| `eye` | Ver — solo consulta | "Ver detalles" |
| `pencil` | Editar — modificación de datos | "Editar [registro]" |

  Ambos con tooltip al hover y área de toque mínima 44x44px aunque el ícono visual sea de ~18-20px (Ley de Fitts). Cuando el registro es de solo lectura para el rol activo, se muestra únicamente `eye` — nunca `pencil` deshabilitado (coherente con la regla de sidebar por rol: no exponer lo que el rol no puede hacer).

**Variante Ver-only / CRUD parcial:** si el Depends-on del módulo no expone PATCH de ficha (o el rol no puede crear/editar), la lista usa **solo** `eye` y el CTA de alta del header se omite o se sustituye por la acción de dominio permitida (ej. «Entrada directa» solo Admin). El workpanel puede vivir como **página dedicada** (no split-view) cuando el spec lo declare — misma tipografía, mismos estados loading/vacío/error e misma tabla `md:table` + cards mobile. Implementación canónica de esos estados: componentes `app-list-loading-skeleton`, `app-list-error-state`, `app-list-empty-state` y constantes en `frontend/src/app/shared/ui/list-states/`.

**Chrome del workpanel página dedicada (golden sample Accidente Detalles):** link «← Volver a la lista» con ícono `arrow-left` (no botón outline a la derecha como único retorno); eyebrow de modo («Detalles» / «Editar…»); `h1` + badge(s) en la misma fila; secciones en cards; en modo **Ver**, datos como `<dl>` con `dt` uppercase + `dd` texto — **nunca** `<input disabled>` para fingir solo lectura. Formularios (Crear/Editar): inputs según sección Formularios; catálogos y personas se eligen por **nombre legible** (combobox / select / typeahead). **Prohibido** pedir al usuario que teclee PKs (`idcondado`, `idcliente`, `idusuario`) o mostrarlos como campos principales de la UI (los IDs viajan solo en el payload).

**2. Workpanel (vista de detalle — un mismo componente para los tres modos)**

- **Desktop / Tablet:** panel amplio de ~640-720px, en layout tipo split-view junto a la lista. El ancho amplio se elige por sobre un panel angosto porque estos formularios tienen muchos campos agrupados por sección; un panel estrecho obligaría a scroll excesivo y rompería la agrupación por proximidad (Gestalt).
- **Mobile (<640px):** el workpanel pasa a **página completa**, mismo criterio que ya aplica el Alert modal en mobile (ancho completo, sin split, sin overlay lateral).

**Modos del workpanel:**

| Modo | Título del panel | Campos de datos | Acción en header |
|---|---|---|---|
| Ver | "Detalles" | Deshabilitados (ver Formularios) | — (sin botón de guardado) |
| Editar | "Editar [registro]" | Editables | "Guardar cambios" |
| Crear | "Nuevo [registro]" | Editables, formulario vacío | "Guardar" |

- El modo **Crear reutiliza el mismo componente** que Editar (no una pantalla aparte): mismo layout, mismas secciones, mismo orden de campos. Esto mantiene la consistencia visual entre registrar y modificar, y evita que el formulario se desincronice entre dos implementaciones distintas.
- En modo Editar y Crear, el foco se ubica automáticamente en el **primer campo editable relevante** al abrir el panel, con scroll a esa sección si no está visible — el usuario no debería tener que buscar dónde empezar a escribir.
- El botón de guardado sigue el **patrón de botón en carga** ya definido en esta sección (deshabilitado para evitar doble-submit, texto en gerundio, spinner de 16px dentro del propio botón).
- **Las acciones de dominio del registro** (ej. Descartar, Escalar, Cerrar caso) se rigen por el **estado y el rol**, no por el modo del panel: pueden estar visibles tanto en Ver como en Editar. El modo únicamente gobierna si los campos de datos son editables y si aparece el botón de guardado — nunca qué acciones de negocio están disponibles.

**3. Retorno a la lista**

Al volver desde el workpanel (desde cualquiera de los tres modos), la fila del último registro abierto se distingue con un **fondo de fila en `accent-primary` muy tenue** (rgba ~0.06-0.08). Se elige deliberadamente el acento de marca y no un color semántico: teñir la fila con un token de severidad haría que "esto fue lo último que abriste" se confunda con "esto es grave" o con el estado del registro, que ya se comunican mediante el badge de su celda. La intensidad debe quedar por encima del zebra striping pero muy por debajo de cualquier badge, para que se lea como una marca de orientación y no como una alerta.

**4. Eliminar**

La eliminación **no usa el workpanel**. El ícono de papelera (`trash`, Tabler) dispara el **Alert modal de confirmación en 2 pasos** ya definido en las secciones de Botones y Alert de este documento. Nunca hay borrado directo desde la fila ni desde dentro del workpanel sin ese paso de confirmación explícita.

**Qué no define este patrón:** el manejo de estado de selección entre navegaciones (cómo se recuerda el último registro visto), el esquema de rutas y sus parámetros, y los campos, validaciones y reglas de negocio de cada tipo de registro. Todo eso se documenta en el spec del caso de uso o del módulo correspondiente; aquí solo se fija el patrón visual y de interacción, reutilizable en cualquier módulo con CRUD.

**Espaciado y grid:** sistema de 8px (8, 16, 24, 32, 48, 64). Grid de 12 columnas, gutter 24px. Ancho máximo 1440px.

**Iconografía semántica de severidad:** cada nivel de severidad tiene una forma/ícono fijo, no solo un color, para que el estado sea distinguible sin depender del color (accesibilidad para daltonismo, y legibilidad en condiciones de campo con mala luz). Set de íconos oficial del sistema: **Tabler Icons** — se elige por su cobertura amplia de casos específicos de TSI (mapas, dispatch/radio, cámara para evidencia) y por su geometría ligeramente angular que combina bien con la regla de radios sutiles (6-12px) del sistema, sin caer en formas ni muy orgánicas ni muy planas.

| Severidad | Ícono (Tabler) | Lógica de forma |
|---|---|---|
| Crítico | `alert-octagon` | Octágono — mismo lenguaje visual que una señal de PARE, refuerza gravedad máxima |
| Alta | `alert-triangle` (contorno) | Triángulo de advertencia estándar |
| Media | `alert-circle` | Círculo — forma más neutra que el triángulo |
| Éxito | `circle-check` | Check dentro de círculo, patrón universal de "completado" |
| Información | `info-circle` (peso liviano) | Mismo círculo que Media, pero en el peso más fino de la familia para diferenciarlo sutilmente |

La forma debe mantenerse consistente en todos los componentes donde aparece severidad (badges, toasts, alerts, pines de mapa) — el usuario aprende el lenguaje visual una sola vez y lo reconoce en cualquier contexto del sistema.

**Estados de carga, vacío y error:** todo componente que dependa de datos asíncronos (tablas, listas, cards de KPI) debe contemplar sus 3 estados no felices, no solo el estado con datos:

- **Loading:** *skeleton screens* — bloques con la silueta exacta del contenido real (filas de tabla, cards) en tono ligeramente distinto a `bg-surface` según el tema activo, con una animación sutil de opacidad. Nunca spinners centrados ni shimmer brillante (rompe la regla de "no glow" de la sección 7).
- **Vacío:** ícono Tabler lineal (nunca ilustración o mascota genérica) + texto corto funcional describiendo la situación + acción si aplica (ej. "Registrar nuevo caso").
- **Error de carga:** ícono de alerta + mensaje claro + botón "Reintentar", usando el token `informacion` o `alerta-media` según la gravedad real del error (un fallo de red no es lo mismo que un error de permisos).

El copy específico de cada estado (qué dice exactamente el mensaje vacío o de error en cada módulo) se define en el spec del caso de uso correspondiente — este documento solo fija el patrón visual, no el contenido.

**Implementación:** cualquier página que muestre estos tres estados —no solo listados en modo Ver-only— usa los componentes compartidos `app-list-loading-skeleton`, `app-list-error-state`, `app-list-empty-state` (`frontend/src/app/shared/ui/list-states/`), nunca HTML propio que reproduzca el mismo patrón visual. `app-list-error-state` incluye el botón "Reintentar"; `app-list-empty-state` acepta contenido proyectado (`ng-content`) para una acción adicional cuando aplique (ej. CTA de subida). Reproducir el patrón con markup inline es aceptable únicamente cuando la forma real del contenido difiere de una tabla o card genérica (ej. un dashboard de KPIs, un resumen de tarjeta con título propio) o cuando el error no ofrece una acción de "Reintentar" con sentido (ej. un error de validación de formulario). Corregido 2026-08-01 (ver `.specify/docs/changelog.md`): 10 páginas reimplementaban el mismo patrón con HTML propio en vez de reusar los componentes.

**Indicador de sincronización/conexión:** un punto de estado (*dot*) + texto corto, ubicado junto al título de cualquier módulo que dependa de datos en tiempo real (ej. "Casos activos"): punto verde + "En vivo", ámbar + "Reconectando…", o gris + "Sin conexión". Se evita deliberadamente el ícono de wifi como elemento principal, por asociarse más a apps de consumo/OS que a software de control profesional. Para el técnico de campo, además, se agrega un banner no bloqueante en la parte superior del formulario activo cuando se pierde conexión ("Guardado localmente, se sincronizará al reconectar") — esto es la expresión visual concreta de la regla de resiliencia de captura en campo ya definida en la sección 2.

**Mapa (referencia):** los pines de ubicación en el mapa reutilizan los mismos tokens e iconografía semántica de severidad ya definidos en esta sección — nunca una paleta o set de formas nueva exclusiva del mapa. La elección de proveedor (Mapbox, Google Maps, Leaflet), su estilo dark correspondiente, y el comportamiento de clustering son decisiones técnicas que se documentan en `infrastructure.md`, no en este archivo.

**Responsividad (aplica a todo el sistema, breakpoints estándar):**

| Breakpoint | Rango |
|---|---|
| Mobile | < 640px |
| Tablet | 640px – 1024px |
| Desktop | > 1024px |

- **Sidebar:** Desktop/Tablet, fija a 240px. Mobile: colapsa a menú hamburguesa (ícono en el header), sidebar se muestra como overlay a pantalla completa o drawer lateral al abrir.
- **Grid de 12 columnas:** Desktop usa las 12 columnas completas. Tablet reduce a 6-8 columnas efectivas (los bloques de 3-4 columnas en desktop pasan a ocupar la mitad o el ancho completo). Mobile colapsa a 1 columna, todo apilado verticalmente.
- **Tablas:** en Desktop/Tablet se muestran como tabla tradicional. En Mobile, cada fila se transforma en un card apilado (mismo radio de card, 8-10px) con los datos en formato etiqueta-valor y el ícono de ojo visible como acción al final del card — se evita el scroll horizontal de tablas, que es una mala práctica en mobile.
- **Toasts:** ver sección de Toasts arriba (ancho completo con márgenes en mobile, ancho fijo en tablet/desktop).
- **KPIs / ring charts:** Desktop hasta 3-4 rings por fila. Tablet 2 por fila. Mobile 1 por fila (apilados), sin reducir el tamaño del ring por debajo de un mínimo legible.
- **Header:** en Mobile, la barra de búsqueda centrada puede colapsar a un ícono de lupa que expande el input al tocarlo, para no saturar el espacio horizontal junto al logo y las notificaciones.

## 6. Accesibilidad

- Contraste mínimo 4.5:1 texto normal, 3:1 texto grande, **verificado en ambos temas por separado** (claro y oscuro) para cada token semántico definido en la sección 3 — un color que cumple contraste en modo claro no garantiza cumplirlo en modo oscuro y viceversa.
- Los colores nunca son el único medio para transmitir información — siempre acompañados de íconos y labels.
- Tamaño mínimo 14px, zoom sin romper el layout.
- El cambio de tema (claro/oscuro) debe persistir por usuario (no reiniciar en cada sesión) y estar disponible desde una ubicación consistente y predecible (ej. selector en el header o en configuración de cuenta).

## 7. Reglas negativas (para evitar estética "genérica de IA")

No usar:
- Esquinas 0-2px en ningún componente (rompe la coherencia del sistema redondeado)
- Gradientes excesivos o decorativos sin función
- Neón, glow, o efectos de brillo
- Sombras fuertes o flotantes exageradas
- Íconos genéricos de "IA" (cerebros, chispas, robots) como decoración
- Formas orgánicas/blobs sin propósito
- Colores pastel o saturados que resten seriedad
- Ilustraciones stock genéricas (preferir iconografía lineal consistente, un solo set de íconos en todo el sistema)
- Exceso de whitespace decorativo que no aporte jerarquía — el espacio debe agrupar, no solo "verse limpio"
