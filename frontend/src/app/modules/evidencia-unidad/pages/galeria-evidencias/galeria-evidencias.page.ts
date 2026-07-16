import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { EvidenciaApiService } from '../../services/evidencia-api.service';
import { EvidenciaSyncSchedulerService } from '../../services/evidencia-sync-scheduler.service';
import { EvidenciaFotoItem, EvidenciaItem } from '../../services/models/evidencia-unidad.types';
import { EvidenciaCapturaModal } from './evidencia-captura.modal';
import { EvidenciaVisorModal } from './evidencia-visor.modal';

@Component({
  selector: 'app-galeria-evidencias',
  standalone: true,
  imports: [RouterLink, DatePipe, TablerIconComponent, EvidenciaCapturaModal, EvidenciaVisorModal],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './galeria-evidencias.page.html',
})
export class GaleriaEvidenciasPage implements OnInit {
  readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly syncScheduler = inject(EvidenciaSyncSchedulerService);
  private readonly notifications = inject(NotificationService);
  readonly connectivity = inject(ConnectivityService);

  idaccidente = '';
  readonly items = signal<EvidenciaItem[]>([]);
  readonly error = signal('');
  readonly cargando = signal(true);
  readonly sincronizando = signal(false);
  readonly mostrarSubida = signal(false);
  readonly fotoVisorIndice = signal<number | null>(null);

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
