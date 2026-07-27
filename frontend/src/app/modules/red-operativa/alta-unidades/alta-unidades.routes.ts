import { Routes } from '@angular/router';

import { proveedorFlotaGuard } from './guards/proveedor-flota.guard';
import { BajaPage } from './pages/baja/baja.page';
import { CatalogoPage } from './pages/catalogo/catalogo.page';
import { EdicionPage } from './pages/edicion/edicion.page';

export const ALTA_UNIDADES_ROUTES: Routes = [
  {
    path: '',
    children: [
      {
        path: 'catalogo',
        component: CatalogoPage,
        canActivate: [proveedorFlotaGuard],
      },
      {
        path: 'editar/:idunidademergencia',
        component: EdicionPage,
        canActivate: [proveedorFlotaGuard],
      },
      {
        path: 'baja/:idunidademergencia',
        component: BajaPage,
        canActivate: [proveedorFlotaGuard],
      },
      { path: '', redirectTo: 'catalogo', pathMatch: 'full' },
    ],
  },
];
