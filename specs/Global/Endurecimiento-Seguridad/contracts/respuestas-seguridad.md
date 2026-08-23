# Contrato: respuestas de denegación

**Fecha:** 2026-08-23 · **Plan:** [../plan.md](../plan.md)

> **Por qué este contrato no es un OpenAPI.** Esta feature **no añade endpoints**: endurece los 234
> existentes, cuyos contratos ya viven en los 37 ficheros `*.openapi.yaml` de cada módulo. Lo que
> falta especificar no es una ruta nueva, sino **la forma exacta de las respuestas de denegación**
> — transversal a todos ellos y hoy no escrita en ninguna parte.
>
> Restricción heredada del plan: **no se rompe ningún contrato publicado.** Los códigos aquí
> descritos ya estaban declarados; lo que se fija es *cuál* corresponde a cada caso y *qué cuerpo*
> lleva.

Formato base, según `.specify/docs/architecture/api-standards.md`:

```json
{ "error": "error_code", "detail": "mensaje", "code": "ERROR_CODE" }
```

---

## C1 — Recurso de otro tenant o inexistente

**La regla que gobierna todo lo demás:** para un actor **no gestor**, ambos casos producen una
respuesta **byte a byte idéntica**. Cualquier diferencia —código, cuerpo, o una latencia
apreciablemente distinta— reabre el oráculo de enumeración.

### Actor NO gestor

Da igual si el recurso existe:

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": "forbidden",
  "detail": "El partner no pertenece al cliente autenticado",
  "code": "propiedad_partner"
}
```

⚠️ El `detail` es **una constante** (`DENEGACION_UNIFICADA`), no un mensaje redactado en el punto
de fallo. Redactarlo en cada sitio es cómo aparecen las diferencias que filtran.

### Actor gestor (`ROL_ADMINISTRADOR`, `ROL_DESARROLLADOR_APIS`)

Conserva el diagnóstico preciso, porque opera sobre cualquier tenant y no le revela nada:

```http
HTTP/1.1 404 Not Found

{ "error": "not_found", "detail": "Partner no encontrado", "code": "not_found" }
```

**Contrato de prueba (US1):**

| Actor | Recurso | Código | Cuerpo |
|---|---|---|---|
| No gestor | Inexistente | `403` | `DENEGACION_UNIFICADA` |
| No gestor | De otro tenant | `403` | `DENEGACION_UNIFICADA` |
| No gestor | Propio | `200` | Datos |
| Gestor | Inexistente | `404` | «Partner no encontrado» |
| Gestor | De cualquier tenant | `200` | Datos |

Las dos primeras filas deben ser **indistinguibles**. Es el aserto central de US1.

---

## C2 — Rol no autorizado (US2)

Eje distinto del anterior: aquí el recurso **puede existir y ser del tenant correcto**, pero la
materia no corresponde al rol.

```http
HTTP/1.1 403 Forbidden

{ "error": "forbidden", "detail": "<materia no autorizada>", "code": "403" }
```

⚠️ **No se unifica con C1 a propósito.** Aquí no hay existencia que ocultar: el usuario ya sabe
que el recurso existe porque pertenece a su organización. Unificar degradaría el diagnóstico sin
ganar seguridad.

---

## C3 — Credencial ausente, inválida o revocada (US3)

Las seis variantes adversariales producen **la misma respuesta**. Distinguir «firma inválida» de
«expirado» informa al atacante de qué modificar.

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer

{ "error": "unauthorized", "detail": "Token invalido o credenciales invalidas", "code": "401" }
```

| Variante | Código |
|---|---|
| Firma alterada · `alg: none` · algoritmo ≠ RS256 · expirado · claims manipulados · sesión revocada | `401` |

**Distinción que sí debe mantenerse:** `401` = «no sé quién eres» · `403` = «sé quién eres y no
puedes». Un endpoint que devuelve `401` a un usuario autenticado con rol insuficiente está mal
—fue el fallo de `changelog.md` C3— y confunde al cliente legítimo sin beneficio.

---

## C4 — Cupo superado (US6)

```http
HTTP/1.1 429 Too Many Requests
Retry-After: <segundos>

{ "error": "throttled", "detail": "Limite de peticiones excedido", "code": "429" }
```

Aplica a los cuatro throttles declarados: `prospecto_registro` (10/min), `demo_sesion_ip` (20/min),
`demo_interaccion_token` (60/min), `partner_api` (1000/min).

⛔ **Frontera de negocio.** Esto es el techo **técnico** de plataforma. **No** es la cuota comercial
`RN-APM-002`, donde el cupo mensual **nunca bloquea: se factura**. Una prueba que espere `429` por
cuota mensual verificaría lo contrario de la regla de negocio.

---

## C5 — Subida rechazada (US7)

| Caso | Código | `code` |
|---|---|---|
| Tipo real no permitido (bytes mágicos) | `400` | `tipo_no_permitido` |
| Excede el límite de tamaño | `413` | `payload_too_large` |
| Nombre con travesía de rutas | `400` | `nombre_invalido` |

⚠️ El `detail` **no** debe revelar qué tipo se detectó realmente: «se esperaba imagen» basta;
«se detectó PE ejecutable» le confirma al atacante que la detección funciona y por dónde.

---

## C6 — Cabeceras obligatorias (US8)

Presentes en **toda** respuesta, incluidos los errores:

| Cabecera | Valor | Entorno |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Todos |
| `X-Frame-Options` | `DENY` | Todos |
| `Referrer-Policy` | `same-origin` | Todos |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | No local |
| `Content-Security-Policy` | Por definir en US8 | No local |

Verificable en Django y en `frontend/nginx.conf`; ninguno de los dos puede contradecir al otro.

---

## C7 — Invariante transversal: los errores no filtran

Aplica a **todas** las respuestas anteriores y a cualquier `500`:

- Sin traza de pila, rutas internas, nombres de tabla ni SQL.
- Sin datos personales, coordenadas exactas de víctimas, tokens ni credenciales.
- El `detail` describe **qué pasó**, nunca **por qué internamente**.

Es `FR-SEC-007` (US5) y la razón de que el manejador central
(`core/api/response_envelope.custom_exception_handler`) sea el único camino de salida admitido.
