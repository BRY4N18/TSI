import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { DespachoApiService } from '../../services/despacho-api.service';
import { UnidadCandidata } from '../../services/models/despacho.types';

@Component({
  selector: 'app-asignacion-manual',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './asignacion-manual.page.html',
})
export class AsignacionManualPage {
  private readonly api = inject(DespachoApiService);
  private readonly route = inject(ActivatedRoute);

  readonly idaccidente = this.route.snapshot.paramMap.get('idaccidente')!;

  readonly candidatas = signal<UnidadCandidata[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly mensaje = signal('');
  readonly asignando = signal(false);
  unidadSeleccionada = 0;

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listarCandidatas(this.idaccidente).subscribe({
      next: (res) => {
        this.candidatas.set(res.data.candidatas);
        if (res.data.candidatas.length) {
          this.unidadSeleccionada = res.data.candidatas[0].idunidademergencia;
        }
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar las unidades candidatas.');
        this.loading.set(false);
      },
    });
  }

  asignar(): void {
    this.asignando.set(true);
    this.mensaje.set('');
    this.api.asignarManual(this.idaccidente, this.unidadSeleccionada).subscribe({
      next: (res) => {
        this.mensaje.set(res.data.message);
        this.asignando.set(false);
      },
      error: () => {
        this.mensaje.set('Error al asignar');
        this.asignando.set(false);
      },
    });
  }
}
