import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ListEmptyStateComponent } from '../../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
} from '../../../../../shared/ui/list-states/list-table.styles';
import { AuthApiService } from '../../../auth/services/auth-api.service';
import { BusinessRole, BusinessUser } from '../../../auth/services/auth-api.types';
import { UserRoleAdminService } from '../../../auth/services/user-role-admin.service';

@Component({
  selector: 'app-gestion-cuenta-hub',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './hub.page.html',
})
export class GestionCuentaHubPage implements OnInit {
  private readonly usersApi = inject(UserRoleAdminService);
  private readonly auth = inject(AuthApiService);
  private readonly router = inject(Router);

  readonly usuarios = signal<BusinessUser[]>([]);
  readonly roles = signal<BusinessRole[]>([]);
  readonly cargando = signal(false);
  readonly mensaje = signal('');
  readonly error = signal('');

  readonly listTableClass = LIST_TABLE_CLASS;
  readonly listTableThClass = LIST_TABLE_TH_CLASS;
  readonly listTableTdClass = LIST_TABLE_TD_CLASS;
  readonly listTableTdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly listRowClass = LIST_ROW_CLASS;
  readonly listMobileCardClass = LIST_MOBILE_CARD_CLASS;

  idclienteDestino = 1;
  cuentasDisponibles = signal<{ id: number; label: string }[]>([]);
  assignUserId: number | null = null;
  assignRoleId: number | null = null;

  ngOnInit(): void {
    const cuenta = this.auth.getCuenta();
    if (cuenta?.idcliente) {
      this.idclienteDestino = cuenta.idcliente;
    }
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set('');
    this.usersApi.listUsers().subscribe({
      next: (res) => {
        this.usuarios.set(res.data ?? []);
        this.usersApi.listRoles().subscribe({
          next: (rolesRes) => {
            this.roles.set(rolesRes.data ?? []);
            this.assignRoleId = this.roles()[0]?.idrol ?? null;
            this.assignUserId = this.usuarios()[0]?.idusuario ?? null;
            this.cargando.set(false);
          },
          error: () => {
            this.cargando.set(false);
            this.error.set('No se pudieron cargar los roles.');
          },
        });
      },
      error: () => {
        this.cargando.set(false);
        this.error.set('No se pudieron cargar los usuarios.');
      },
    });
  }

  abrirCuenta(seccion: 'perfil' | 'preferencias' | 'transferencia' | 'baja'): void {
    const id = Number(this.idclienteDestino);
    if (!Number.isFinite(id) || id < 1) {
      this.error.set('Indica un ID de cliente válido.');
      return;
    }
    void this.router.navigate(['/cuentas-clientes/gestion-cuenta', id, seccion]);
  }

  asignarRol(): void {
    if (!this.assignUserId || !this.assignRoleId) {
      return;
    }
    this.usersApi
      .assignRole({ idusuario: this.assignUserId, idrol: this.assignRoleId })
      .subscribe({
        next: () => {
          this.mensaje.set('Rol asignado correctamente.');
          this.cargar();
        },
        error: () => this.error.set('No se pudo asignar el rol.'),
      });
  }

  desactivar(u: BusinessUser): void {
    this.usersApi.deactivateUser(u.idusuario).subscribe({
      next: () => {
        this.mensaje.set(`Usuario ${u.gmail} desactivado.`);
        this.cargar();
      },
      error: () => this.error.set('No se pudo desactivar el usuario.'),
    });
  }

  esAdmin(): boolean {
    return this.auth.hasRole('Administrador');
  }
}
