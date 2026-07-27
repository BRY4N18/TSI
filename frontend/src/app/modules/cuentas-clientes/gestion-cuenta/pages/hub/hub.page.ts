import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../auth/services/auth-api.service';
import { BusinessRole, BusinessUser } from '../../../auth/services/auth-api.types';
import { UserRoleAdminService } from '../../../auth/services/user-role-admin.service';

@Component({
  selector: 'app-gestion-cuenta-hub',
  standalone: true,
  imports: [FormsModule, RouterLink, TablerIconComponent],
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

  idclienteDestino = 1;
  assignUserId: number | null = null;
  assignRoleId: number | null = null;

  ngOnInit(): void {
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
