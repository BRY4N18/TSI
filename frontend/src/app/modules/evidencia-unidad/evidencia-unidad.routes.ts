import { Routes } from '@angular/router';

import { administradorFlotaGuard } from './guards/administrador-flota.guard';
import { evidenciaGalleryGuard } from './guards/evidencia-gallery.guard';
import { unidadEmergenciaDisponibilidadGuard } from './guards/unidad-emergencia-disponibilidad.guard';

export const EVIDENCIA_UNIDAD_ROUTES: Routes = [
  {
    path: 'disponibilidad',
    canActivate: [unidadEmergenciaDisponibilidadGuard],
    loadComponent: () =>
      import('./pages/panel-disponibilidad/panel-disponibilidad.page').then(
        (m) => m.PanelDisponibilidadPage,
      ),
  },
  {
    path: 'accidentes/:idaccidente/galeria',
    canActivate: [evidenciaGalleryGuard],
    loadComponent: () =>
      import('./pages/galeria-evidencias/galeria-evidencias.page').then(
        (m) => m.GaleriaEvidenciasPage,
      ),
  },
  {
    path: 'flota',
    canActivate: [administradorFlotaGuard],
    loadComponent: () =>
      import('./pages/panel-disponibilidad/panel-disponibilidad.page').then(
        (m) => m.PanelDisponibilidadPage,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'disponibilidad' },
];
