import { Routes } from '@angular/router';

import { clienteExpedienteGuard } from './guards/cliente-expediente.guard';
import { operadorSeguimientoGuard } from './guards/operador-seguimiento.guard';
import { unidadSeguimientoGuard } from './guards/unidad-seguimiento.guard';

export const SEGUIMIENTO_ROUTES: Routes = [
  {
    path: 'mapa',
    canActivate: [operadorSeguimientoGuard],
    loadComponent: () =>
      import('./pages/mapa-seguimiento/mapa-seguimiento.page').then((m) => m.MapaSeguimientoPage),
  },
  {
    path: 'mi-seguimiento',
    canActivate: [unidadSeguimientoGuard],
    loadComponent: () =>
      import('./pages/mi-seguimiento/mi-seguimiento.page').then((m) => m.MiSeguimientoPage),
  },
  {
    path: 'historial',
    canActivate: [operadorSeguimientoGuard],
    loadComponent: () =>
      import('./pages/historial-emergencias/historial-emergencias.page').then(
        (m) => m.HistorialEmergenciasPage,
      ),
  },
  {
    path: 'expedientes',
    canActivate: [clienteExpedienteGuard],
    loadComponent: () =>
      import('./pages/detalle-expediente/detalle-expediente.page').then(
        (m) => m.DetalleExpedientePage,
      ),
  },
  {
    path: 'expedientes/:idaccidente',
    canActivate: [clienteExpedienteGuard],
    loadComponent: () =>
      import('./pages/detalle-expediente/detalle-expediente.page').then(
        (m) => m.DetalleExpedientePage,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'mapa' },
];
