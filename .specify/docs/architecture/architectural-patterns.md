# Patrones Arquitectónicos — TSI
**Ubicación de este archivo:** `docs/arquitectura/patrones-arquitectonicos.md`
**Última actualización:** 2026-07-20

> Decisiones de arquitectura fijas del proyecto. No son principios de gobernanza (eso vive en la constitution) — son el "cómo" técnico que ya se decidió y no se vuelve a discutir spec por spec.

---

## 1. Estilo arquitectónico: API-First REST + Capas + Event-Driven

```
Angular (presentación / interacción)
    ↓  HTTP (JSON) — queries y comandos
Django REST Framework (controllers / views)
    ↓
Django Services (lógica de negocio / casos de uso)
    ↓
Django Repositories (única capa de acceso a datos)
    │
    ├── ESCRITURA → Kafka (topic por tabla) → Apache Pinot ingiere en tiempo real
    │   (regla vinculante: ningún repositorio escribe directo a Pinot, ver infrastructure.md sección 4)
    │
    └── LECTURA → Apache Pinot (SQL directo vía Broker, solo lectura)
```

**Nota:** Pinot es de solo lectura desde Django. El único canal de escritura de datos de dominio es Kafka — esta regla es vinculante y está definida en `infrastructure.md` (sección 4). Un repositorio que ejecute un `INSERT`/`UPDATE` directo contra Pinot viola esta regla, sin excepción.

Los flujos del camino crítico (registro de accidente → validación → asignación → despacho → tracking) usan un patrón **Event-Driven** asíncrono: cada paso publica un evento interno que el siguiente consumidor procesa, sin acoplar módulos entre sí.

El módulo `ml/` opera fuera del ciclo HTTP. Los modelos entrenados se consumen desde `inteligencia/` mediante queries a tablas de resultados precomputados en Pinot, o mediante llamadas a servicios de ML independientes.

---

## 2. Principios de diseño

### SOLID (aplicado a Django Services / Angular Services)

| Principio | Regla | Ejemplo en TSI |
|---|---|---|
| **S** — Responsabilidad Única | Cada servicio Django/Angular hace una sola cosa de dominio. Si necesitas usar "y" para describir qué hace una clase, son dos clases. | `DispatchService` asigna unidades; no clasifica severidad (eso es `SeverityService`) ni calcula facturación (eso es `BillingService`). |
| **O** — Abierto/Cerrado | Una clase se extiende sin modificar su código ya probado. Nuevas variantes de una regla se agregan como una implementación nueva, no como un `if/elif` más largo dentro del servicio existente. | Si aparece una tercera forma de calcular prioridad de despacho (además de distancia y tier de proveedor, ver `MarketplaceProveedores.md`), se agrega una nueva estrategia de ranking — no se le agrega un `if es_proveedor_marketplace` más al método `calcular_prioridad()` ya existente. |
| **L** — Sustitución de Liskov | Si un servicio/repositorio implementa una interfaz o hereda de una base, debe poder reemplazar a esa base sin romper al que la usa. | Cualquier repositorio en `core/repositories/` que herede de `BaseRepository` debe poder ser inyectado donde se espera `BaseRepository` sin que el caller necesite saber si es Pinot, un mock de test, u otra fuente — mismo contrato, mismo comportamiento esperado (paginación, manejo de "no encontrado", etc.). |
| **I** — Segregación de Interfaces | No fuerces a una clase a depender de métodos que no usa. Interfaces/servicios pequeños y específicos, no un "god service" con 20 métodos donde cada consumidor solo usa 2. | `NotificacionService` (en `core/notificaciones/`) se divide por canal (`EmailNotifier`, `SMSNotifier`, `PushNotifier`) en vez de un único servicio con todos los métodos de todos los canales — `soporte_cliente/` solo depende de lo que realmente envía. |
| **D** — Inversión de Dependencias | Los módulos de alto nivel (services) no dependen de detalles de bajo nivel (Pinot, Kafka); ambos dependen de una abstracción (`core/repositories/`). Las vistas dependen de servicios, los servicios de repositorios — nunca al revés. | `AccidenteService.registrar()` depende de la interfaz `AccidenteRepository`, no de un cliente de Kafka o Pinot hardcodeado — así el repositorio real se puede sustituir por un fake en tests sin tocar el servicio. |

> **📌 Recomendación técnica (no aplicada aún al código):** el principio **L (Liskov)** hoy es más una disciplina que algo que el lenguaje fuerce, porque `BaseRepository` en `core/repositories/` no es una interfaz formal declarada. Para que Liskov sea verificable y no solo una buena intención, se recomienda convertir `BaseRepository` en una `ABC` (Abstract Base Class) de Python con métodos abstractos explícitos (`get()`, `list()`, `create()`, etc.) — así cualquier repositorio concreto que no implemente el contrato completo falla en tiempo de definición de la clase, no en producción. Esto es una mejora recomendada, pendiente de aplicar; no es retroactiva a los repositorios ya existentes hasta que se decida abordarla explícitamente.

### Reglas complementarias

| Principio | Explicación |
|---|---|
| Inyección de dependencias en Angular | Todo acceso a datos o al canal de tiempo real (SSE) pasa por un servicio inyectado, nunca hardcodeado en el componente. |
| No repetir lógica de dominio | Si una regla de negocio (ej. criterio de severidad crítica) aparece en más de un lugar, se extrae a un servicio compartido en `core/`. |
| Componentes Angular sin lógica de negocio | Los componentes solo manejan presentación y eventos de usuario. La lógica va en el servicio correspondiente. |
| Repositorios como única capa de acceso a datos | Ninguna vista, servicio o componente externo ejecuta SQL crudo. Todo pasa por repositorios en `core/`. |
| Django como gateway exclusivo a Pinot | Angular y cualquier consumidor externo solo acceden a datos vía la API REST de Django. Sin conexiones directas a Pinot desde el frontend o terceros. |

**Regla general:** un import directo entre apps es aceptable únicamente cuando es vocabulario puro (constantes/enums que respaldan una tabla, sin lógica ejecutable) entre apps del mismo módulo de negocio según `module-map.md` (ej. `apps.accidentes.domain_constants` importado desde `despacho/`, ambas partes del módulo Emergencias). Cualquier servicio, clase con comportamiento, o llamada que ejecute lógica pertenece a `core/` si más de un módulo de negocio lo necesita — nunca se importa directo entre apps de distintos módulos. Ejemplos ya aplicados de este patrón: `core/notificaciones/` (envío de email/SMS/push), `core/auth/` (permisos/autenticación, usado por todas las apps), `core/audit/` (trazabilidad de acceso, Principio V, usado por `accidentes` y `despacho`). Fuera de esos dos casos (vocabulario intra-módulo, o comportamiento ya extraído a `core/`), ningún módulo llama a otro módulo de Django directamente — la comunicación entre módulos de negocio distintos ocurre exclusivamente vía Kafka. Las lecturas de datos ocurren exclusivamente a través de repositorios en `core/`.

---

## 3. RBAC — Roles múltiples sin herencia (actores tácticos y operativos)

**Decisión:** cuando una misma persona necesita más de un rol del sistema (ej. es Director de Operaciones y además opera como Operador de Emergencias), **no se implementa herencia de permisos entre roles**. El rol "Director de Operaciones" no incluye automáticamente los permisos de "Operador" ni de "Técnico de Campo", y viceversa.

**Mecanismo:** se resuelve asignando **múltiples filas a esa persona en `Dim_Usuario_Rol`** (tabla puente muchos-a-muchos, ver `GestionCuentasClientes.md` CU-O63). Cada rol conserva su propio conjunto de permisos, íntegro e independiente — el rol sigue siendo el permiso (regla ya definida en `GestionCuentasClientes.md`), simplemente una persona puede tener más de uno.

**Por qué no herencia:**
- El rol es una definición general ("todo Director de Operaciones puede X"), no una decisión por persona. Si los permisos operativos se hornean dentro del rol táctico, todo Director de Operaciones los heredaría siempre, incluso quien nunca deba operar directamente — la asignación multi-rol deja esa decisión a nivel de persona, no de rol.
- Mantiene la auditoría limpia: cada acción queda ligada al rol específico con el que se ejecutó (`Fact_Session`, `idusuario` en las tablas de hecho correspondientes), sin ambigüedad de "¿esto lo hizo como director o como operador?".
- Es consistente con la regla de sidebar por rol de `design-system.md` (sección 5): cada rol mantiene su propio sidebar; con multi-rol, el comportamiento del sidebar (fusión vs. selector explícito) depende de si los roles pertenecen al mismo departamento o a departamentos distintos — detalle de interfaz definido en `design-system.md`, no en este documento.

**Alcance actual:** la mayoría de actores tácticos/estratégicos (Director de Operaciones, Director Comercial, etc.) siguen fuera de los CU operativos implementados (ver `actors.md`). **Excepción incorporada (2026-07-30):** **Director de Estrategia** es actor **operativo** con rol JWT `DirectorEstrategia` y ejecuta RF-SUSF-001 (catálogo `Dim_Plan`) en Suscripciones-Facturación; no implica herencia de permisos de Administrador ni de otros roles (sigue el mecanismo multi-fila `Dim_Usuario_Rol` de esta sección). El resto de tácticos permanece fuera de alcance hasta que se incorporen formalmente a `Dim_Rol`.



