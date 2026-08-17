# Research — Informes tácticos simples de Partners y API (Frontend)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md)

## D0 — Cerrar FR-014a en el permiso de informes, no en `es_gestor()` operativo

**Decision:** añadir `ROL_DIRECTOR_TECNOLOGICO` a un conjunto **nuevo**
`ROLES_GESTORES_INFORMES` = Administrador + DesarrolladorAPIs + Director Tecnológico.
`InformesAccesoPermission` / `InformesContratoPermission` y `acotar()` de los listados usan
`es_gestor_informes()`. `es_gestor()` —el que exime `verificar_propiedad` en consola, emisión,
suspensión— **no cambia**.

**Rationale:** FR-014a exige al Director en los cinco listados, sin acotar. Hoy el token
`DirectorTecnologico` recibe `403` (el fixture `director_tecnologico_informes_headers` existe y no
se usa). Meterlo en `es_gestor()` le daría operación sobre cualquier partner por URL, y la consola
no se la abre (FR-UI fuera de alcance: «no abrir al Director la consola operativa»). El acotamiento
de informes tiene que tratarlo como gestor de **lectura**; el de escritura, no.

**Alternatives considered:** esconder al Director en el frontend para coincidir con el `403` —
deja mintiendo el backend spec. Añadirlo a `es_gestor()` — ensancha el módulo operativo. Un tercer
permiso DRF solo para él — duplica lo que un conjunto más amplio de gestores de informe ya expresa.

## D1 — Copiar Soporte, no Cuentas, para guards e índice

**Decision:** dos guards como Soporte (`tickets` amplio / `escalados` estrecho):

| Guard | Roles | Rutas |
|---|---|---|
| `informesAccesoGuard` | Partner, DesarrolladorAPIs, Administrador, DirectorTecnologico | índice, partners, credenciales, cambios-acceso |
| `informesContratoGuard` | DesarrolladorAPIs, Administrador, DirectorTecnologico | versiones-contrato, alcance-datos |

Las dos de contrato van **antes** de `:informe`, con `path` literal y `data.informe`. El índice usa
el amplio y filtra enlaces por rol.

**Rationale:** Cuentas parte al revés (el estrecho es el que el Director *sí* ve). Aquí el Partner
es quien *no* ve dos listados. Un guard único con la unión le daría versiones y alcance (FR-UI-022).

**Alternatives considered:** reusar `gestorPartnersGuard` — no incluye al Director. Tres guards —
innecesario: acceso vs contrato basta.

## D2 — Ruta `/partners/informes` hermana, no hija del redirect a consola

**Decision:** `loadChildren` en `app.routes.ts` con `path: 'partners/informes'` **antes** de
`path: 'partners'`. El módulo operativo redirige `''` → `consola`; anidar informes ahí sin cuidado
mandaría al Partner a una consola que su guard rechaza.

**Rationale:** es el patrón de la serie (`cuentas-clientes/informes`, `soporte-cliente/informes`).
FR-UI-001.

**Alternatives considered:** `path: 'informes'` dentro de `PARTNERS_ROUTES` — viable si cada hijo
tiene su guard y no hereda el de consola, pero el `redirectTo: 'consola'` del `''` sigue siendo una
trampa. Hermana en `app.routes.ts` es la que ya está probada.

## D3 — Dos entradas de menú, misma ruta, textos distintos

**Decision:**

| Etiqueta | Roles | Grupo |
|---|---|---|
| Informes de partners | Administrador, DesarrolladorAPIs, DirectorTecnologico | Partners y API |
| Estado de mi acceso | PartnerIntegracion | Partners y API |

Misma `path: '/partners/informes'`. El Partner no lee «todos los partners»; el gestor no lee «mi
integración». Consola y portal **no** ganan un enlace cruzado.

**Rationale:** design-system §5 ya aplicado en nav-links de Partners. FR-UI-005. Un solo ítem con
la unión de roles forzaría un texto que miente a uno de los dos públicos.

**Alternatives considered:** `/partners/consola/informes` y `/partners/portal/informes` como dos
rutas al mismo componente — duplica guards y no aporta. Un índice distinto por superficie — dos
catálogos que se desfasarían.

## D4 — Una página, cinco definiciones; el filtro `partner` se oculta al Partner

**Decision:** `informe.page.ts` único. El filtro `partner` (número) se declara en los tres de
acceso y la página **no se lo pasa** a la barra cuando el actor es Partner. No se añade un campo
`visiblePara` a `shared/informes` en esta pasada.

**Rationale:** FR-UI-009. Mostrarle al Partner un selector cuyo único efecto útil es un `403` es
ofrecer un control para provocar un error. Extender la capa compartida por un solo filtro de un
solo departamento es la señal de generalización incompleta; aquí basta con no pasarlo.

**Alternatives considered:** no declarar el filtro — los gestores perderían FR-009. Dejarlo y
tragar el `403` — viola FR-UI-009. `visiblePara` en `FiltroListado` — aplazado a un tercer caso.

## D5 — Enumeraciones: las que el backend valida, no el typo del OpenAPI

**Decision:**

| Filtro | Fuente de los valores del desplegable |
|---|---|
| `estado` (partners) | `ESTADO_*` de `domain_constants` (los seis que importa la vista) |
| `entorno` | `ENTORNOS` = `Sandbox`, `Producción` |
| `tipo_cambio` | constantes `CAMBIO_*` (la vista las recoge con `startswith("CAMBIO_")`) |
| `estado` (versiones) | `ESTADOS_VERSION` |

La prueba de definiciones compara **columnas y `admiteRango`** contra el OpenAPI (transcripción,
igual que Cuentas) y **enumeraciones** contra esas constantes, transcritas en el spec de prueba.

**Rationale:** el backend de este módulo **importa** el dominio a propósito (research D5 de
backend): copiar en la vista produciría un `400` engañoso el día que se añada un tipo. El OpenAPI
declara `entorno: [Sandbox, Produccion]` **sin tilde**; `parse_enumeracion` valida contra
`ENTORNOS` (`Producción`). Pintar `Produccion` haría que **cada** uso del filtro fuera un `400`.

**Alternatives considered:** copiar el OpenAPI al pie de la letra — el desplegable mentiría. Pedir
un endpoint de metadatos — fuera de alcance.

## D6 — Alinear el enum `entorno` del OpenAPI con `ENTORNOS`

**Decision:** en el mismo trabajo, el contrato backend pasa `Produccion` → `Producción`. No se
añaden campos. No se toca el resto del OpenAPI.

**Rationale:** D5 deja de tener dos fuentes. Compatibility: el frontend consume el contrato; si el
contrato nombra un valor que la vista rechaza, el contrato miente.

**Alternatives considered:** dejar el typo y documentarlo — la prueba de columnas vs OpenAPI no
caza el filtro, y el siguiente implementador copiaría el valor roto.

## D7 — No hay columna de motivo en credenciales; `tipo_cambio` no se agrupa

**Decision:** el catálogo de credenciales declara `activa` (booleano) y **ningún** campo de motivo.
El de cambios de acceso declara `tipo_cambio` como texto; el desplegable lista cada `CAMBIO_*` por
separado. Prohibido un filtro «inactivas» que una revocación, cascada y expiración.

**Rationale:** FR-UI-027, FR-UI-028, backend FR-006/007. Agrupar en el cliente reintroduce el
compuesto que el módulo existió para no hacer.

## D8 — Mensajes vacíos de dominio; el del Partner menciona el acotamiento

**Decision:** cada definición lleva `mensajeVacio` de dominio. La capa compartida ya antepone el
aviso de `acotado_a` cuando no es `todos`. El mensaje del Partner no dice «no hay partners en el
sistema»; dice que no hay resultados **entre los suyos** (el aviso cubre la segunda mitad; el
mensaje nombra el listado).

**Rationale:** contrato frontend §2.1. Soporte ya lo ejercitó. Aquí se vuelve a ejercitar
(`propios` vs `todos`).

## D9 — No tocar consola, portal, ni logs

**Decision:** cero cambios en `partners.routes.ts` operativo, cero en páginas de consola/portal,
cero en la consola de registros. «Llamadas rechazadas por límite» sigue ahí.

**Rationale:** fuera de alcance de la spec. Un sexto listado duplicaría OT09 ya cubierto.

## D10 — Pruebas de exclusión, no solo de entrada

**Decision:** los specs de guard comprueban que el Partner **no** pasa `informesContratoGuard` y
que un Operador **no** pasa ninguno. El índice, que un Partner obtiene tres ids y un gestor cinco.
Las definiciones, que credenciales no declara campo de secreto ni de motivo.

**Rationale:** un permiso de unión pasa si solo se testea que cada rol entra a *lo suyo*. Es la
lección de Cuentas y de Red Operativa compuestos.
