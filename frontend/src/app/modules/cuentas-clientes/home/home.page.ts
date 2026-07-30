import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../auth/services/auth-api.service';

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [RouterLink, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './home.page.html',
})
export class HomePage {
  private readonly auth = inject(AuthApiService);

  readonly profile = this.auth.getProfile();

  esAdmin(): boolean {
    return this.auth.hasRole('Administrador');
  }

  esCliente(): boolean {
    return this.auth.hasRole('Cliente');
  }

  esUnidad(): boolean {
    return this.auth.hasRole('Unidad');
  }

  esOperador(): boolean {
    return this.auth.hasRole('Operador');
  }

  esSoporte(): boolean {
    return this.auth.hasAnyRole([
      'Soporte',
      'DesarrolladorAPIs',
      'DirectorTecnologico',
      'Administrador',
    ]);
  }

  tituloHub(): string {
    if (this.esUnidad()) return 'Unidad de emergencia';
    if (this.esOperador()) return 'Operaciones de emergencia';
    return 'Cuentas y clientes';
  }
}
