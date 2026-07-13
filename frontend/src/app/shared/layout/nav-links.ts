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
 * Fuente de verdad de qué módulos ve cada rol en el sidebar (design-system.md
 * §5 "Regla de sidebar por rol"). El contenido concreto rol→módulo todavía no
 * vive en `.specify/docs/architecture/module-map.md` (ese doc solo cubre
 * spec→CU→tablas), así que este array sigue siendo la única fuente hasta que
 * se documente ahí.
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
    label: 'Gestión de cuenta',
    description: 'Administrar usuarios, roles y accesos',
    path: '/cuentas-clientes/gestion-cuenta',
    roles: ['Administrador'],
    icon: 'settings',
    group: 'Administración',
  },
];
