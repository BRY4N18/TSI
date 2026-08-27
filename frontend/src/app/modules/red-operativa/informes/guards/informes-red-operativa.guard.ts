/**
 * Acceso a los informes tácticos de Red Operativa.
 *
 * **Tres grupos, no uno**, y cada corte tiene su motivo:
 *
 * | Listado | Quién |
 * |---|---|
 * | Flota y bajas | Administrador, Expansión **y los roles de cuenta proveedora** |
 * | Regiones | Administrador, Expansión y Tecnológico — **sin proveedores** |
 * | Validaciones | Administrador y **solo** Tecnológico |
 *
 * ⚠️ **Una región no pertenece a ninguna empresa de flota.** Su estado es
 * materia de gobierno de la red, no información que un proveedor deba ver: por
 * eso los proveedores quedan fuera de regiones aunque sí entren a su flota.
 *
 * ⚠️ **Las validaciones son solo del Tecnológico.** Él fija los criterios; el
 * detalle de por qué se rechaza una región no le sirve a quien decide dónde
 * crecer.
 *
 * Y el guard **no decide qué filas se ven**: un proveedor entra a flota y el
 * backend lo acota a la suya.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

const ROLES_ACOTADOS = ['Cliente', 'Proveedor'];
const AMPLIOS_FLOTA = ['Administrador', 'DirectorExpansion'];
const AMPLIOS_REGION = ['Administrador', 'DirectorTecnologico', 'DirectorExpansion'];
const AMPLIOS_VALIDACION = ['Administrador', 'DirectorTecnologico'];

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

export const informesFlotaGuard: CanActivateFn = guardDeRoles([
  ...AMPLIOS_FLOTA,
  ...ROLES_ACOTADOS,
]);

export const informesRegionesGuard: CanActivateFn = guardDeRoles(AMPLIOS_REGION);

export const informesValidacionesGuard: CanActivateFn = guardDeRoles(AMPLIOS_VALIDACION);

/**
 * Guard del índice: la unión de los tres grupos, no solo el de flota.
 *
 * El índice no muestra datos, solo enlaces a lo que cada rol puede abrir —
 * pero `DirectorTecnologico` no está en `AMPLIOS_FLOTA` (solo en región y
 * validación), así que reusar `informesFlotaGuard` aquí lo dejaba fuera del
 * índice aunque sí pudiera entrar directo a `/regiones` y
 * `/validaciones-region`: el enlace del menú (`nav-links.ts`) apuntaba a un
 * índice que él no podía abrir.
 */
export const informesIndiceGuard: CanActivateFn = guardDeRoles([
  ...AMPLIOS_FLOTA,
  ...ROLES_ACOTADOS,
  ...AMPLIOS_REGION,
  ...AMPLIOS_VALIDACION,
]);

export function listadosVisiblesPara(tieneRol: (rol: string) => boolean): string[] {
  const visibles: string[] = [];
  if ([...AMPLIOS_FLOTA, ...ROLES_ACOTADOS].some(tieneRol)) {
    visibles.push('flota', 'bajas-unidad');
  }
  if (AMPLIOS_REGION.some(tieneRol)) {
    visibles.push('regiones');
  }
  if (AMPLIOS_VALIDACION.some(tieneRol)) {
    visibles.push('validaciones-region');
  }
  return visibles;
}

export const ROLES_AMPLIOS_FLOTA = AMPLIOS_FLOTA;
export const ROLES_AMPLIOS_REGION = AMPLIOS_REGION;
export const ROLES_AMPLIOS_VALIDACION = AMPLIOS_VALIDACION;
export const ROLES_INFORMES_ACOTADOS = ROLES_ACOTADOS;
