/**
 * Rutas de los informes tácticos de ventas-crm.
 *
 * ⚠️ `reasignaciones` va **antes** de la ruta genérica y con su propio guard: es
 * supervisión pura, y el guard genérico —que admite a los gerentes— se la daría
 * a quien no debe verla. Como su `path` es literal, el identificador viaja por
 * `data`.
 *
 * El índice usa el guard más permisivo —no muestra datos, solo enlaces— y filtra
 * por rol lo que ofrece.
 */

import { Routes } from '@angular/router';

import {
  informesReasignacionesGuard,
  informesVentasGuard,
} from './guards/informes-ventas-crm.guard';

export const VENTAS_CRM_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesVentasGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesVentasPage),
  },
  {
    path: 'reasignaciones',
    canActivate: [informesReasignacionesGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeVentasPage),
    data: { informe: 'reasignaciones' },
  },
  {
    path: ':informe',
    canActivate: [informesVentasGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeVentasPage),
  },
];
