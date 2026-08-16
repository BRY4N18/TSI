# Research — Informes Tácticos Simples de Partners y API (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el código real.

---

## D1 — El acotamiento ya está resuelto y se reutiliza tal cual

**Hallazgo.** `apps/partners/permissions.py:77` implementa `verificar_propiedad`, que:

- Resuelve la cuenta del solicitante con **el mismo servicio que usa Soporte**, y lo dice: *«en vez
  de duplicar la consulta»*.
- Exime a los gestores, porque su trabajo es operar sobre partners ajenos.
- **Lanza una excepción en vez de devolver un booleano**, «para que sea imposible ignorar el
  resultado por descuido».

**Decisión.** Los listados reutilizan `verificar_propiedad` y el criterio de pertenencia **amplio**,
el mismo que Soporte. **No se toca la capa transversal ni se añade un criterio nuevo.**

**Rationale.** Es el segundo módulo consecutivo que solo consume `core/informes/`. Que dos
departamentos distintos —uno acotando por cliente reportador y otro por organización de partner— usen
la misma pieza sin modificarla es la confirmación de que la parametrización hecha en Red Operativa
fue suficiente.

**El detalle de diseño que conviene copiar:** que la comprobación **lance** en vez de devolver un
booleano. Un `if not verificar(...)` olvidado es un fallo silencioso de autorización; una excepción
no se puede ignorar por descuido.

> **Hereda la limitación de Soporte.** La resolución de cuenta cae en el administrador local porque
> la tabla de vínculos no la escribe ningún código. Un usuario de partner que no sea administrador
> local de su cuenta **no resolverá**, y recibirá una negativa. Es la misma limitación ya anotada,
> no un defecto de estos listados.

---

## D2 — Por qué una credencial está inactiva no se puede saber desde la credencial ⚠️

**Hallazgo.** El servicio de reactivación de partners documenta el problema al explicar cómo evita
resucitar credenciales comprometidas:

> *«No pregunta "¿por qué está inactiva esta credencial?" — no podría: las tres razones (cascada,
> revocación, expiración) son **indistinguibles** en `Dim_CredencialAPI`.»*

Su solución es estructural: lee las filas de desactivación en cascada del **último evento de
suspensión** en la bitácora y restituye exactamente ese conjunto. Una credencial que el partner
revocó ya estaba inactiva antes de la suspensión, así que no generó fila de cascada y sencillamente
no aparece en la lista.

**Decisión.** El listado de credenciales informa de **si** está activa, su entorno y su vigencia.
**No informa del motivo.** Los motivos se listan en la bitácora de cambios de acceso, cada uno con su
tipo propio.

**Rationale.** Averiguar el motivo desde la credencial exige localizar el último evento relevante por
credencial en la bitácora y volver a cruzar: **una agregación más un cruce**, es decir compuesto. Es
la misma forma que la disponibilidad de una unidad en Red Operativa.

**Y la consecuencia de negocio no es teórica.** Un listado de credenciales inactivas sin distinguir
el motivo pondría en la misma línea una **decisión de seguridad del partner** y un **impago
administrativo**. Quien reactivara guiándose por él, sin mirar la bitácora, resucitaría una
credencial comprometida — exactamente lo que la regla de reactivación selectiva previene.

**Alternativa descartada.** *Resolver el motivo con una consulta a la bitácora por credencial* —
N+1 consultas por página, y seguiría siendo la respuesta correcta a una pregunta que corresponde a
un informe compuesto.

---

## D3 — Lista blanca de columnas, no lista negra de secretos ⚠️

**Hallazgo.** El módulo ya protege el secreto de autenticación, pero **con una lista negra**:
`consulta_partner_service.py:36` declara un conjunto de campos prohibidos y los descarta después de
leer la fila.

**Decisión.** Los repositorios de estos listados **enumeran las columnas que sí devuelven**, en vez
de leerlas todas y descartar las prohibidas. La lista negra existente se mantiene como **segunda
línea de defensa**, no como única.

**Rationale.** Una lista negra falla abierta: si mañana se añade una columna con material sensible a
la tabla de credenciales, **no estará en el conjunto prohibido y saldrá en la respuesta**. Nadie se
dará cuenta, porque la respuesta seguirá teniendo la forma esperada, solo que con un campo de más.

Una lista blanca falla cerrada: una columna nueva simplemente no aparece hasta que alguien decida
incluirla.

Es la misma lección que en Soporte con el texto de las notas internas, aplicada a un dato de mayor
consecuencia: el secreto con el que un partner se autentica contra la API.

**Se conservan ambas** porque no se estorban: la lista blanca protege estos listados, y la lista
negra sigue protegiendo el resto del módulo, que no se toca.

---

## D4 — Las llamadas rechazadas por límite ya están cubiertas

**Hallazgo.** `apps/partners/views/metricas_views.py:78` implementa la consola de registros de
llamada, y su documentación enumera lo que ofrece: filtros por código de respuesta, por credencial,
por endpoint y por rango de fechas, **todos resueltos en la base**, más paginación real por cursor.
Su acceso ya está resuelto: gestores sobre cualquier partner, y el partner sobre el suyo.

**Decisión.** **No se construye un listado de llamadas rechazadas.** La pregunta del catálogo se
responde con un filtro sobre el endpoint existente.

**Rationale.** Duplicar una vista que ya filtra, acota y pagina correctamente añadiría superficie sin
aportar capacidad. Además, aquella vista arrastra una corrección reciente —el partner puede
consultar sus propios errores, que es lo que la regla de negocio pedía y el permiso impedía—; un
endpoint paralelo se arriesgaría a repetir el error corregido.

**Efecto colateral útil:** ninguno de los cinco listados de esta spec lee el registro de llamadas, así
que **la cuestión de exponer o no la dirección de origen de cada petición no llega a plantearse**.
Queda donde ya estaba resuelta.

---

## D5 — Los estados y los tipos de cambio son enumeraciones cerradas

**Hallazgo.** El módulo declara sus vocabularios en un único sitio:

- **Seis estados de partner:** Registrado, Plan asignado, Pruebas activo, Pendiente de aprobación,
  Producción activa, Suspendido.
- **Trece tipos de cambio de acceso**, entre ellos los dos que D2 exige distinguir: revocación de
  credencial y desactivación por cascada.

**Decisión.** Los filtros de los listados validan contra esas enumeraciones **importándolas**, no
copiándolas.

**Rationale.** Copiar los valores en el módulo de informes crearía dos fuentes de verdad: el día que
se añada un estado, el filtro lo rechazaría con un `400` engañoso —«no es válido»— cuando en realidad
sí lo es. Importar hace que el listado siga automáticamente al dominio.

**Nota sobre los estados.** «Pruebas activo» y «Producción activa» **no son excluyentes** en la
práctica: un partner en producción conserva su acceso de pruebas. El estado del partner describe el
punto de su incorporación, y el entorno de cada credencial se lee en el listado de credenciales.

---

## D6 — La suspensión exige motivo; la reactivación, no

**Hallazgo.** El servicio de reactivación lo declara: *«El motivo es opcional aquí (a diferencia de
la suspensión): el SRS exige motivo al cortar el acceso, no al devolverlo.»*

**Decisión.** El listado de cambios de acceso presenta el motivo **como ausente** en las
reactivaciones, sin tratarlo como dato faltante ni como cadena vacía.

**Rationale.** Es una asimetría deliberada de la regla de negocio, no una laguna de datos. Marcar
esas filas como incompletas induciría a «corregir» algo que está bien.

---

## D7 — Formas de cursor y tipo de cada listado

Se reutiliza la paginación keyset. Nada nuevo.

| Listado | Tipo | Orden por defecto | Cursor |
|---|---|---|---|
| Partners | Estado actual | `idpartner DESC` | Escalar |
| Credenciales | Estado actual | `fecha_expiracion ASC` — lo que antes caduca, primero | Compuesto `fecha_expiracion\|idcredencial` |
| Cambios de acceso | **Período opcional** | `fecha_cambio DESC` | Compuesto `fecha_cambio\|idhistorial` |
| Versiones del contrato | Estado actual | `fecha_publicacion DESC` | Compuesto `fecha_publicacion\|idversion` |
| Alcance de datos | Estado actual | `id_preferencia DESC` | Escalar |

**Nota sobre la fecha de expiración.** Es una marca de tiempo numérica, así que el filtro por
proximidad de caducidad se resuelve **entero en la base** — como en Suscripciones y a diferencia del
listado de demos de Ventas y CRM, que necesitó dos pasos por ser texto. Verificar el tipo antes de
diseñar el filtro sigue siendo la regla.

> **Dato de entorno conocido, no defecto.** La revisión anterior dejó constancia de una credencial de
> pruebas sembrada a mano con el centinela de vigencia propio de producción. Al ordenar por
> caducidad aparecerá al final; el código de emisión asigna la vigencia correctamente.
