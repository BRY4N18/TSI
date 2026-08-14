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

/**
 * Destino de la incorporación guiada cuando la cuenta la tiene pendiente.
 *
 * El SRS §3.2.2 dice que el sistema **lleva** al cliente a su siguiente paso
 * pendiente, no que él lo busque: antes el asistente solo se alcanzaba
 * escribiendo la URL, así que la incorporación no llegaba a ocurrir nunca.
 */
export function onboardingPathForCuenta(
  cuenta: { idcliente: number; onboardingPendiente: boolean } | null | undefined,
): string | null {
  if (!cuenta?.onboardingPendiente) {
    return null;
  }
  return `/cuentas-clientes/incorporacion-clientes/${cuenta.idcliente}/onboarding`;
}

/** Prefer explicit deep-link returnUrl; otherwise role home (ignore generic cuentas hub). */
export function resolvePostLoginPath(
  roles: string[] | undefined | null,
  returnUrl: string | null,
  cuenta?: { idcliente: number; onboardingPendiente: boolean } | null,
): string {
  if (returnUrl && returnUrl !== '/' && returnUrl !== '/cuentas-clientes') {
    return returnUrl;
  }
  // La incorporación pendiente manda sobre el home del rol: hasta completarla,
  // la cuenta no está lista para operar.
  return onboardingPathForCuenta(cuenta) ?? homePathForRoles(roles);
}
