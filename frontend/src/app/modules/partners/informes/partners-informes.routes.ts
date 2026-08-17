/**
 * Rutas de los informes tácticos de Partners y API.
 *
 * ⚠️ Las dos de contrato van **antes** de la genérica y con su propio guard.
 * Con `:informe` primero, Angular aplicaría el guard de acceso y un Partner
 * entraría a versiones y alcance. Como su `path` es literal, el identificador
 * viaja por `data`.
 *
 * El índice usa el guard amplio: no muestra datos, solo enlaces, y filtra por rol.
 */

import { Routes } from '@angular/router';

import { INFORMES_CONTRATO } from './definiciones/informes-partners.definiciones';
import { informesAccesoGuard, informesContratoGuard } from './guards/informes-partners.guard';

export const PARTNERS_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesAccesoGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesPartnersPage),
  },
  {
    path: INFORMES_CONTRATO[0],
    canActivate: [informesContratoGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformePartnersPage),
    data: { informe: INFORMES_CONTRATO[0] },
  },
  {
    path: INFORMES_CONTRATO[1],
    canActivate: [informesContratoGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformePartnersPage),
    data: { informe: INFORMES_CONTRATO[1] },
  },
  {
    path: ':informe',
    canActivate: [informesAccesoGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformePartnersPage),
  },
];
