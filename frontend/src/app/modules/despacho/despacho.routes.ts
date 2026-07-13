import { Routes } from '@angular/router';

import { directorTecnologicoGuard } from './guards/director-tecnologico.guard';
import { operadorDespachoGuard } from './guards/operador-despacho.guard';
import { unidadDespachoGuard } from './guards/unidad-despacho.guard';

export const DESPACHO_ROUTES: Routes = [
  {
    path: 'monitoreo',
    canActivate: [operadorDespachoGuard],
    loadComponent: () =>
      import('./pages/lista-monitoreo/lista-monitoreo.page').then((m) => m.ListaMonitoreoPage),
  },
  {
    path: 'monitoreo/:idaccidente',
    canActivate: [operadorDespachoGuard],
    loadComponent: () =>
      import('./pages/monitoreo-despacho/monitoreo-despacho.page').then(
        (m) => m.MonitoreoDespachoPage,
      ),
  },
  {
    path: 'asignacion/:idaccidente',
    canActivate: [operadorDespachoGuard],
    loadComponent: () =>
      import('./pages/asignacion-manual/asignacion-manual.page').then(
        (m) => m.AsignacionManualPage,
      ),
  },
  {
    path: 'mi-despacho',
    canActivate: [unidadDespachoGuard],
    loadComponent: () =>
      import('./pages/mi-despacho/mi-despacho.page').then((m) => m.MiDespachoPage),
  },
  {
    path: 'parametros',
    canActivate: [directorTecnologicoGuard],
    loadComponent: () =>
      import('./pages/parametros-algoritmo/parametros-algoritmo.page').then(
        (m) => m.ParametrosAlgoritmoPage,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'mi-despacho' },
];
