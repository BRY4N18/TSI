# Actores del Sistema — TSI

**Ubicación de este archivo:** `docs/actores.md`
**Última actualización:** 2026-07-30

> Catálogo completo de actores. Marcados según si participan en los 98 CU operativos (alcance actual de implementación — 89 originales + 9 de Marketplace-Proveedores) o son tácticos/estratégicos (fuera de alcance, documentados solo por completitud y trazabilidad con el BSC del proyecto).

---

## Actores operativos (dentro del alcance actual)

| Actor                           | Descripción                                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Administrador                   | Gestiona cuentas de clientes, usuarios, roles, sesiones y unidades de la red operativa. No gestiona el catálogo de planes ni pricing (ver Director de Estrategia). |
| Operador de Emergencias         | Registra accidentes en tiempo real, coordina el despacho de unidades y da seguimiento a casos activos.                             |
| Técnico de Campo                | Realiza verificación en sitio, reporta evidencia fotográfica y confirma el estado de emergencias atendidas.                        |
| Unidad de Emergencia            | Recibe el despacho del operador, confirma atención en sitio y reporta el estado de la emergencia (en tránsito, atendido, cerrado). |
| Analista de Datos               | Genera reportes de siniestralidad, mapas de calor, modelos predictivos y dashboards de inteligencia de mercado.                    |
| Desarrollador de APIs           | Equipo técnico **de TSI**: registra partners, les asigna el plan de acceso y vigila consumo y errores (SRS L124). **No** es quien consume la API — eso es el Partner de integración. |
| Partner de integración 🆕       | **Área técnica de un cliente integrador** (SRS L121). Obtiene y rota sus credenciales, solicita el paso a producción y consulta su propio consumo. Pertenece a un Cliente, pero es una persona distinta con permisos distintos: el Cliente titular gestiona plan, facturas y tickets; el partner solo gestiona credenciales. |
| Soporte al Cliente              | Atiende solicitudes de clientes, resuelve incidencias técnicas, gestiona reclamos y da seguimiento a necesidades.                  |
| Cliente (aseguradora/municipio) | Consulta reportes de siniestralidad, recibe alertas, accede a APIs, visualiza dashboards y gestiona su suscripción.                |
| Gerente de Ventas               | Gestiona el pipeline comercial y el seguimiento de prospectos.                                                                     |
| Gerente de Cuentas Públicas     | Gestiona alianzas con municipios, convenios de cooperación y demos para el sector público.                                         |
| Proveedor 🆕                    | Empresa de asistencia vial (grúas, ambulancias privadas) que se suscribe al Marketplace de Proveedores para vincular sus unidades externas y recibir priorización de leads en casos de baja severidad. |
| Director de Estrategia          | Gestiona el catálogo de planes de suscripción (crear, editar, desactivar `Dim_Plan`: nombre, precio, límites, nivel, activo). Rol JWT canónico: `DirectorEstrategia`. Pricing dinámico por región queda fuera de v1 (ver RF-SUSF-001). |
| Sistema (actor automatizado)    | Ejecuta procesos automáticos: asignación de despacho, facturación, renovaciones, validaciones, re-entrenamiento de modelos.        |

## Autoridades departamentales (capa táctica — **implementadas**) 🆕

> **Actualizado 2026-08-14.** Estos actores **dejan de estar fuera de alcance**: los informes
> tácticos de `specs/002-tactico/` los tienen como destinatarios. La asignación exacta de qué informe
> ve cada uno vive en [`specs/002-tactico/acceso-tactico.md`](../../specs/002-tactico/acceso-tactico.md).
>
> **Autoridad de esta tabla: el §5.1 del SRS** (`informestacticos/TSI-SRS-Especificacion-de-Requisitos.md`),
> que es la fuente decidida ante discrepancias.

| Actor | Rol JWT canónico | Autoridad del departamento | Descripción |
| --- | --- | --- | --- |
| Director de Marketing        | `DirectorMarketing`   | **Ventas y CRM** | Fija los criterios del embudo comercial y la captación digital. Supervisa carteras de todos los ejecutivos, sin acotamiento. |
| Director de Estrategia       | `DirectorEstrategia`  | **Suscripciones** *(catálogo y precios)* | Decide qué planes existen y a qué precio. Ya existía como actor operativo; suma la autoridad sobre composición de cartera y movimientos de plan. |
| Director Financiero          | `DirectorFinanciero`  | **Suscripciones** *(resultado económico)* | Responde por la facturación, el cobro y la mora. |
| Director Tecnológico         | `DirectorTecnologico` | **Partners y API** · **Red Operativa** *(validación de regiones)* · **Cuentas** *(solo capa de accesos técnicos)* | ⚠️ En Cuentas y Clientes su alcance es **únicamente** la capa de accesos técnicos, no el departamento (§5.1). |
| Director de Expansión        | `DirectorExpansion`   | **Red Operativa** *(crecimiento)* | Decide dónde crecer; supervisa flota y bajas. |
| Director de Operaciones      | `DirectorOperaciones` | **Emergencias** | Supervisa casos, despachos, evidencia y cierres. Sujeto a las mismas exclusiones de dato sensible que cualquier otro rol. |
| Gerente de Éxito del Cliente | `GerenteExitoCliente` | **Soporte al Cliente** | Fija los criterios de atención y supervisa el cumplimiento de compromisos. **No es** `SupervisorSoporte`, que es el destinatario operativo de un escalado automático. |
| Director de Datos            | `DirectorDatos`       | **Analítica e Inteligencia** | Se aplicará cuando ese módulo se especifique. |

> **Cuentas y Clientes no tiene autoridad de negocio.** El §5.1 solo le asigna el Director
> Tecnológico, con alcance limitado a accesos técnicos. Sus informes de altas, incorporación, ciclo
> de vida y sesiones quedan bajo el Administrador, que es a la vez su responsable operativo.
> Anotado en `decisiones-pendientes.md`.

---

## Autoridad estratégica (capa estratégica — **en alcance**) 🆕

> **Añadido 2026-08-16.** Los informes estratégicos de `specs/001-estrategico/` se reparten entre las
> autoridades departamentales de la tabla anterior, según la regla de
> [`acceso-estrategico.md`](../../specs/001-estrategico/acceso-estrategico.md) §1: *un informe lo ve la
> autoridad del departamento dueño del dato que mide*. El §13.1 del marco asigna «Alta Dirección» a
> los diez CU-E, pero eso describe el nivel de la decisión, no el permiso de lectura.

| Actor | Rol JWT canónico | Autoridad de | Descripción |
| --- | --- | --- | --- |
| Gerente | `Gerente` | **El tablero estratégico integral** — los 76 informes de OE1–OE6 | Único rol transversal de la capa estratégica. Existe porque CU-E01 (tablero integral), CU-E09 (escenarios de expansión) y CU-E10 (reporte gerencial) **cruzan los seis objetivos por construcción**: sin él, esos tres casos de uso no son ejecutables por nadie. **No es un grupo que acumule directores** — cada director entra por su departamento. |

> ⚠️ **`Gerente` no está sembrado todavía.** Falta crearlo en `Dim_Rol` y en
> `backend/core/auth/roles_tacticos.py`, junto con los seis roles tácticos que siguen pendientes.

---

## Actores estratégicos (fuera de alcance — no incluidos en los 89 CU operativos)

| Actor                        | Descripción                                                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Director de Producto         | Mide el Time-to-Market de nuevas funcionalidades y gestiona el roadmap de producto.                               |
| Director de RRHH             | Capacita personal, gestiona rotación de personal clave y fortalece la cultura organizacional.                     |
| Legal                        | Crea plantillas de contrato para integraciones API y gestiona aspectos legales.                                   |

> **`Director Comercial` retirado (2026-08-14).** Lo introdujo una spec de Ventas y CRM como
> autoridad de ese departamento, pero el §5.1 del SRS asigna esa autoridad al **Director de
> Marketing**. Ante la discrepancia se decidió que manda el SRS, así que el rol correcto es
> `DirectorMarketing` y `Director Comercial` deja de existir.

---

## Actores por Departamento

> Agrupación de referencia por los 6 paquetes implementados (`module-map.md`), para responder de un vistazo "quién participa en cada departamento" — combina actores operativos y tácticos ya listados arriba, sin redefinirlos. Un actor puede tener más de un rol asignado en `Dim_Usuario_Rol` (ver `architectural-patterns.md`, sección 3); esta tabla no implica que un mismo usuario tenga automáticamente todos los roles de su departamento, solo agrupa cuáles existen dentro de cada uno.

### Gestión de Emergencias
| Nivel | Actor |
|---|---|
| Operativo | Operador de Emergencias |
| Operativo | Técnico de Campo |
| Operativo | Unidad de Emergencia |
| Táctico | Director de Operaciones |

### Gestión de Cuentas y Clientes
| Nivel | Actor |
|---|---|
| Operativo | Cliente (aseguradora/municipio) |
| Operativo | Administrador *(responsable operativo del departamento, §5.1)* |
| Táctico | Director Tecnológico — ⚠️ **solo la capa de accesos técnicos**, no el departamento |

> **Corregido 2026-08-14.** Decía «Gerente de Éxito del Cliente»; el §5.1 del SRS asigna a este
> departamento el Director Tecnológico con alcance limitado. El Gerente de Éxito del Cliente es la
> autoridad de **Soporte al Cliente**, no de este.

### Gestión de Red Operativa
| Nivel | Actor |
|---|---|
| Táctico | Director Tecnológico |

### Gestión de Soporte al Cliente
| Nivel | Actor |
|---|---|
| Operativo | Soporte al Cliente |
| Táctico | Gerente de Éxito del Cliente |

### Gestión de Suscripciones y Facturación
| Nivel | Actor |
|---|---|
| Operativo | Director de Estrategia |
| Operativo | Proveedor / Cliente (suscripción propia) |
| Operativo | Administrador (aprobaciones de downgrade y consulta de facturación; no catálogo de planes) |
| Táctico | Director Financiero |

### Gestión de Ventas y CRM (Pre-venta)
| Nivel | Actor |
|---|---|
| Operativo | Gerente de Ventas |
| Operativo | Gerente de Cuentas Públicas |
| Táctico | **Director de Marketing** |

> **Corregido 2026-08-14.** Decía «Director Comercial», rol que este documento introdujo por su
> cuenta. El §5.1 del SRS asigna la autoridad de Ventas y CRM al **Director de Marketing**, y ante la
> discrepancia se decidió que manda el SRS.

### Transversales (no atados a un solo departamento)
| Nivel | Actor | Por qué es transversal |
|---|---|---|
| Operativo | Administrador | Ejecuta CU de alta/configuración en cuentas, usuarios, roles, sesiones y red operativa. No incluye catálogo de planes (Director de Estrategia). |
| Operativo | Analista de Datos | Genera reportes e inteligencia que cruzan varios departamentos, no uno solo. |
| Operativo | Desarrollador de APIs | Integraciones técnicas externas, no ligadas a un paquete de negocio específico. |
| Operativo | Partner de integración 🆕 | Actúa **solo sobre su propio perfil** en Partners y API (`idrol` 15, `PartnerIntegracion`). No es transversal: se lista aquí para dejar clara su separación del rol Cliente y del Desarrollador de APIs. |
| Operativo | Sistema (actor automatizado) | Ejecuta procesos automáticos de varios módulos (despacho, facturación, notificaciones). |
| Operativo | Proveedor 🆕 | Pertenece al módulo Marketplace-Proveedores, fuera de los 6 paquetes actuales. |
| **Estratégico** 🆕 | Gerente | Visión estratégica de toda la empresa, no de un departamento puntual. Es el único rol que abarca los seis OE (`acceso-estrategico.md` §2). |
| Táctico | Director de Datos | Estrategia de datos transversal a todos los módulos. |
| Táctico | Director de Expansión | Estrategia de crecimiento geográfico general, complementaria a Red Operativa pero no ejecutora directa de sus CU. |
| Táctico | Director de Producto | Roadmap de producto, cruza todos los paquetes. |
| Táctico | Director de RRHH | Gestión de personal, no ligada a un paquete de negocio. |
| Táctico | Director de Marketing | Generación de demanda, relacionado con Ventas y CRM pero con alcance propio más amplio. |
| Táctico | Legal | Aspectos legales y contractuales de toda la empresa. |

**Nota sobre Director Tecnológico:** se asignó como responsable táctico de Red Operativa por ser el actor que efectivamente ejecuta las decisiones de validación/despublicación de región en los CU documentados (`ConfiguracionRedOperativa.md`), aunque su descripción general también cubre arquitectura técnica transversal a todo el sistema.
