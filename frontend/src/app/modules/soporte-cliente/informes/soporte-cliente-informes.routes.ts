/**
 * Rutas de los informes tácticos de Soporte al Cliente.
 *
 * ⚠️ `escalados` va **antes** de la ruta genérica y con su propio guard: es el
 * único restringido a roles de atención. Con la genérica primero, Angular
 * aplicaría el guard permisivo y un reportador entraría a un listado que es
 * proceso interno del equipo. Como su `path` es literal, el identificador viaja
 * por `data` en vez de por el parámetro de ruta.
 *
 * El índice usa el guard permisivo —no muestra datos, solo enlaces— y filtra por
 * rol lo que ofrece.
 */

import { Routes } from '@angular/router';

import { INFORME_ESCALADOS } from './definiciones/informes-soporte.definiciones';
import { informesEscaladosGuard, informesTicketsGuard } from './guards/informes-soporte.guard';

export const SOPORTE_CLIENTE_INFORMES_ROUTES: Routes = [
  {
    path: '',
    canActivate: [informesTicketsGuard],
    loadComponent: () =>
      import('./pages/indice/indice-informes.page').then((m) => m.IndiceInformesSoportePage),
  },
  {
    path: INFORME_ESCALADOS,
    canActivate: [informesEscaladosGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeSoportePage),
    data: { informe: INFORME_ESCALADOS },
  },
  {
    path: ':informe',
    canActivate: [informesTicketsGuard],
    loadComponent: () =>
      import('./pages/informe/informe.page').then((m) => m.InformeSoportePage),
  },
];
