# Phase 0 — Research: Endurecimiento de Seguridad Transversal

**Fecha:** 2026-08-23 · **Plan:** [plan.md](plan.md) · **Spec:** [spec.md](spec.md)

Resuelve las incógnitas del *Technical Context* antes de diseñar. Todo lo que aquí se afirma sobre
el sistema está **verificado contra el código**, no supuesto.

---

## R1 — ¿Cómo se identifica el tenant? (bloqueaba US1)

**Decisión:** la pertenencia se resuelve **contra el almacén**, no desde el token.

**Hallazgo.** El JWT **no lleva claim de tenant**. `core/jwt_utils.py` firma un payload de tres
campos: `sub`, `roles` y `session_id`. La pertenencia se resuelve en la capa de servicio con
`verificar_propiedad()` (`apps/partners/permissions.py`), que obtiene el cliente del usuario vía
`ClienteLookupService` — el mismo servicio que usa Soporte.

**Rationale.** La suposición de partida («el filtro de tenencia debe aplicarse en la capa de datos
a partir de los claims») habría llevado a rediseñar un mecanismo que ya es correcto: resolver
contra el almacén es **más seguro** que confiar en un claim, porque un token robado con claim
manipulado no sirve de nada si el vínculo se comprueba en la base. Lo que falta no es el mecanismo,
es **aplicarlo y verificarlo en todas partes**.

**Alternativas descartadas.**
- *Añadir un claim `idcliente` al JWT.* Rechazada: mejoraría el rendimiento (evita una consulta por
  petición) a cambio de mover la verdad al token. Un token es un dato que el cliente custodia; el
  vínculo de pertenencia no debe vivir ahí. Además obligaría a reemitir todos los tokens vivos.
- *Middleware que inyecte el tenant en cada petición.* Rechazada por Mantenibilidad: añade magia
  implícita difícil de seguir para un mantenedor único (Principio VII).

---

## R2 — ¿Cuántas vías de autenticación hay que cubrir? (bloqueaba US1)

**Decisión:** **dos**, y la suite debe cubrir ambas o dejará media superficie sin probar.

| Vía | Clase | Cómo resuelve el tenant |
|---|---|---|
| Usuario | `apps.cuentas_clientes.authentication.JWTSessionAuthentication` | Sin claim; vía `ClienteLookupService` |
| Partner API | `apps.partners.authentication.CredencialAPIAuthentication` | `PartnerAPIUser.idpartner`, desde la credencial |

**Rationale.** `CredencialAPIAuthentication` descompone un `client_id` en `(idpartner,
idcredencial)` y construye un `PartnerAPIUser` que **sí** conoce su `idpartner`. Es un modelo de
identidad distinto del JWT de usuario, con superficie y modos de fallo propios.

**Riesgo si se ignora:** una suite que solo cubra el JWT reportaría «100 % de endpoints cubiertos»
dejando fuera toda la API de partners — precisamente la que consumen terceros. Sería peor que no
tener suite, porque produce confianza infundada.

---

## R3 — ¿Cómo enumerar los endpoints sin escribir una lista a mano?

**Decisión:** recorrer el `URLResolver` de Django en tiempo de prueba.

**Verificado ejecutándolo** contra el sistema real:

```
rutas api/v1 totales:               234
rutas con identificador en el path:  92
```

Esas 92 son el alcance exacto de US1 (más los identificadores en cuerpo, que no aparecen aquí).

**Rationale.** Es el único enfoque que satisface **SC-002**: añadir un endpoint sin filtro de
tenencia debe hacer fallar la suite. Con una lista a mano el endpoint nuevo simplemente no se
prueba, y el informe sigue diciendo «todo cubierto».

**Alternativas descartadas.**
- *Lista de endpoints en un fichero.* Rechazada: es exactamente el fallo que la regla busca evitar.
- *Leer los 37 OpenAPI.* Rechazada: describen el contrato **declarado**, no las rutas realmente
  registradas. Un endpoint implementado y no documentado —el caso peligroso— sería invisible.

**Detalle de implementación.** El recorrido debe ser recursivo sobre `url_patterns` e ir
acumulando el prefijo; los `include()` anidan resolvers. Se filtran los identificadores con un
patrón sobre `<...id...>` en la ruta.

---

## R4 — Detección de tipo real de archivo (US7)

**Decisión:** `puremagic`.

**Hallazgo.** Ninguna de las tres candidatas está instalada hoy (`magic`, `filetype`, `puremagic`).

**Rationale.** `python-magic` es la más completa pero depende de la biblioteca C `libmagic`, que en
Windows exige binarios aparte — el entorno de desarrollo de este proyecto es Windows y el
despliegue Linux, así que introduciría una divergencia entre ambos. `puremagic` es Python puro, sin
dependencias nativas, y para el caso de uso —distinguir imágenes reales de ejecutables y SVG con
script— es suficiente. Pesa a favor la Mantenibilidad (Principio VII): una dependencia que se
instala igual en los dos entornos.

**Alternativas descartadas.**
- *`python-magic`.* Rechazada por la dependencia nativa y la divergencia Windows/Linux.
- *Validación propia leyendo cabeceras.* Rechazada: reimplementar detección de formatos es
  superficie de bugs sin ganancia. La spec ya lo excluye en sus supuestos.

⚠️ **Advertencia.** Los bytes mágicos identifican el formato, **no garantizan que el contenido sea
inocuo**. Un JPEG válido puede llevar carga en metadatos. US7 cubre la confusión de tipo, que es su
alcance declarado; el análisis de contenido no está en este plan.

---

## R5 — Alcance del fail-closed en la validación de sesión (US3)

**Decisión:** **fail-closed por defecto, con una lista explícita de exclusiones que debe fijarse
antes de implementar US3.**

**Rationale.** Ante un fallo del almacén de sesión, denegar es lo correcto en general (regla 3 del
mecanismo de desempate: datos de identidad sensibles). Pero el Principio IX es absoluto: **si está
en juego la seguridad física de personas, Safety gana sobre Security sin excepción**. Un operador
que no puede despachar una ambulancia porque Redis no responde es un fallo peor que el que se
intenta evitar.

### R5.1 — Resuelto (T030/T031): la disyuntiva también era falsa

**Decisión final: degradación a validación criptográfica, no fail-open ni fail-closed.**

Al leer `SessionValidationService.validate_token_and_session` aparece que la validación son **dos
pasos con propiedades distintas**:

```python
claims = verify_access_token(token)          # 1. Criptografía pura. SIN E/S.
if not self.session_repo.is_active(session_id):   # 2. Requiere el almacén.
    raise SessionValidationError("Session closed or revoked")
```

El paso 1 —firma RS256, expiración, formato de claims— **sigue funcionando con el almacén caído**.
Solo el paso 2 depende de infraestructura. Plantear la elección como «denegar todo o admitir todo»
daba por perdida la autenticación entera cuando en realidad solo se pierde **la comprobación de
revocación**.

**La regla, entonces:**

| Situación | Fuera de la cadena crítica | En la cadena crítica |
|---|---|---|
| `is_active` devuelve `False` (revocada) | `401` | `401` — **también aquí** |
| `is_active` **lanza** (almacén caído) | `401` (fail-closed) | Degradar al paso 1 y continuar |

⚠️ **La distinción decisiva:** «sesión revocada» y «no puedo comprobar si está revocada» son cosas
distintas y hoy el código las trata igual, porque ambas terminan en excepción. Una sesión revocada
se deniega **siempre**, cadena crítica incluida: no hay ningún argumento de seguridad física para
dejar entrar a alguien a quien se le retiró el acceso a propósito.

**Lo que se sacrifica, dicho explícitamente:** durante una caída del almacén, un token robado y
revocado hace minutos seguiría sirviendo **en los endpoints de la cadena crítica** hasta que expire.
Es una ventana acotada por la vigencia del token, y el Principio IX es absoluto: una ambulancia que
no se despacha porque Redis no responde es peor.

### Endpoints de la cadena crítica (inventario T030)

Derivados del `Additional Constraints` de la constitución —registro → validación → asignación de
unidad → confirmación de despacho → seguimiento— cruzados con el inventario de rutas:

| Etapa | Endpoints | Por qué degradan |
|---|---|---|
| Registro | `POST /accidentes`, `.../confirmar` | Sin registro no hay despacho posible |
| Asignación | `.../despacho/asignar-manual`, `.../unidades-candidatas` | Es el acto de enviar ayuda |
| Confirmación | `/mi-despacho/{id}/confirmar`, `/rechazar` | La unidad no puede aceptar el aviso |
| Seguimiento | `/mi-seguimiento/posicion`, `.../llegada`, `/seguimiento/stream` | Se pierde de vista una unidad en ruta |

**Quedan FUERA de la degradación**, pese a estar cerca de la cadena:

- **Los catálogos** (`/accidentes/paises`, `estados`, `ciudades`, `calles`…). Son lectura de
  referencia: su denegación degrada el formulario, no impide salvar a nadie. Además son la
  superficie más grande y menos vigilada.
- **Los informes y listados históricos** (`/informes/emergencias/cierres`, `/seguimiento/mapa` de
  consulta). Se consultan *después*, no durante.
- **Todo lo que no es la cadena**: partners, suscripciones, ventas, soporte, cuentas.

> El criterio para entrar en la lista no es «pertenece al módulo de emergencias», sino **«su
> denegación durante una caída retrasa la llegada de ayuda a una persona»**. Con el criterio ancho
> la lista sería de 46 rutas; con el estricto son 9.

⚠️ **Requiere confirmación del responsable antes de implementarse** (T035–T038): es una decisión
con impacto en seguridad física, y la constitución exige justificación explícita de Safety y
Reliability para cualquier cambio que toque esta cadena.

**Alternativas descartadas.**
- *Fail-open en todo.* Rechazada: admitiría sesiones revocadas en todo el sistema, incluidos
  partners y facturación, donde no hay ningún argumento de seguridad física.
- *Fail-closed en todo.* Rechazada por Principio IX.
- *Caché local de sesiones válidas.* Reduciría aún más la ventana, pero añade un estado que
  invalidar y un modo de fallo nuevo. Desproporcionado para un mantenedor único (Principio VII);
  anotada como mejora futura.

---

## R6 — Magnitud de la matriz rol × endpoint (US2)

**Decisión:** generar la matriz, no escribirla.

**Hallazgo verificado:** **15 roles** declarados (`ROL_ADMINISTRADOR`, `ROL_CLIENTE`,
`ROL_DESARROLLADOR_APIS`, `ROL_DIRECTOR_*` ×7, `ROL_GERENTE`, `ROL_GERENTE_EXITO_CLIENTE`,
`ROL_PARTNER_INTEGRACION`, `ROL_SOPORTE`) × **234 rutas** = **3.510 combinaciones**.

**Rationale.** A esa escala, escribir la matriz a mano no es una opción — ni redactarla ni
mantenerla. Se genera cruzando el inventario de R3 con el registro de roles, y se comprueba contra
las `permission_classes` declaradas en cada vista.

⚠️ **Riesgo de rendimiento.** 3.510 peticiones HTTP reales harían la suite inviable en el ciclo
rápido. Diseño previsto: interrogar **la clase de permiso** directamente (como ya hace
`test_permisos_red_operativa.py::_concede`) en vez de pasar por HTTP, y reservar el camino HTTP
completo para una muestra de casos de denegación. Es un compromiso consciente: se gana cobertura
exhaustiva de la decisión de acceso a cambio de no ejercitar la pila entera en cada celda.

---

## R7 — Lección heredada aplicable a todas las suites

Toda prueba nueva de este bloque debe incluir la fixture que mockea Pinot:

```python
@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot
```

**Por qué.** `JWTSessionAuthentication` valida la sesión contra Pinot. Sin el mock, la petición
espera a que venza el timeout de red y la excepción se traduce en `AuthenticationFailed` → `401`.
El síntoma **aparenta ser un fallo de permisos** y cuesta horas de diagnóstico; la pista real es el
tiempo de ejecución. Costó 42 pruebas en falso rojo el 2026-08-23 (`changelog.md` C3).

---

## Resumen de decisiones

| # | Asunto | Decisión |
|---|---|---|
| R1 | Identificación de tenant | Contra el almacén (`ClienteLookupService`), no desde el token |
| R2 | Vías de autenticación | Dos: JWT de usuario y credencial de partner |
| R3 | Inventario de endpoints | Recorrer el `URLResolver` — 234 rutas, 92 con identificador |
| R4 | Detección de tipo de archivo | `puremagic` (Python puro, sin dependencia nativa) |
| R5 | Fail-closed en sesión | Por defecto sí, con exclusiones de la cadena crítica **por fijar antes de US3** |
| R6 | Matriz rol × endpoint | Generada — 15 roles × 234 rutas; interrogar la clase de permiso, no HTTP |
| R7 | Fixture obligatoria | `mock_pinot` en toda prueba autenticada |

**Ninguna incógnita queda abierta.** La única condición previa es la lista de exclusiones de R5,
que es trabajo de la propia US3 y está anotada como tal.
