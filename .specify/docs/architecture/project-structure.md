# Estructura del Proyecto — TSI
**Ubicación de este archivo:** `docs/arquitectura/estructura-proyecto.md`
**Última actualización:** 2026-07-20

> Organización de carpetas del código. Cambia conforme se agregan módulos — actualizar aquí cuando se cree una carpeta nueva.

---

## Regla de organización

**1 app de Django = 1 módulo de negocio, sin excepciones.** Cada carpeta bajo `apps/` corresponde exactamente a un módulo documentado en `module-map.md`, con el mismo nombre normalizado a snake_case. `core/` **no** es una excepción a esta regla porque no es un módulo de negocio — es infraestructura transversal, por eso vive fuera de `apps/`, como hermano directo.

**Excepción explícita y justificada — Emergencias:** `accidentes/` y `despacho/` son dos apps separadas dentro del mismo módulo Emergencias. No es una mezcla de dominios (ambas cosas SÍ son Emergencias), es una separación por complejidad real: el registro de accidentes y el despacho N-N (`Fact_Despacho` ↔ múltiples unidades) tienen ciclos de vida, actores y volumen de eventos distintos. Mismo criterio aplicado a Analítica-ML (`reportes/` + `inteligencia/`), que mapea 1:1 a sus dos specs.

**Orden del árbol:** las apps están listadas siguiendo el "Orden de implementación sugerido" de `module-map.md` (orden de dependencias), no alfabético — así el árbol se navega con el mismo mapa mental que el resto de la documentación.

**Acceso a datos — sin excepción:** ninguna app habla directo con Pinot/Kafka. Todo pasa por `core/repositories/` (ver `architectural-patterns.md` e `infrastructure.md` sección 4). Las apps con lecturas complejas pueden tener un `queries.py` que **compone** llamadas a `core/repositories/`, nunca que las reemplaza.

---

## Backend

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py                  → Rutas raíz, monta /api/v1/ de cada app
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── cuentas_clientes/        → Módulo Cuentas-Clientes: auth, RBAC, onboarding, gestión de cuenta
│   ├── ventas_crm/              → Módulo Ventas-CRM: pipeline comercial, prospectos, notificación a ventas
│   ├── suscripciones/           → Módulo Suscripciones-Facturación: planes, facturación, cobro, dunning
│   ├── apis_integraciones/      → Módulo Partners-API: onboarding de partners, monitoreo/facturación de API
│   ├── infraestructura/         → Módulo Infraestructura: resiliencia, uptime, monitoreo
│   ├── red_operativa/           → Módulo Red-Operativa: alta de unidades, onboarding de región
│   ├── accidentes/              → Módulo Emergencias (parte 1): registro y validación de accidentes
│   ├── despacho/                → Módulo Emergencias (parte 2): asignación de unidades, tracking (SSE)
│   ├── soporte_cliente/         → Módulo Soporte-Cliente: tickets, SLA, escalado
│   ├── reportes/                → Módulo Analítica-ML (parte 1): tasas de siniestralidad, exportación
│   ├── inteligencia/            → Módulo Analítica-ML (parte 2): consumo de resultados de ML, calidad de datos
│   ├── marketplace_proveedores/ → 🆕 Módulo Marketplace-Proveedores: registro/aprobación de proveedores, vinculación de unidades externas, leads por severidad baja, suscripción de visibilidad (reutiliza suscripciones/)
│   └── bsc/                     → ⚠️ FUERA DE ALCANCE ACTUAL — Dashboard de KPIs estratégicos. No respaldado por ningún CU de los 98 operativos (ver actors.md). No implementar hasta que se decida llevar a alcance operativo.
├── core/                        → Infraestructura transversal, NO es un módulo de negocio (hermano de apps/, nunca hijo)
│   ├── auth/                    → Permisos/autenticación compartidos (ej. IsAuthenticated401), usados por todas las apps — espejo de frontend/app/core/auth/
│   ├── audit/                   → Servicios de auditoría/trazabilidad (Principio V) compartidos entre módulos, ej. AuditEvidenciaService (usado por accidentes y despacho)
│   ├── notificaciones/          → Despacho de email/SMS/push, usado por ventas_crm, soporte_cliente, despacho, suscripciones
│   └── repositories/            → ÚNICA capa de acceso a datos (Pinot/Kafka). Repositorios base, mixins, utils, middleware compartido
├── ml/                          → Scripts de entrenamiento ML (fuera del ciclo request/response), consumido por apps/inteligencia/
└── manage.py
```

### Estructura interna de una app (ejemplo — `apps/accidentes/`)

```
apps/accidentes/
├── __init__.py
├── apps.py
├── models.py         → Dataclasses tipadas de las tablas Dim_/Fact_ relevantes (sin ORM, sin validación, sin lógica — solo forma del dato)
├── serializers.py     → CAPA DE DTO: validación de entrada/salida (DRF)
├── services.py         → CAPA DE NEGOCIO: casos de uso que mutan estado (ej. registrar accidente → publica evento Kafka)
├── views.py            → CAPA DE PRESENTACIÓN: recibe requests, delega a services.py, retorna responses (DRF)
├── urls.py             → Rutas de esta app, montadas en config/urls.py
└── queries.py          → OPCIONAL, solo si hay lecturas complejas: compone llamadas a core/repositories/, nunca SQL directo
```

`queries.py` es opcional y solo se agrega en apps con lecturas genuinamente complejas (`despacho/`, `reportes/`, `inteligencia/`). Apps mayormente CRUD (`cuentas_clientes/`, `soporte_cliente/`) no lo necesitan — `services.py` llama directo a `core/repositories/`.

**Ejemplo de `models.py` (dataclass, no Django ORM ni Pydantic):**

```python
from dataclasses import dataclass

@dataclass
class FactAccidente:
    idaccidente: str
    idseveridad: int
    idcalle: int
    activo: bool
    fecha_actualizacion: int  # epoch ms, ver data-model.md
```

---

## Frontend

```
frontend/
└── src/
    ├── assets/                  → Logos, íconos Tabler, recursos estáticos
    ├── styles/                  → Estilos globales y tokens de design-system.md
    ├── app/
    │   ├── core/                → Lógica global y conexión a Django
    │   │   ├── auth/            → RoleGuard, AuthService, manejo de JWT
    │   │   ├── http/            → Interceptor para inyectar token en cada petición
    │   │   └── models/          → Interfaces globales (Usuario, Roles)
    │   ├── shared/               → UI genérica y "tonta"
    │   │   ├── components/       → ui-button, ui-modal, ui-alert, etc.
    │   │   └── pipes/            → currency-format, date-format, etc.
    │   ├── layouts/               → Shell único con sidebar-por-rol (design-system.md v4), NO un layout distinto por actor
    │   │   ├── main-layout/       → Header + sidebar (240px, colapsa en mobile) + slot de contenido; el sidebar renderiza ítems según rol vía RoleGuard
    │   │   └── auth-layout/       → Pantalla limpia solo para login (sin sidebar)
    │   ├── modules/                → Un módulo Angular por app de Django, alineación 1:1 estricta
    │   │   ├── cuentas-clientes/
    │   │   ├── ventas-crm/
    │   │   ├── suscripciones/
    │   │   ├── apis-integraciones/
    │   │   ├── infraestructura/
    │   │   ├── red-operativa/
    │   │   ├── accidentes/
    │   │   ├── despacho/
    │   │   ├── soporte-cliente/
    │   │   ├── reportes/
    │   │   ├── inteligencia/
    │   │   └── marketplace-proveedores/  → 🆕 (bsc/ sigue sin módulo frontend hasta que entre a alcance operativo)
    │   ├── app.routes.ts           → Une layouts (actor) con modules (negocio)
    │   └── app.config.ts
    └── main.ts
```

Cada módulo de negocio sigue internamente la misma lógica de capas del ejemplo del backend, adaptada a Angular:

```
modules/accidentes/
├── components/       → Presentación, sin lógica de negocio
├── services/          → Llama a la API de Django, maneja el canal SSE si aplica
└── accidentes.routes.ts
```

---

## Tabla de equivalencia de nombres

| Módulo (`module-map.md`) | App Django (`apps/`) | Módulo Angular (`modules/`) |
|---|---|---|
| Cuentas-Clientes | `cuentas_clientes` | `cuentas-clientes` |
| Ventas-CRM | `ventas_crm` | `ventas-crm` |
| Suscripciones-Facturación | `suscripciones` | `suscripciones` |
| Partners-API | `apis_integraciones` | `apis-integraciones` |
| Infraestructura | `infraestructura` | `infraestructura` |
| Red-Operativa | `red_operativa` | `red-operativa` |
| Emergencias | `accidentes` + `despacho` | `accidentes` + `despacho` |
| Soporte-Cliente | `soporte_cliente` | `soporte-cliente` |
| Analítica-ML | `reportes` + `inteligencia` | `reportes` + `inteligencia` |
| Marketplace-Proveedores 🆕 | `marketplace_proveedores` | `marketplace-proveedores` |
| — (fuera de alcance) | `bsc` | *(sin módulo frontend aún)* |

---

**Convención:** un app de Django por módulo de negocio, nombres en plural o snake_case consistente con el nombre del módulo en `module-map.md`. Un módulo Angular por app de Django — alineación 1:1 estricta, en kebab-case.

**Relación con specs de Spec Kit:** cada carpeta de módulo en `specs/003-operational/` mapea exactamente a un `apps/` de este árbol — mismo nombre normalizado. Si un spec nuevo no calza en un app existente, se crea un app nuevo.

**Módulos en capas (003-operational):** los módulos operativos usan `specs/.../{modulo}/{backend|frontend}/` más un índice `{modulo}.md` (no README). Speckit apunta `feature.json` a **una capa** (backend primero). Crear con `create-new-feature.ps1 -Layered`.
