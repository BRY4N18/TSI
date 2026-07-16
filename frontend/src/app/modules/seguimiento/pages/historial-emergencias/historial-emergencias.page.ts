import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { catchError, debounceTime, of } from 'rxjs';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ESTADOS, estadoInfo } from '../../../accidentes/estado.constants';
import { EstadoAccidente } from '../../../accidentes/services/models/accidente.types';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
import { UbicacionCatalogoApiService } from '../../../accidentes/services/ubicacion-catalogo-api.service';
import { CatalogoItem } from '../../../accidentes/services/models/accidente.types';
import { DisponibilidadUnidadApiService } from '../../../evidencia-unidad/services/disponibilidad-unidad-api.service';
import { UnidadEmergenciaResumen } from '../../../evidencia-unidad/services/models/evidencia-unidad.types';
import { SeguimientoApiService } from '../../services/seguimiento-api.service';
import { HistorialEmergenciaItem } from '../../models/seguimiento.types';

@Component({
  selector: 'app-historial-emergencias',
  standalone: true,
  imports: [ReactiveFormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './historial-emergencias.page.html',
})
export class HistorialEmergenciasPage implements OnInit {
  private readonly api = inject(SeguimientoApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly unidadApi = inject(DisponibilidadUnidadApiService);
  private readonly fb = inject(FormBuilder);

  readonly severidadOptions = Object.entries(SEVERIDAD_INFO).map(([value, info]) => ({
    value: Number(value),
    label: info.label,
  }));
  readonly estados = ESTADOS;
  readonly estado = estadoInfo;

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estadosRegion = signal<CatalogoItem[]>([]);
  readonly unidades = signal<UnidadEmergenciaResumen[]>([]);

  readonly items = signal<HistorialEmergenciaItem[]>([]);
  readonly loading = signal(false);
  readonly loadingMas = signal(false);
  readonly error = signal<string | null>(null);
  readonly truncado = signal(false);

  private nextCursor: string | null = null;

  readonly filtros = this.fb.group({
    idpais: [null as number | null],
    idestadoregion: [null as number | null],
    idseveridad: [null as number | null],
    estado: [null as string | null],
    idunidademergencia: [null as number | null],
    fechaDesde: [''],
    fechaHasta: [''],
  });

  ngOnInit(): void {
    this.cargar();
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.paises.set(paises));
    this.unidadApi
      .listarUnidades({ limit: 100 })
      .pipe(
        // El listado completo de flota está reservado a Administrador/Despacho
        // (IsAdministradorOrDespachoService). Si el Operador no tiene acceso,
        // el filtro de Unidad simplemente queda sin opciones — no debe tronar
        // el resto de la pantalla.
        catchError(() => of({ data: { items: [] } })),
      )
      .subscribe((res) => this.unidades.set(res.data.items));

    this.filtros.controls.idpais.valueChanges.subscribe((idpais) => {
      this.filtros.controls.idestadoregion.setValue(null, { emitEvent: false });
      this.estadosRegion.set([]);
      if (idpais) {
        this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => this.estadosRegion.set(estados));
      }
    });

    this.filtros.valueChanges.pipe(debounceTime(300)).subscribe(() => this.cargar());
  }

  severidad(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  asEstado(estado: string): EstadoAccidente {
    return estado as EstadoAccidente;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.nextCursor = null;
    this.buscar().subscribe({
      next: (res) => {
        this.items.set(res.data.items);
        this.nextCursor = res.data.next_cursor;
        this.truncado.set(!!this.nextCursor);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el historial de emergencias.');
        this.loading.set(false);
      },
    });
  }

  cargarMas(): void {
    if (!this.nextCursor) {
      return;
    }
    this.loadingMas.set(true);
    this.buscar(this.nextCursor).subscribe({
      next: (res) => {
        this.items.update((actuales) => [...actuales, ...res.data.items]);
        this.nextCursor = res.data.next_cursor;
        this.truncado.set(!!this.nextCursor);
        this.loadingMas.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar más resultados.');
        this.loadingMas.set(false);
      },
    });
  }

  private buscar(cursor?: string) {
    const raw = this.filtros.getRawValue();
    return this.api.listarHistorial({
      cursor,
      limit: 20,
      estado: raw.estado ?? undefined,
      idseveridad: raw.idseveridad ?? undefined,
      idunidademergencia: raw.idunidademergencia ?? undefined,
      idestadoregion: raw.idestadoregion ?? undefined,
      fechaDesde: raw.fechaDesde ? new Date(raw.fechaDesde).getTime() : undefined,
      fechaHasta: raw.fechaHasta ? new Date(raw.fechaHasta).getTime() : undefined,
    });
  }
}
