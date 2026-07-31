import { Routes } from '@angular/router';

import { proveedorFlotaGuard } from './guards/proveedor-flota.guard';
import { CatalogoPage } from './pages/catalogo/catalogo.page';
import { DetallePage } from './pages/detalle/detalle.page';
import { FormularioPage } from './pages/formulario/formulario.page';

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
        path: 'detalle/:idunidademergencia',
        component: DetallePage,
        canActivate: [proveedorFlotaGuard],
      },
      {
        path: 'nueva',
        component: FormularioPage,
        canActivate: [proveedorFlotaGuard],
        data: { mode: 'create' },
      },
      {
        path: 'editar/:idunidademergencia',
        component: FormularioPage,
        canActivate: [proveedorFlotaGuard],
        data: { mode: 'edit' },
      },
      {
        path: 'baja/:idunidademergencia',
        redirectTo: 'catalogo',
        pathMatch: 'full',
      },
      { path: '', redirectTo: 'catalogo', pathMatch: 'full' },
    ],
  },
];
