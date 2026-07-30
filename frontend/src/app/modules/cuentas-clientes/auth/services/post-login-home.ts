/**
 * Home path after login by business role.
 * Aligns with NAV_LINKS (sidebar) — Unidad must not land on "Cuentas y clientes".
 */
export function homePathForRoles(roles: string[] | undefined | null): string {
  const set = new Set(roles ?? []);

  if (set.has('Unidad')) {
    return '/despacho/mi-despacho';
  }
  if (set.has('Operador')) {
    return '/accidentes/lista';
  }
  if (set.has('Despacho')) {
    return '/despacho/monitoreo';
  }
  if (set.has('Proveedor')) {
    return '/red-operativa/alta-unidades/catalogo';
  }
  if (set.has('Cliente')) {
    return '/soporte-cliente/mis-tickets';
  }
  if (set.has('Soporte') || set.has('DesarrolladorAPIs')) {
    return '/soporte-cliente/cola';
  }
  if (set.has('DirectorTecnologico')) {
    return '/red-operativa/incorporacion-regional/catalogo';
  }
  if (set.has('DirectorEstrategia')) {
    return '/suscripciones/catalogo-planes';
  }
  if (set.has('Administrador')) {
    return '/cuentas-clientes';
  }
  return '/cuentas-clientes';
}

/** Prefer explicit deep-link returnUrl; otherwise role home (ignore generic cuentas hub). */
export function resolvePostLoginPath(
  roles: string[] | undefined | null,
  returnUrl: string | null,
): string {
  if (returnUrl && returnUrl !== '/' && returnUrl !== '/cuentas-clientes') {
    return returnUrl;
  }
  return homePathForRoles(roles);
}
