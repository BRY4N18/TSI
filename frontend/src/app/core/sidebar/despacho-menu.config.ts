export interface DespachoMenuItem {
  label: string;
  route: string;
  roles: string[];
}

export const DESPACHO_MENU: DespachoMenuItem[] = [
  {
    label: 'Monitoreo despacho',
    route: '/despacho/monitoreo/ACC-EVI-TEST-1',
    roles: ['Operador', 'Despacho', 'Administrador'],
  },
  {
    label: 'Asignación manual',
    route: '/despacho/asignacion/ACC-EVI-TEST-1',
    roles: ['Operador', 'Despacho', 'Administrador'],
  },
  {
    label: 'Mi despacho',
    route: '/despacho/mi-despacho',
    roles: ['Unidad'],
  },
  {
    label: 'Parámetros algoritmo',
    route: '/despacho/parametros',
    roles: ['DirectorTecnologico', 'Administrador'],
  },
];

export function despachoMenuForRoles(roles: string[]): DespachoMenuItem[] {
  const roleSet = new Set(roles);
  return DESPACHO_MENU.filter((item) => item.roles.some((role) => roleSet.has(role)));
}
