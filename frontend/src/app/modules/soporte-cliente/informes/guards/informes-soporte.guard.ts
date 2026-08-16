/**
 * Acceso a los informes tácticos de Soporte al Cliente.
 *
 * ⚠️ **La asimetría del departamento.** `tickets` lo ven quienes atienden **y**
 * quienes reportan; `escalados`, **solo** quienes atienden — un escalado es
 * proceso interno del equipo de atención, no información que el reportador
 * necesite sobre su propio ticket.
 *
 * Un guard único con la unión borraría esa distinción y le daría los escalados
 * al Cliente.
 *
 * ⚠️ **Y el guard no decide qué filas se ven.** Abre la puerta a los dos grupos
 * en `tickets`; que un reportador quede acotado a los suyos lo decide el
 * backend. Intentar adivinarlo aquí duplicaría una regla que ya costó una
 * corrección en el módulo operativo: el acotamiento se decide por **no tener
 * ningún rol de atención**, no por tener uno concreto de reporte.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

/** Quien atiende tickets. `GerenteExitoCliente` es la autoridad del departamento. */
const ROLES_ATENCION = [
  'Soporte',
  'Administrador',
  'DesarrolladorAPIs',
  'DirectorTecnologico',
  'GerenteExitoCliente',
];

/** Quien reporta. El Partner está aquí por la disputa de facturación. */
const ROLES_REPORTADORES = ['Cliente', 'PartnerIntegracion'];

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

export const informesTicketsGuard: CanActivateFn = guardDeRoles([
  ...ROLES_ATENCION,
  ...ROLES_REPORTADORES,
]);

export const informesEscaladosGuard: CanActivateFn = guardDeRoles(ROLES_ATENCION);

/** Expuestos para que la prueba compare contra el permiso del backend. */
export const ROLES_INFORMES_ATENCION = ROLES_ATENCION;
export const ROLES_INFORMES_REPORTADORES = ROLES_REPORTADORES;
