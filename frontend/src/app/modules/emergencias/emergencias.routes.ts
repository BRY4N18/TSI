import { Routes } from '@angular/router';

import { emergenciasInformesGuard } from './guards/emergencias-informes.guard';

export const EMERGENCIAS_ROUTES: Routes = [
  {
    path: 'informes/registro',
    canActivate: [emergenciasInformesGuard],
    loadComponent: () =>
      import('./pages/workpanel-registro/workpanel-registro.page').then(
        (m) => m.WorkpanelRegistroPage,
      ),
  },
  {
    path: 'informes/despacho',
    canActivate: [emergenciasInformesGuard],
    loadComponent: () =>
      import('./pages/workpanel-despacho/workpanel-despacho.page').then(
        (m) => m.WorkpanelDespachoPage,
      ),
  },
  {
    path: 'informes/seguimiento',
    canActivate: [emergenciasInformesGuard],
    loadComponent: () =>
      import('./pages/workpanel-seguimiento/workpanel-seguimiento.page').then(
        (m) => m.WorkpanelSeguimientoPage,
      ),
  },
];
