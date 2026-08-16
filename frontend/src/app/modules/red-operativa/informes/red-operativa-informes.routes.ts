/**
 * Rutas de los informes tácticos de red-operativa.
 *
 * ⚠️ **Tres grupos.** Una región no pertenece a ninguna empresa de flota, así que
 * `regiones` y `validaciones-region` van antes de la genérica con su guard
 * propio: el genérico admite proveedores, y el estado de la red no es
 * información suya.
 *
 * El índice usa el guard más permisivo —no muestra datos, solo enlaces— y filtra
 * por rol lo que ofrece.
 */

import { Routes } from '@angular/router';

import {
  informesFlotaGuard,
  informesRegionesGuard,
  informesValidacionesGuard,
} from './guards/informes-red-operativa.guard';

export const RED_OPERATIVA_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesFlotaGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesRedOperativaPage),
  },
  {
    path: 'regiones',
    canActivate: [informesRegionesGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeRedOperativaPage),
    data: { informe: 'regiones' },
  },
  {
    path: 'validaciones-region',
    canActivate: [informesValidacionesGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeRedOperativaPage),
    data: { informe: 'validaciones-region' },
  },
  {
    path: ':informe',
    canActivate: [informesFlotaGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeRedOperativaPage),
  },
];
