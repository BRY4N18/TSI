# Phase 1 — Modelo de datos: Endurecimiento de Seguridad Transversal

**Fecha:** 2026-08-23 · **Plan:** [plan.md](plan.md) · **Research:** [research.md](research.md)

> ⚠️ **Esta feature no crea tablas ni columnas.** No toca el modelo dimensional
> (`Dim_*` / `Hecho_*`), que tiene su autoridad en `.specify/docs/architecture/data-model.md`.
>
> Lo que sí necesita son **estructuras en memoria** para las verificaciones, y hacer explícitas dos
> relaciones que hoy están implícitas en el código: quién es dueño de qué, y quién puede qué.

---

## 1. Entidades conceptuales

### 1.1. Actor

Quien hace la petición. Tiene **dos formas distintas** según la vía de autenticación (R2), y esto
importa porque cada una resuelve la pertenencia de otra manera.

| Forma | Clase | Atributos | Tenant |
|---|---|---|---|
| Usuario | `AuthenticatedUser` | `idusuario`, `roles[]`, `session_id` | **No lo lleva** — se resuelve vía `ClienteLookupService` |
| Partner API | `PartnerAPIUser` | `idpartner`, `idcredencial` | `idpartner`, desde la credencial |

**Clasificación transversal**, la que decide el comportamiento de US1:

- **Gestor** — `ROL_ADMINISTRADOR` o `ROL_DESARROLLADOR_APIS`. Opera sobre cualquier tenant, así
  que recibe diagnóstico preciso (`404` para inexistente).
- **No gestor** — todos los demás. «No existe» y «no es tuyo» le llegan idénticos.

> La función `es_gestor()` de `apps/partners/permissions.py` ya materializa esta distinción. El
> `ROL_DIRECTOR_TECNOLOGICO` **no** está incluido a propósito: es autoridad de los listados
> (FR-014a), no de la consola operativa.

### 1.2. Tenant

Organización propietaria de un conjunto de recursos. **No es una entidad nueva**: es el
`idcliente` que ya resuelve `ClienteLookupService`, y el `idpartner` en la vía de credencial.

Relación con Actor: un usuario pertenece a **un** cliente. Un cliente puede tener varios partners.

⚠️ **Supuesto a validar en US1:** que un usuario pertenezca siempre a un único cliente. Si existe
el caso de un usuario con varias organizaciones, el eje de aislamiento deja de ser un escalar y
toda la suite cambia de forma. `ClienteLookupService.resolve_idcliente()` devuelve un escalar, lo
que sugiere que no, pero conviene confirmarlo antes de codificar.

### 1.3. Sesión

Vínculo entre un token emitido y su validez actual; es lo que permite revocar (US3).
Vive en `Fact_Session` (Pinot), con `idsession`, `idusuario` y `estadosession`.

**Transiciones relevantes para US3:**

```
[emitida] --usar--> [válida] --expirar--> [expirada]  → 401
                        |
                        +---revocar-----> [revocada]  → 401
```

Que un token **no expirado** de una sesión revocada sea rechazado es el escenario 6 de US3, y es el
único que exige consultar el almacén en cada petición — de ahí el conflicto Seguridad ↔ Fiabilidad
documentado en el plan.

---

## 2. Estructuras de verificación (en memoria, solo en pruebas)

No se persisten. Se **derivan del sistema** en tiempo de ejecución de la suite (R3, R6).

### 2.1. `RutaInventariada`

| Campo | Tipo | Origen |
|---|---|---|
| `patron` | str | `URLResolver`, con prefijos acumulados |
| `vista` | class | `callback.view_class` |
| `parametros_id` | list[str] | Extraídos del patrón (`<int:idpartner>` → `idpartner`) |
| `metodos` | list[str] | Métodos HTTP que la vista implementa |
| `permission_classes` | list[class] | Declaradas en la vista |

**Invariante que da valor a la suite:** toda `RutaInventariada` con `parametros_id` no vacío debe
tener una prueba de aislamiento. Si no la tiene, **la suite falla** (SC-002). Es lo que impide que
la cobertura envejezca.

### 2.2. `CeldaMatriz` (US2)

`(rol, ruta) → permitido: bool | DESCONOCIDO`

15 roles × 234 rutas = **3.510 celdas**. El estado `DESCONOCIDO` es deliberado y es el punto
importante: una celda sin verificar se **reporta**, no se omite. Omitirla en silencio es
exactamente lo que hace que una matriz parcial parezca completa.

### 2.3. `TokenAdversarial` (US3)

Seis variantes, correspondientes a los seis escenarios de aceptación: firma alterada, `alg: none`,
algoritmo distinto de RS256, expirado, claims manipulados, sesión revocada. Todas deben producir
`401`.

### 2.4. `CargaInyeccion` (US4)

`(parametro, carga, tipo)` donde `tipo` ∈ {valor de filtro, nombre de columna, criterio de orden}.
La distinción importa: los valores se parametrizan, los nombres de columna y el orden **no pueden
parametrizarse** y exigen lista blanca. Es donde está el riesgo real.

---

## 3. Reglas de validación derivadas de los requisitos

| Regla | Origen | Dónde se aplica |
|---|---|---|
| Pertenencia resuelta contra el almacén, nunca desde un parámetro del cliente | FR-SEC-001 | `resolver_partner_visible` y equivalentes por módulo |
| Respuesta indistinguible para no gestores | FR-SEC-002 | Mismo código **y mismo cuerpo** (`DENEGACION_UNIFICADA`) |
| Cobertura verificada contra el inventario | FR-SEC-003 | Suite de US1 |
| Roles admitidos declarados por endpoint | FR-SEC-004 | `permission_classes` |
| Token inválido rechazado en 6 variantes | FR-SEC-005 | `JWTSessionAuthentication` |
| Entrada parametrizada o en lista blanca | FR-SEC-006 | Constructores de consultas |
| Sin dato personal en logs ni errores | FR-SEC-007 | `core/seguridad/enmascarado.py`, `response_envelope` |
| Cupos aplicados | FR-SEC-008 | `throttling.py` |
| Subidas validadas por bytes mágicos | FR-SEC-009 | `core/seguridad/validacion_archivos.py` |
| Cabeceras presentes | FR-SEC-010 | `settings.py` y `nginx.conf` |
| Token de demo rechazado en negocio | FR-SEC-011 | `demo_tokens.py` |

---

## 4. Lo que este modelo NO cubre

Declarado explícitamente para que no se dé por cubierto:

- **El canal temporal.** La rama «no existe» responde antes que «no es tuyo» porque retorna sin
  consultar el cliente. Distinguible midiendo tiempos. Fuga de menor ancho de banda, real, abierta
  (`decisiones-pendientes.md` #51).
- **Los siete servicios de Partners** que lanzan `not_found` por su cuenta
  (`consulta_partner_service`, `emitir_credencial_service`, `metricas_consumo_service`,
  `promocion_produccion_service`, `reactivar_partner_service`, `suspender_partner_service`,
  `asignar_plan_acceso_service`). Sin revisar si un no gestor los alcanza con un id ajeno.
- **El resto de módulos.** El oráculo se cerró en Partners; el mismo patrón puede existir en
  Cuentas-Clientes, Soporte o Suscripciones. Es el trabajo que la suite transversal debe destapar.
- **Contenido malicioso dentro de un fichero de tipo válido** (R4).
