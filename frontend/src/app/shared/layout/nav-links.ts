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
    label: 'Registrar accidente',
    description: 'Capturar un nuevo accidente en tiempo real',
    path: '/accidentes/registro',
    roles: ['Operador', 'Administrador'],
    icon: 'car-crash',
    group: 'Emergencias',
  },
  {
    label: 'Lista de accidentes',
    description: 'Consultar y editar accidentes activos',
    path: '/accidentes/lista',
    roles: ['Operador', 'Tecnico', 'Administrador'],
    icon: 'list',
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
    roles: ['Operador', 'Despacho', 'Administrador'],
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
    roles: ['Operador', 'Despacho', 'Administrador'],
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
    roles: ['Operador', 'Despacho', 'Administrador'],
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
    roles: ['Administrador', 'Despacho'],
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
    roles: ['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico', 'Administrador'],
    icon: 'list',
    group: 'Soporte',
  },
  {
    label: 'Dashboard de soporte',
    description: 'Métricas de tickets y cumplimiento de SLA',
    path: '/soporte-cliente/dashboard',
    roles: ['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico', 'Administrador'],
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
];
