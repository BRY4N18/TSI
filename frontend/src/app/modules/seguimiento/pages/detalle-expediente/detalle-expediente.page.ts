import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { SEVERIDAD_INFO } from '../../../accidentes/severidad.constants';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { ExpedienteData } from '../../models/seguimiento.types';
import { ExpedienteClienteApiService } from '../../services/expediente-cliente-api.service';

/**
 * Expediente del cliente en modo Ver (RF-SEG-006).
 *
 * Sigue el chrome de workpanel en pagina dedicada del golden sample
 * (Accidente Detalles, design-system seccion 5): link «Volver a la lista» con
 * `arrow-left`, eyebrow de modo, h1 + badge en la misma fila, secciones en
 * cards y datos como `<dl>` — nunca `<input disabled>` para fingir solo lectura.
 */
@Component({
  selector: 'app-detalle-expediente',
  standalone: true,
  imports: [
    DatePipe,
    RouterLink,
    TablerIconComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './detalle-expediente.page.html',
})
export class DetalleExpedientePage implements OnInit {
  private readonly api = inject(ExpedienteClienteApiService);
  private readonly route = inject(ActivatedRoute);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly expediente = signal<ExpedienteData | null>(null);
  readonly idaccidente = signal<string | null>(null);
  readonly descargando = signal(false);

  readonly accidente = computed(
    () => (this.expediente()?.accidente ?? {}) as Record<string, unknown>,
  );

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('idaccidente');
    if (!id) {
      this.error.set('No se indicó el expediente a consultar.');
      return;
    }
    this.idaccidente.set(id);
    this.cargar();
  }

  cargar(): void {
    const id = this.idaccidente();
    if (!id) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.api.obtenerDetalle(id).subscribe({
      next: (res) => {
        this.expediente.set(res.data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err?.status === 404
            ? 'Este expediente no existe o no pertenece a tu cuenta.'
            : 'No se pudo cargar el expediente.',
        );
      },
    });
  }

  campo(nombre: string): string {
    const valor = this.accidente()[nombre];
    return valor === null || valor === undefined || valor === '' ? '—' : String(valor);
  }

  fecha(nombre: string): number | null {
    const valor = this.accidente()[nombre];
    return typeof valor === 'number' ? valor : null;
  }

  severidadLabel(): string {
    const valor = this.accidente()['idseveridad'];
    return typeof valor === 'number' ? (SEVERIDAD_INFO[valor]?.label ?? '—') : '—';
  }

  conteo(clave: keyof ExpedienteData): number {
    const valor = this.expediente()?.[clave];
    return Array.isArray(valor) ? valor.length : 0;
  }

  descargarPdf(): void {
    const id = this.idaccidente();
    if (!id || this.descargando()) {
      return;
    }
    this.descargando.set(true);
    this.api.descargarPdf(id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `expediente-${id}.pdf`;
        enlace.click();
        URL.revokeObjectURL(url);
        this.descargando.set(false);
      },
      error: () => {
        this.descargando.set(false);
        this.error.set('No se pudo descargar el PDF del expediente.');
      },
    });
  }
}
