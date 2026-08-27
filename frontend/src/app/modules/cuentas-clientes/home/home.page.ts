import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { NodePatternComponent } from '../../../shared/brand/node-pattern.component';
import { TablerIconComponent } from '../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../auth/services/auth-api.service';

/**
 * Motivo → mensaje, para los guards que devuelven aquí cuando el usuario
 * tiene sesión y rol pero no acceso al RECURSO puntual (esa cuenta, ese id).
 *
 * ⚠️ Antes esos tres guards (`admin-local`, `cuenta-activa`, `cuenta-scope`
 * de `gestion-cuenta/`) redirigían aquí en silencio: el operador veía el
 * campo de ID vacío otra vez y ningún aviso, indistinguible de un clic
 * perdido. Este mapa vive en `HomePage` y no en el hub de gestión de cuenta
 * porque `/cuentas-clientes` — el destino real del redirect — es esta
 * pantalla general, no ese hub (que además exige rol Administrador y
 * rompería para cualquier otro rol).
 */
const MOTIVO_DENEGADO: Record<string, string> = {
  admin_local: 'Solo el administrador local de esa cuenta puede transferir su titularidad.',
  cuenta_inactiva: 'Esa cuenta está dada de baja; no admite esta acción.',
  fuera_de_alcance: 'No tienes acceso a esa cuenta.',
};

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [RouterLink, TablerIconComponent, NodePatternComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './home.page.html',
})
export class HomePage implements OnInit {
  private readonly auth = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly profile = this.auth.getProfile();
  readonly accesoDenegado = signal('');

  ngOnInit(): void {
    const motivo = this.route.snapshot.queryParamMap.get('denegado');
    if (motivo) {
      this.accesoDenegado.set(MOTIVO_DENEGADO[motivo] ?? 'No se pudo completar la acción solicitada.');
      void this.router.navigate([], { queryParams: {}, replaceUrl: true });
    }
  }

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
