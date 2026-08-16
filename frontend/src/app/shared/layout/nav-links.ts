import type { TablerIconName } from '../ui/icon/tabler-icon.component';

export interface NavLink {
  label: string;
  description: string;
  path: string;
  roles: string[];
  icon: TablerIconName;
  group: string;
}

/**
 * Fuente de verdad de qué módulos ve cada rol en el sidebar (design-system /
 * Interaction Capability). Matriz documentada también en
 * `.specify/docs/architecture/module-map.md` § "Matriz rol → navegación UI".
 * Código canónico: este array.
 */
export const NAV_LINKS: NavLink[] = [
  {
    label: 'Prospectos',
    description: 'Listado y workpanel del pipeline comercial',
    path: '/ventas-crm/prospectos',
    roles: ['GerenteVentas', 'GerenteCuentasPublicas', 'Administrador'],
    icon: 'list',
    group: 'Ventas CRM',
  },
  {
    label: 'Pipeline',
    description: 'Tablero por etapa del funnel comercial',
    path: '/ventas-crm/pipeline',
    roles: ['GerenteVentas', 'GerenteCuentasPublicas', 'Administrador'],
    icon: 'dashboard',
    group: 'Ventas CRM',
  },
  {
    label: 'Entrada directa',
    description: 'Alta de cliente sin prospecto previo (solo Admin)',
    path: '/ventas-crm/entrada-directa',
    roles: ['Administrador'],
    icon: 'plus',
    group: 'Ventas CRM',
  },
  {
    label: 'Registrar accidente',
    description: 'Capturar un nuevo accidente en tiempo real',
    path: '/accidentes/registro',
    roles: ['Operador'],
    icon: 'car-crash',
    group: 'Emergencias',
  },
  {
    label: 'Lista de accidentes',
    description: 'Consultar y editar accidentes activos',
    path: '/accidentes/lista',
    roles: ['Operador', 'Tecnico'],
    icon: 'list',
    group: 'Emergencias',
  },
  {
    label: 'Informes de Registro',
    description: 'Volumen, severidad, zona y calidad del registro',
    path: '/emergencias/informes/registro',
    roles: ['Operador', 'Administrador'],
    icon: 'dashboard',
    group: 'Emergencias',
  },
  {
    label: 'Informes de Despacho',
    description: 'Asignación, tiempos de respuesta y ratio demanda/capacidad',
    path: '/emergencias/informes/despacho',
    roles: ['Operador', 'Administrador'],
    icon: 'dashboard',
    group: 'Emergencias',
  },
  {
    label: 'Informes de Seguimiento',
    description: 'Tiempos de cierre, cierres forzados y abortos',
    path: '/emergencias/informes/seguimiento',
    roles: ['Operador', 'Administrador'],
    icon: 'dashboard',
    group: 'Emergencias',
  },
  {
    label: 'Mi despacho',
    description: 'Despachos asignados a mi unidad',
    path: '/despacho/mi-despacho',
    roles: ['Unidad'],
    icon: 'radio',
    group: 'Despacho',
  },
  {
    label: 'Monitoreo de despacho',
    description: 'Asignación y seguimiento de unidades',
    path: '/despacho/monitoreo',
    roles: ['Operador', 'Despacho'],
    icon: 'radio',
    group: 'Despacho',
  },
  {
    label: 'Parámetros del algoritmo',
    description: 'Configuración del despacho inteligente',
    path: '/despacho/parametros',
    roles: ['DirectorTecnologico', 'Administrador'],
    icon: 'settings',
    group: 'Despacho',
  },
  {
    label: 'Mapa de seguimiento',
    description: 'Seguimiento GPS de unidades en curso',
    path: '/seguimiento/mapa',
    roles: ['Operador', 'Despacho'],
    icon: 'map',
    group: 'Seguimiento',
  },
  {
    label: 'Mi seguimiento',
    description: 'Seguimiento de mi despacho activo',
    path: '/seguimiento/mi-seguimiento',
    roles: ['Unidad'],
    icon: 'map',
    group: 'Seguimiento',
  },
  {
    label: 'Historial de emergencias',
    description: 'Casos cerrados y su expediente',
    path: '/seguimiento/historial',
    roles: ['Operador', 'Despacho'],
    icon: 'history',
    group: 'Seguimiento',
  },
  {
    label: 'Mis expedientes',
    description: 'Historial de casos como cliente',
    path: '/seguimiento/expedientes',
    roles: ['Cliente'],
    icon: 'history',
    group: 'Seguimiento',
  },
  {
    label: 'Disponibilidad de unidad',
    description: 'Marcar disponibilidad y ver flota',
    path: '/evidencia-unidad/disponibilidad',
    roles: ['Unidad'],
    icon: 'camera',
    group: 'Evidencia y flota',
  },
  {
    label: 'Flota',
    description: 'Administración de unidades de emergencia',
    path: '/evidencia-unidad/flota',
    roles: ['Despacho'],
    icon: 'camera',
    group: 'Evidencia y flota',
  },
  {
    label: 'Mis unidades',
    description: 'Alta, edición y baja de la flota del proveedor',
    path: '/red-operativa/alta-unidades/catalogo',
    roles: ['Cliente', 'Proveedor'],
    icon: 'car',
    group: 'Red operativa',
  },
  {
    label: 'Regiones operativas',
    description: 'Catálogo, validación y reevaluación de regiones',
    path: '/red-operativa/incorporacion-regional/catalogo',
    roles: ['Administrador', 'DirectorTecnologico'],
    icon: 'map',
    group: 'Red operativa',
  },
  {
    label: 'Validación de región',
    description: 'Protocolo de onboarding y remediación de regiones',
    path: '/red-operativa/incorporacion-regional/validacion',
    roles: ['Administrador', 'DirectorTecnologico'],
    icon: 'map-pin',
    group: 'Red operativa',
  },
  {
    label: 'Gestión de cuenta',
    description: 'Usuarios, roles y perfil corporativo de clientes',
    path: '/cuentas-clientes/gestion-cuenta',
    roles: ['Administrador'],
    icon: 'settings',
    group: 'Administración',
  },
  {
    label: 'Informes de cuentas',
    description: 'Listados tácticos de cuentas, incorporación, usuarios y accesos',
    path: '/cuentas-clientes/informes',
    // El Director Tecnológico ve el índice porque desde ahí llega a accesos
    // técnicos, el único que le corresponde; el índice le oculta los otros siete.
    roles: ['Administrador', 'DirectorTecnologico'],
    icon: 'chart-bar',
    group: 'Administración',
  },
  {
    label: 'Informes de soporte',
    description: 'Cola de tickets y escalados del período',
    // El Cliente entra: ve **sus** tickets, y el aviso de alcance de la
    // respuesta se lo dice. Los escalados los filtra el índice y los cierra su
    // propio guard.
    //
    // ⚠️ `PartnerIntegracion` **no está aquí**, y no es un descuido: FR-UI-033
    // dice que la consola de Partners y su portal no se fusionan, y que ningún
    // rol descubre la existencia del otro departamento. Darle una entrada en el
    // grupo «Soporte» rompería esa regla.
    //
    // El backend **sí** le permite el listado —puede abrir una disputa de
    // facturación, y ve solo sus tickets—, así que la ruta le responde si llega
    // a ella. Lo que no tiene es un enlace. Queda anotado como decisión de
    // producto, no resuelto por conveniencia.
    path: '/soporte-cliente/informes',
    roles: [
      'Soporte',
      'Administrador',
      'DesarrolladorAPIs',
      'DirectorTecnologico',
      'GerenteExitoCliente',
      'Cliente',
    ],
    icon: 'chart-bar',
    group: 'Soporte',
  },
  {
    label: 'Solicitudes de cliente',
    description: 'Aprobar, rechazar o anular autorregistros',
    path: '/cuentas-clientes/incorporacion-clientes/solicitudes',
    roles: ['Administrador'],
    icon: 'list',
    group: 'Administración',
  },
  {
    label: 'Mis tickets',
    description: 'Reportar y dar seguimiento a incidencias',
    path: '/soporte-cliente/mis-tickets',
    roles: ['Cliente'],
    icon: 'list',
    group: 'Soporte',
  },
  {
    label: 'Cola de soporte',
    description: 'Tickets pendientes de atención',
    path: '/soporte-cliente/cola',
    roles: ['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico'],
    icon: 'list',
    group: 'Soporte',
  },
  {
    label: 'Dashboard de soporte',
    description: 'Métricas de tickets y cumplimiento de SLA',
    path: '/soporte-cliente/dashboard',
    roles: ['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico'],
    icon: 'dashboard',
    group: 'Soporte',
  },
  {
    label: 'Configuración de SLA',
    description: 'Reglas de tiempos de respuesta y resolución por plan',
    path: '/soporte-cliente/configuracion-sla',
    roles: ['Administrador'],
    icon: 'settings',
    group: 'Soporte',
  },
  {
    label: 'Mi suscripción',
    description: 'Estado del plan, acceso y cancelación',
    path: '/suscripciones/mi-suscripcion',
    roles: ['Cliente', 'Proveedor'],
    icon: 'history',
    group: 'Suscripciones',
  },
  {
    label: 'Métodos de pago',
    description: 'Registrar o actualizar medio de cobro',
    path: '/suscripciones/metodos-pago',
    roles: ['Cliente', 'Proveedor'],
    icon: 'settings',
    group: 'Suscripciones',
  },
  {
    label: 'Historial de facturas',
    description: 'Consultar facturas emitidas y cobros',
    path: '/suscripciones/historial-facturas',
    roles: ['Cliente', 'Proveedor'],
    icon: 'list',
    group: 'Suscripciones',
  },
  {
    label: 'Catálogo de planes',
    description: 'Ver planes activos y límites',
    path: '/suscripciones/catalogo-planes',
    roles: ['Cliente', 'Proveedor', 'Administrador', 'DirectorEstrategia'],
    icon: 'dashboard',
    group: 'Suscripciones',
  },
  {
    label: 'Aprobaciones de plan',
    description: 'Aprobar o rechazar downgrades pendientes',
    path: '/suscripciones/aprobaciones-downgrade',
    roles: ['Administrador'],
    icon: 'circle-check',
    group: 'Suscripciones',
  },

  // --- Partners y API ---
  // Dos superficies de departamentos distintos: los sidebars NO se fusionan
  // (design-system § 5). El partner nunca ve la consola y viceversa.
  {
    label: 'Partners',
    description: 'Incorporar partners y asignarles su plan de acceso',
    path: '/partners/consola',
    roles: ['Administrador', 'DesarrolladorAPIs'],
    icon: 'license',
    group: 'Partners y API',
  },
  {
    label: 'Solicitudes pendientes',
    description: 'Aprobar o rechazar el paso a producción',
    path: '/partners/consola/solicitudes',
    roles: ['Administrador', 'DesarrolladorAPIs'],
    icon: 'clock',
    group: 'Partners y API',
  },
  {
    label: 'Mi integración',
    description: 'Tu estado, tu cupo y tus credenciales de API',
    path: '/partners/portal',
    roles: ['PartnerIntegracion'],
    icon: 'key',
    group: 'Partners y API',
  },
  {
    label: 'Registros de API',
    description: 'Detalle de cada llamada, con filtros y autodiagnóstico',
    path: '/partners/consola/logs',
    roles: ['Administrador', 'DesarrolladorAPIs'],
    icon: 'list',
    group: 'Partners y API',
  },
  {
    label: 'Reporte de consumo',
    description: 'Consumo mensual, comparable entre períodos',
    path: '/partners/consola/reportes',
    roles: ['Administrador', 'DesarrolladorAPIs'],
    icon: 'chart-bar',
    group: 'Partners y API',
  },
  {
    // Solo Administrador: es una cola de decisiones de negocio, no de
    // plataforma. El DesarrolladorAPIs no la ve en su sidebar.
    label: 'Excepciones de facturación',
    description: 'Excedente que no se pudo facturar y espera acción',
    path: '/partners/consola/excepciones',
    roles: ['Administrador'],
    icon: 'report-money',
    group: 'Partners y API',
  },
  {
    // Solo Administrador: la reactivación de un partner es competencia suya
    // (RN-PAC-009) y el sistema nunca la ejecuta por su cuenta.
    label: 'Suspensiones de partners',
    description: 'Suspendidos y en mora; suspender y reactivar',
    path: '/partners/consola/suspensiones',
    roles: ['Administrador'],
    icon: 'license',
    group: 'Partners y API',
  },
  {
    label: 'Mi consumo',
    description: 'Tu consumo del período y tu excedente estimado',
    path: '/partners/portal/consumo',
    roles: ['PartnerIntegracion'],
    icon: 'chart-bar',
    group: 'Partners y API',
  },
  {
    label: 'Contrato de integración',
    description: 'Versión vigente y versiones soportadas por servicio',
    path: '/partners/portal/contrato',
    roles: ['PartnerIntegracion'],
    icon: 'license',
    group: 'Partners y API',
  },
];
