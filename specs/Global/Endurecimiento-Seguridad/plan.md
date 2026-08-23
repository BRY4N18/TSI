# Implementation Plan: Endurecimiento de Seguridad Transversal

**Branch**: `Endurecimiento-Seguridad` | **Date**: 2026-08-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/Global/Endurecimiento-Seguridad/spec.md`

---

## Summary

Implementar las nueve reglas `PG-SEC-*` pendientes o parciales del [Plan Global de
Pruebas](../PlanPruebas/spec.md) §8, cinco de ellas Bloqueantes.

El enfoque técnico central, y lo que distingue este plan de «escribir unas pruebas de seguridad»,
es que **las verificaciones se construyen sobre inventarios derivados del propio sistema**, no
sobre listas escritas a mano: el inventario de rutas del enrutador de DRF (US1, US2), el registro
de throttles de `settings.py` (US6), el catálogo de consultas de informes (US4). Una lista escrita a
mano envejece en cuanto alguien añade un endpoint y, peor, **da sensación de cobertura completa
mientras deja huecos**. Es la misma lección que ya produjo `PG-CFG-002`, cuyo registro de secretos
se comprueba contra `settings.py` en vez de mantenerse a mano.

Este trabajo **no introduce funcionalidad de negocio**: endurece y verifica la existente. La única
excepción prevista es US7 (validación de subidas por bytes mágicos), que sí añade una comprobación
que hoy no existe.

---

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x / Angular 19 (frontend)

**Primary Dependencies**: Django 5.x, Django REST Framework, PyJWT (RS256), `cryptography`,
`requests`. **Nuevas previstas**: una biblioteca de detección de tipo por bytes mágicos para US7
(ver `research.md`).

**Storage**: Apache Pinot (operacional, vía Kafka) · ClickHouse (analítica, vía Airflow) ·
Redis (sesiones). Sin ORM ni Postgres de negocio.

**Testing**: pytest + pytest-django, markers de `.specify/docs/architecture/testing.md`. Playwright
para E2E. Fixtures `mock_pinot`, `mock_kafka`, `auth_headers` de `backend/conftest.py`.

**Target Platform**: Linux server (Docker Compose), navegadores modernos.

**Project Type**: Web application (backend Django + frontend Angular) — Opción 2.

**Performance Goals**: no aplica como objetivo propio. Restricción heredada: las verificaciones
añadidas no deben degradar los presupuestos P95 de `testing.md` (`PG-RES-001`).

**Constraints**:
- Las suites nuevas deben correr en el ciclo rápido del CI (`-m unit` / `-m not integration`). Toda
  prueba que necesite infraestructura real va marcada `integration` (lección de `changelog.md` C3).
- **Sin romper contratos OpenAPI publicados.** Partners integra contra esta API; un cambio de código
  de respuesta es un breaking change. La resolución de #51 respeta esto: `403` y `404` ya estaban
  declarados.
- El sistema es individual: toda solución debe ser mantenible por una sola persona (Principio VII).

**Scale/Scope**: 11 módulos de backend, 37 contratos OpenAPI, ~4.100 pruebas existentes. La suite
de US1 debe cubrir **todos** los endpoints con identificador, por **dos vías de autenticación**.

**NEEDS CLARIFICATION**: ninguna abierta. Las dos que traía la spec se resolvieron leyendo el
código (ver `research.md` R1 y R2) y la tercera en `decisiones-pendientes.md` #51.

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

### Golden Rule — justificación por las 9 características ISO/IEC 25010:2023

| Característica | Justificación |
|---|---|
| **Security** | Es el objeto entero de esta feature. Cubre confidencialidad (US1, US5), integridad (US3), autenticidad (US3), resistencia a ataques (US4, US6, US7) y trazabilidad (el audit de denegaciones ya existente). |
| **Functional Suitability** | No se altera ninguna capacidad de negocio. Riesgo real: un filtro de tenencia demasiado estricto rompería un caso legítimo. Mitigado por el escenario «el partner accede a lo suyo» y por las 744 pruebas de `apps/partners/`. |
| **Reliability** | Se preserva. US3 introduce una decisión sensible: ante fallo del almacén de sesión, el sistema **deniega** (fail-closed). Eso sacrifica disponibilidad por seguridad y está justificado abajo. |
| **Performance Efficiency** | US1 añade una resolución de pertenencia por petición, ya presente hoy vía `ClienteLookupService`. No se prevé degradación; si aparece, `PG-RES-001` la detecta. |
| **Interaction Capability** | Impacto acotado: un usuario legítimo que se equivoca de identificador recibe una denegación menos explícita. Es el coste aceptado de no filtrar existencia, y **solo afecta a no gestores**. |
| **Compatibility** | Restricción dura: no se rompe ningún contrato OpenAPI. Ver Constraints. |
| **Maintainability** | Prioridad por defecto según la constitución. Se materializa en construir sobre inventarios derivados en vez de listas a mano: una suite que se actualiza sola es la única mantenible por una persona. |
| **Flexibility** | **No aplica.** Esta feature no toca el eje multi-región ni la escalabilidad; no añade ni retira capacidad de crecer. |
| **Safety** | **No aplica directamente.** Ninguna regla de este bloque interviene en la cadena de despacho ni en la clasificación de severidad. ⚠️ Con una salvedad: US1 y US2 **no deben** poder denegar a un operador legítimo durante una emergencia activa. Ver el desempate. |

### Mecanismo de desempate — conflictos documentados

**Conflicto 1 — Seguridad ↔ Idoneidad Funcional (resuelto sin sacrificio).**
Distinguir «no existe» de «no es tuyo» es más claro para el cliente legítimo, y filtra el padrón a
un atacante. Se resolvió **segmentando por actor**: el gestor conserva el diagnóstico preciso, el
resto recibe una respuesta unificada. Ninguna de las dos características se sacrifica.
*Trade-off aceptado:* un Partner de integración que teclea mal un id recibe «no es tuyo» en vez de
«no existe». Impacto: menor claridad diagnóstica para el actor con menos necesidad de ella.
Registrado en `decisiones-pendientes.md` #51 y `changelog.md` C4.

**Conflicto 2 — Seguridad ↔ Fiabilidad (US3, fail-closed).**
Si el almacén de sesión no responde al comprobar una revocación, el sistema puede denegar (seguro)
o conceder (disponible). Se elige **denegar**, por la regla 3 del mecanismo: el caso involucra
datos de identidad sensibles, así que Seguridad puede primar sobre Fiabilidad.
*Trade-off aceptado:* una caída de Redis deja a los usuarios fuera en lugar de dejarlos entrar con
sesiones potencialmente revocadas.
⚠️ **Límite explícito, por Principio IX:** esta regla **no puede aplicarse a la cadena de despacho
de emergencias**. Si Safety entra en juego, Safety gana sobre Security sin excepción. La
implementación de US3 debe dejar por escrito qué endpoints quedan fuera del fail-closed y por qué.
**Esto se decide antes de implementar US3, no durante.**

### Métrica de validación (obligatoria por historia)

| Historia | Sub-característica ISO | Criterio medible |
|---|---|---|
| US1 | Security — Confidencialidad | 100 % de endpoints con identificador cubiertos, en 4 métodos y 2 vías de autenticación |
| US2 | Security — Control de acceso | 0 celdas sin verificar en la matriz rol × endpoint |
| US3 | Security — Autenticidad | 0 de 6 variantes de token manipulado obtienen acceso |
| US4 | Security — Resistencia a ataques | 0 cargas de inyección alteran una consulta o revelan error del motor |
| US5 | Security — Confidencialidad | 0 apariciones de dato personal en logs y respuestas de error |
| US6 | Security — Integridad | 4 de 4 throttles declarados devuelven `429` al superarse |
| US7 | Security — Resistencia a ataques | 100 % de subidas validadas por bytes mágicos |
| US8 | Security — Confidencialidad | 5 cabeceras presentes + CSP en entorno no local |
| US9 | Security — Control de acceso | 0 endpoints de negocio aceptan un token de demo |

**Resultado del gate: PASA.** Sin violaciones que justificar; los dos conflictos están documentados
según exige el mecanismo. La sección *Complexity Tracking* queda vacía a propósito.

---

### Re-evaluación post-diseño (tras Phase 1)

Repetida al terminar `data-model.md`, `contracts/` y `quickstart.md`, como exige el flujo. **Sigue
pasando**, con tres matices que el diseño hizo aparecer y que no estaban en la primera pasada:

1. **Mantenibilidad — riesgo de suite lenta (US2).** 3.510 celdas ejercitadas por HTTP harían el
   ciclo rápido inviable y llevarían a que alguien deje de esperarlo, que es como muere un CI.
   Mitigado interrogando la clase de permiso en vez de la pila HTTP (`research.md` §R6).
   *Trade-off:* se cubre exhaustivamente la **decisión de acceso**, no el camino completo.

2. **Seguridad ↔ Idoneidad Funcional (US7), conflicto nuevo.** El contrato C5 prohíbe revelar qué
   tipo de fichero se detectó realmente, lo que degrada el diagnóstico para el usuario legítimo que
   sube algo equivocado. Prevalece Seguridad por la regla 3 (evidencia fotográfica = dato
   sensible). *Trade-off:* «se esperaba una imagen» en vez de «se detectó un ejecutable».

3. **Safety (US3) — sigue siendo la condición previa.** El diseño no la resuelve: la hace más
   visible. La lista de exclusiones del fail-closed **debe existir antes de codificar US3**, y así
   queda anotado en `research.md` §R5 y en `quickstart.md`. Es el único punto donde el Principio IX
   entra en juego, y es absoluto: Safety gana sobre Security sin excepción.

**Resultado: PASA.** *Complexity Tracking* sigue vacío.

---

## Project Structure

### Documentation (this feature)

```text
specs/Global/Endurecimiento-Seguridad/
├── spec.md              # Especificación (ya existente)
├── plan.md              # Este fichero
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
└── tasks.md             # Phase 2 (/speckit-tasks — NO lo crea este comando)
```

### Source Code (repository root)

```text
backend/
├── core/
│   ├── auth/
│   │   └── permissions.py            # IsAuthenticated401 (existente)
│   ├── seguridad/                    # NUEVO — utilidades transversales
│   │   ├── inventario_rutas.py       #   US1/US2: enumera el enrutador DRF
│   │   ├── enmascarado.py            #   US5: filtro de logging
│   │   └── validacion_archivos.py    #   US7: bytes mágicos
│   ├── jwt_utils.py                  # US3 (existente)
│   └── api/response_envelope.py      # US5 (existente)
├── apps/
│   ├── partners/
│   │   ├── permissions.py            # US1 — resolver_partner_visible (hecho, C4)
│   │   ├── services/                 # US1 — 7 servicios con `not_found` por revisar
│   │   └── throttling.py             # US6 (existente)
│   ├── cuentas_clientes/
│   │   └── authentication.py         # US3 — JWTSessionAuthentication
│   ├── informes_tacticos/            # US4 — filtros dinámicos, ORDER BY
│   ├── informes_estrategicos/        # US4
│   └── ventas_crm/demo_tokens.py     # US9 (existente)
└── tests/
    └── seguridad/                    # NUEVO — suites transversales
        ├── test_aislamiento_tenant.py   # US1
        ├── test_matriz_roles.py         # US2
        ├── test_integridad_jwt.py       # US3
        ├── test_inyeccion.py            # US4
        ├── test_datos_sensibles.py      # US5
        ├── test_throttles.py            # US6
        ├── test_subida_archivos.py      # US7
        └── test_cabeceras.py            # US8

frontend/
└── nginx.conf                        # US8 — cabeceras del lado servidor estático

.github/workflows/ci.yml              # Incorporar la suite al gate (PG-CI-001)
```

**Structure Decision**: Opción 2 (web application), que es la estructura real del repositorio.

Dos decisiones propias de esta feature:

1. **Las suites viven en `backend/tests/seguridad/`, no repartidas por módulo.** Son
   **transversales por definición**: US1 recorre el enrutador entero, US2 la matriz completa de
   roles. Colocarlas dentro de cada app obligaría a duplicar el recorrido y volvería imposible
   afirmar «todos los endpoints están cubiertos» — que es justo el criterio de éxito.
2. **Las utilidades reutilizables van a `core/seguridad/`**, siguiendo la convención ya establecida
   por `core/config/secretos.py` (`PG-CFG-002`): la lógica en `core/`, las pruebas aparte.

⚠️ **Excepción deliberada:** `test_no_enumeracion_partners.py` quedó en
`apps/partners/tests/unit/` (`changelog.md` C4). Prueba el helper concreto de Partners, no el
recorrido transversal. La suite transversal de US1 lo complementará, no lo sustituye.

---

## Complexity Tracking

*Sin entradas: el Constitution Check pasó sin violaciones.*

---

## Orden de ejecución previsto

Derivado de la prioridad de la spec y de las dependencias técnicas:

1. **US1** (P1) — depende de `core/seguridad/inventario_rutas.py`, que también necesita US2.
   Empezar aquí hace que US2 salga casi gratis.
2. **US2** (P1) — reutiliza el inventario.
3. **US3** (P1) — independiente. ⚠️ Requiere decidir antes el alcance del fail-closed.
4. **US5** (P1) — independiente; toca configuración de logging.
5. **US4** (P1) — la más laboriosa: exige inventariar los parámetros de filtro de cada informe.
6. **US6, US7, US8, US9** (P2) — independientes entre sí, cualquier orden.

**Regla heredada de `changelog.md` C3, aplicable a toda prueba nueva de este bloque:** incluir la
fixture que mockea Pinot, o la validación de sesión saldrá a buscar un Pinot real y devolverá `401`
— un fallo que aparenta ser de permisos y cuesta horas de diagnóstico.
