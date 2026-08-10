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

## Actores tácticos/estratégicos (fuera de alcance — no incluidos en los 89 CU operativos)

| Actor                        | Descripción                                                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Gerente                      | Consulta resultados estratégicos, rentabilidad, indicadores, y toma decisiones de largo plazo.                    |
| Director Tecnológico         | Define arquitectura técnica, gestiona infraestructura cloud, modelos de precios de API y SLA de uptime.           |
| Director de Operaciones      | Supervisa operaciones diarias de despacho, mide eficiencia operativa y gestiona turnos de soporte.                |
| Director de Datos            | Diseña la estrategia de datos, modelos predictivos, dashboards de inteligencia y calidad de datos.                |
| Director de Expansión        | Diseña el playbook de implementación para nuevas ciudades/regiones y gestiona el proceso de expansión.            |
| Director de Producto         | Mide el Time-to-Market de nuevas funcionalidades y gestiona el roadmap de producto.                               |
| Director Financiero          | Gestiona presupuesto, costos de infraestructura e inversión en I+D.                                               |
| Director de RRHH             | Capacita personal, gestiona rotación de personal clave y fortalece la cultura organizacional.                     |
| Director de Marketing        | Planea y ejecuta campañas de marketing B2B, genera contenido de generación de leads y gestiona presencia digital. |
| Gerente de Éxito del Cliente | Gestiona satisfacción, retención y reuniones de revisión de negocio (QBR) con clientes clave.                     |
| Legal                        | Crea plantillas de contrato para integraciones API y gestiona aspectos legales.                                   |
| Director Comercial 🆕         | Dirige la estrategia del pipeline comercial y la conversión de prospectos a cliente; supervisa el desempeño del embudo de Ventas y CRM (Pre-venta) y el aprovechamiento comercial de las señales de intención captadas en la demo interactiva. |

> Nota: si en el futuro se decide implementar specs tácticos o estratégicos, estos actores pasarían a la sección de "operativos" y los specs correspondientes deberían añadirse al `module-map.md`.

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
| Táctico | Gerente de Éxito del Cliente |

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
| Táctico | Director Comercial 🆕 |

### Transversales (no atados a un solo departamento)
| Nivel | Actor | Por qué es transversal |
|---|---|---|
| Operativo | Administrador | Ejecuta CU de alta/configuración en cuentas, usuarios, roles, sesiones y red operativa. No incluye catálogo de planes (Director de Estrategia). |
| Operativo | Analista de Datos | Genera reportes e inteligencia que cruzan varios departamentos, no uno solo. |
| Operativo | Desarrollador de APIs | Integraciones técnicas externas, no ligadas a un paquete de negocio específico. |
| Operativo | Partner de integración 🆕 | Actúa **solo sobre su propio perfil** en Partners y API (`idrol` 15, `PartnerIntegracion`). No es transversal: se lista aquí para dejar clara su separación del rol Cliente y del Desarrollador de APIs. |
| Operativo | Sistema (actor automatizado) | Ejecuta procesos automáticos de varios módulos (despacho, facturación, notificaciones). |
| Operativo | Proveedor 🆕 | Pertenece al módulo Marketplace-Proveedores, fuera de los 6 paquetes actuales. |
| Táctico | Gerente | Visión estratégica de toda la empresa, no de un departamento puntual. |
| Táctico | Director de Datos | Estrategia de datos transversal a todos los módulos. |
| Táctico | Director de Expansión | Estrategia de crecimiento geográfico general, complementaria a Red Operativa pero no ejecutora directa de sus CU. |
| Táctico | Director de Producto | Roadmap de producto, cruza todos los paquetes. |
| Táctico | Director de RRHH | Gestión de personal, no ligada a un paquete de negocio. |
| Táctico | Director de Marketing | Generación de demanda, relacionado con Ventas y CRM pero con alcance propio más amplio. |
| Táctico | Legal | Aspectos legales y contractuales de toda la empresa. |

**Nota sobre Director Tecnológico:** se asignó como responsable táctico de Red Operativa por ser el actor que efectivamente ejecuta las decisiones de validación/despublicación de región en los CU documentados (`ConfiguracionRedOperativa.md`), aunque su descripción general también cubre arquitectura técnica transversal a todo el sistema.
