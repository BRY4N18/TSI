import { Routes } from '@angular/router';

import { ventasCrmGestionGuard } from './guards/ventas-crm-gestion.guard';

export const VENTAS_CRM_GESTION_ROUTES: Routes = [
  {
    path: 'embudo',
    canActivate: [ventasCrmGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'captacion',
    canActivate: [ventasCrmGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
  {
    path: 'nutricion',
    canActivate: [ventasCrmGestionGuard],
    loadComponent: () =>
      import('./pages/pantalla-z.page').then((m) => m.PantallaZPage),
  },
];
