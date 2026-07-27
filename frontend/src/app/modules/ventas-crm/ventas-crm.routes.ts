import { Routes } from '@angular/router';

import { adminCrmGuard } from './guards/admin-crm.guard';
import { adminOGerenteCrmGuard } from './guards/admin-o-gerente-crm.guard';

export const VENTAS_CRM_ROUTES: Routes = [
  {
    path: 'planes',
    loadComponent: () =>
      import('./pages/catalogo-planes/catalogo-planes.page').then((m) => m.CatalogoPlanesPage),
  },
  {
    path: 'registro',
    loadComponent: () =>
      import('./pages/registro-publico/registro-publico.page').then((m) => m.RegistroPublicoPage),
  },
  {
    path: 'demo',
    loadComponent: () =>
      import('./pages/demo-interactiva/demo-interactiva.page').then((m) => m.DemoInteractivaPage),
  },
  {
    path: 'notificaciones',
    canActivate: [adminOGerenteCrmGuard],
    loadComponent: () =>
      import('./pages/notificaciones-ventas/notificaciones-ventas.page').then(
        (m) => m.NotificacionesVentasPage,
      ),
  },
  {
    path: 'prospectos',
    canActivate: [adminOGerenteCrmGuard],
    loadComponent: () =>
      import('./pages/listado-prospectos/listado-prospectos.page').then(
        (m) => m.ListadoProspectosPage,
      ),
  },
  {
    path: 'prospectos/:idprospecto',
    canActivate: [adminOGerenteCrmGuard],
    loadComponent: () =>
      import('./pages/detalle-prospecto/detalle-prospecto.page').then((m) => m.DetalleProspectoPage),
  },
  {
    path: 'pipeline',
    canActivate: [adminOGerenteCrmGuard],
    loadComponent: () =>
      import('./pages/pipeline-board/pipeline-board.page').then((m) => m.PipelineBoardPage),
  },
  {
    path: 'entrada-directa',
    canActivate: [adminCrmGuard],
    loadComponent: () =>
      import('./pages/entrada-directa/entrada-directa.page').then((m) => m.EntradaDirectaPage),
  },
  { path: '', pathMatch: 'full', redirectTo: 'prospectos' },
];
