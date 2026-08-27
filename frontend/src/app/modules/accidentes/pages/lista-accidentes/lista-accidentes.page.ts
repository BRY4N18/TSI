import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';

import { CaseCardComponent } from '../../../../shared/ui/case-card/case-card.component';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { AccidenteApiService } from '../../services/accidente-api.service';
import {
  AccidenteListItem,
  CatalogoItem,
  EstadoAccidente,
  UbicacionLegible,
} from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../severidad.constants';
import { ESTADOS, EstadoInfo, estadoInfo as estadoInfoOf } from '../../estado.constants';

@Component({
  selector: 'app-lista-accidentes',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, TablerIconComponent, CaseCardComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './lista-accidentes.page.html',
})
export class ListaAccidentesPage implements OnInit {
  private readonly api = inject(AccidenteApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly fb = inject(FormBuilder);
  private readonly authApi = inject(AuthApiService);
  private readonly router = inject(Router);
  private readonly listaSeleccion = inject(ListaSeleccionStorage);

  puedeRegistrar(): boolean {
    return this.authApi.hasAnyRole(['Operador', 'Administrador']);
  }

  readonly severidadOptions = Object.entries(SEVERIDAD_INFO).map(([value, info]) => ({
    value: Number(value),
    label: info.label,
  }));
  readonly estados = ESTADOS;

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estadosRegion = signal<CatalogoItem[]>([]);

  readonly accidentes = signal<AccidenteListItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedId = signal<string | null>(null);

  /** Tamaño de página pedido al backend; el servidor topa a 100. */
  readonly pageLimit = 20;
  readonly nextCursor = signal<string | null>(null);
  cursor: string | null = null;
  private cursorStack: (string | null)[] = [];

  readonly filtros = this.fb.group({
    busqueda: [''],
    idpais: [null as number | null],
    idestadoregion: [null as number | null],
    idseveridad: [null as number | null],
    estado: [null as EstadoAccidente | null],
    fechaDesde: [''],
    fechaHasta: [''],
    activo: [true],
  });

  ngOnInit(): void {
    this.selectedId.set(this.listaSeleccion.get());
    this.cargar();
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.paises.set(paises));

    this.filtros.controls.idpais.valueChanges.subscribe((idpais) => {
      this.filtros.controls.idestadoregion.setValue(null, { emitEvent: false });
      this.estadosRegion.set([]);
      if (idpais) {
        this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => this.estadosRegion.set(estados));
      }
    });

    // Cambiar un filtro reinicia la paginación: los cursores acumulados
    // pertenecen al conjunto de resultados anterior y ya no son válidos.
    this.filtros.valueChanges
      .pipe(debounceTime(300))
      .subscribe(() => this.cargar({ reiniciarCursor: true }));
  }

  get puedeSiguiente(): boolean {
    return this.nextCursor() !== null;
  }

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  paginaSiguiente(): void {
    const siguiente = this.nextCursor();
    if (!siguiente) {
      return;
    }
    this.cursorStack.push(this.cursor);
    this.cursor = siguiente;
    this.cargar();
  }

  paginaAnterior(): void {
    if (!this.cursorStack.length) {
      return;
    }
    this.cursor = this.cursorStack.pop() ?? null;
    this.cargar();
  }

  esSeleccionado(idaccidente: string): boolean {
    return this.selectedId() === idaccidente;
  }

  abrirCaso(idaccidente: string, focus: 'view' | 'edit' = 'view'): void {
    this.listaSeleccion.set(idaccidente);
    this.selectedId.set(idaccidente);
    void this.router.navigate(['/accidentes', idaccidente], {
      queryParams: focus === 'edit' ? { focus: 'edit' } : {},
    });
  }

  severidadInfo(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  estadoInfo(estado: EstadoAccidente | null | undefined): EstadoInfo {
    return estadoInfoOf(estado);
  }

  ubicacionLabel(ubicacion: UbicacionLegible | null | undefined): string {
    if (!ubicacion) {
      return '—';
    }
    return [ubicacion.calle, ubicacion.ciudad].filter(Boolean).join(', ') || '—';
  }

  cargar(opciones: { reiniciarCursor?: boolean } = {}): void {
    if (opciones.reiniciarCursor) {
      this.cursor = null;
      this.cursorStack = [];
    }
    const raw = this.filtros.getRawValue();
    this.loading.set(true);
    this.error.set(null);

    this.api
      .listar({
        busqueda: raw.busqueda?.trim() || undefined,
        idseveridad: raw.idseveridad ?? undefined,
        estado: raw.estado ?? undefined,
        activo: raw.activo ?? undefined,
        fechaDesde: raw.fechaDesde ? new Date(raw.fechaDesde).getTime() : undefined,
        fechaHasta: raw.fechaHasta ? new Date(raw.fechaHasta).getTime() : undefined,
        idestadoregion: raw.idestadoregion ?? undefined,
        limit: this.pageLimit,
        cursor: this.cursor,
      })
      .subscribe({
        next: (res) => {
          this.accidentes.set(res.data);
          const siguiente = res.meta?.pagination?.next_cursor;
          this.nextCursor.set(siguiente ? String(siguiente) : null);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la lista de accidentes.');
          this.loading.set(false);
        },
      });
  }
}
