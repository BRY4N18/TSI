import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { EvidenciaApiService } from '../../services/evidencia-api.service';
import { EvidenciaSyncSchedulerService } from '../../services/evidencia-sync-scheduler.service';
import { EvidenciaFotoItem, EvidenciaItem } from '../../services/models/evidencia-unidad.types';
import { EvidenciaCapturaModal } from './evidencia-captura.modal';
import { EvidenciaVisorModal } from './evidencia-visor.modal';

@Component({
  selector: 'app-galeria-evidencias',
  standalone: true,
  imports: [
    RouterLink,
    DatePipe,
    TablerIconComponent,
    ListEmptyStateComponent,
    EvidenciaCapturaModal,
    EvidenciaVisorModal,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './galeria-evidencias.page.html',
})
export class GaleriaEvidenciasPage implements OnInit {
  readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly syncScheduler = inject(EvidenciaSyncSchedulerService);
  private readonly notifications = inject(NotificationService);
  private readonly authApi = inject(AuthApiService);
  readonly connectivity = inject(ConnectivityService);

  /** Roles que sí pueden abrir el detalle del accidente (accidentesLecturaGuard). */
  private static readonly ROLES_DETALLE = ['Operador', 'Tecnico', 'Administrador'];

  idaccidente = '';
  /** Solo consulta cuando se abre desde Detalles (`?mode=view`). */
  readonly soloLectura = signal(false);
  readonly items = signal<EvidenciaItem[]>([]);
  readonly error = signal('');
  readonly cargando = signal(true);
  readonly sincronizando = signal(false);
  readonly mostrarSubida = signal(false);
  readonly fotoVisorIndice = signal<number | null>(null);

  /**
   * A dónde vuelve el enlace de la cabecera. El detalle del accidente es una
   * pantalla de Operador: la unidad que llega desde su seguimiento no puede
   * abrirlo y acabaría en "Acceso denegado", sin forma de volver a lo suyo.
   */
  rutaVolver(): string[] {
    return this.authApi.hasAnyRole(GaleriaEvidenciasPage.ROLES_DETALLE)
      ? ['/accidentes', this.idaccidente]
      : ['/seguimiento/mi-seguimiento'];
  }

  etiquetaVolver(): string {
    return this.authApi.hasAnyRole(GaleriaEvidenciasPage.ROLES_DETALLE)
      ? 'Volver al accidente'
      : 'Volver a mi seguimiento';
  }

  fotos() {
    return this.items().filter((item) => this.evidenciaApi.isFotoItem(item));
  }

  fotosSincronizadas(): EvidenciaFotoItem[] {
    return this.fotos().filter((item): item is EvidenciaFotoItem => item.sincronizado);
  }

  notas() {
    return this.items().filter((item) => this.evidenciaApi.isNotaItem(item));
  }

  abrirVisor(item: EvidenciaFotoItem): void {
    const indice = this.fotosSincronizadas().indexOf(item);
    if (indice !== -1) {
      this.fotoVisorIndice.set(indice);
    }
  }

  ngOnInit(): void {
    this.idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? '';
    this.soloLectura.set(this.route.snapshot.queryParamMap.get('mode') === 'view');
    this.syncScheduler.registrarCaso(this.idaccidente);
    this.recargar();
  }

  onEvidenciaGuardada(): void {
    this.mostrarSubida.set(false);
    this.recargar();
  }

  recargar(): void {
    this.error.set('');
    this.cargando.set(true);
    this.evidenciaApi.listarConPendientesLocales(this.idaccidente).subscribe({
      next: (items) => {
        this.items.set(items);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la galería');
        this.cargando.set(false);
      },
    });
  }

  sincronizar(): void {
    this.sincronizando.set(true);
    this.evidenciaApi.sincronizarPendientes(this.idaccidente).subscribe({
      next: (res) => {
        this.notifications.toast(
          `Sincronizados: ${res.data.sincronizados}, pendientes: ${res.data.pendientes}`,
          'success',
        );
        this.sincronizando.set(false);
        this.recargar();
      },
      error: () => {
        this.sincronizando.set(false);
        this.notifications.alert('No se pudo sincronizar la evidencia pendiente.', 'Error al sincronizar');
      },
    });
  }

  trackItem(item: EvidenciaItem): string | number {
    if ('local_id' in item) {
      return item.local_id;
    }
    if ('idevidenciafoto' in item) {
      return item.idevidenciafoto;
    }
    return item.idnotaaccidentes;
  }
}
