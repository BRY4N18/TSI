/**
 * Acceso a los informes tácticos **simples** de Emergencias.
 *
 * Vive aparte de `emergencias-informes.guard.ts`, que protege los workpanels de
 * los informes **agregados**: son dos módulos con roles distintos, y unificarlos
 * mezclaría el acceso a dos cosas que el catálogo separa.
 *
 * ⚠️ **`casos` admite al Cliente; los otros cuatro, no.** El cliente ve los
 * casos **cerrados de sus zonas contratadas** — el backend lo acota—, pero
 * despachos, evidencia y cierres son operación interna.
 *
 * ⚠️ **`PartnerIntegracion` no entra a ninguno.** El acceso programático a los
 * datos de siniestralidad tiene su propio camino, con su alcance y su auditoría
 * (`consumo_datos_service`). Dejarlo entrar por el listado táctico duplicaría
 * ese control con otro que no lo audita.
 *
 * Y como siempre: **el guard abre la puerta, no decide qué filas se ven.**
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

/** Quien opera el sistema por dentro. `DirectorOperaciones` es la autoridad. */
const ROLES_INTERNOS = ['Operador', 'Tecnico', 'Administrador', 'DirectorOperaciones'];

/** Acotado a sus zonas contratadas y a los casos ya cerrados. */
const ROLES_CLIENTE = ['Cliente'];

function guardDeRoles(roles: string[]): CanActivateFn {
  return () => {
    const authApi = inject(AuthApiService);
    const router = inject(Router);

    if (!authApi.isAuthenticated()) {
      return router.createUrlTree(['/cuentas-clientes/auth/login']);
    }
    if (!roles.some((rol) => authApi.hasRole(rol))) {
      return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
    }
    return true;
  };
}

export const informesCasosGuard: CanActivateFn = guardDeRoles([
  ...ROLES_INTERNOS,
  ...ROLES_CLIENTE,
]);

export const informesEmergenciasInternoGuard: CanActivateFn = guardDeRoles(ROLES_INTERNOS);

/** Expuestos para que la prueba compare contra el permiso del backend. */
export const ROLES_INTERNOS_EMERGENCIAS = ROLES_INTERNOS;
export const ROLES_CLIENTE_EMERGENCIAS = ROLES_CLIENTE;
