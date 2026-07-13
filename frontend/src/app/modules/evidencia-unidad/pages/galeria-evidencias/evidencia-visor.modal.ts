import { DatePipe } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  computed,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { EvidenciaFotoItem } from '../../services/models/evidencia-unidad.types';

@Component({
  selector: 'app-evidencia-visor-modal',
  standalone: true,
  imports: [DatePipe, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="fixed inset-0 z-50 grid place-items-center bg-black/90 p-4"
      (click)="cerrar.emit()"
    >
      <div
        #dialog
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidencia-visor-titulo"
        tabindex="-1"
        class="grid max-h-[95vh] w-full max-w-4xl grid-rows-[auto_1fr_auto] gap-3"
        (click)="$event.stopPropagation()"
        (keydown)="onKeydown($event)"
      >
        <div class="flex items-center justify-between">
          <span id="evidencia-visor-titulo" class="text-sm font-medium text-white/80">
            Evidencia #{{ fotoActual().idevidenciafoto }} — {{ indice() + 1 }} / {{ fotos().length }}
          </span>
          <button
            type="button"
            (click)="cerrar.emit()"
            aria-label="Cerrar"
            class="inline-flex h-9 w-9 items-center justify-center rounded-md text-white/80 hover:bg-white/10"
          >
            <app-tabler-icon name="x" [size]="20" />
          </button>
        </div>

        <div class="relative grid place-items-center overflow-hidden">
          @if (fotos().length > 1) {
            <button
              type="button"
              (click)="anterior()"
              aria-label="Foto anterior"
              class="absolute left-0 inline-flex h-11 w-11 items-center justify-center rounded-md bg-black/40 text-white hover:bg-black/60"
            >
              <app-tabler-icon name="chevron-left" [size]="24" />
            </button>
          }
          <img
            [src]="fotoActual().urlevidenciafoto"
            alt="Evidencia fotográfica en tamaño completo"
            class="max-h-[70vh] max-w-[85vw] rounded-md object-contain"
          />
          @if (fotos().length > 1) {
            <button
              type="button"
              (click)="siguiente()"
              aria-label="Foto siguiente"
              class="absolute right-0 inline-flex h-11 w-11 items-center justify-center rounded-md bg-black/40 text-white hover:bg-black/60"
            >
              <app-tabler-icon name="chevron-right" [size]="24" />
            </button>
          }
        </div>

        <div class="grid gap-1 text-center text-sm text-white/80">
          <span>{{ fotoActual().fechahora | date: 'dd/MM/yyyy HH:mm' }}</span>
          <span>Subido por {{ fotoActual().autor.nombre }}</span>
        </div>
      </div>
    </div>
  `,
})
export class EvidenciaVisorModal implements OnInit, AfterViewInit, OnDestroy {
  private readonly dialogRef = viewChild.required<ElementRef<HTMLElement>>('dialog');
  private elementoConFocoPrevio: HTMLElement | null = null;

  readonly fotos = input.required<EvidenciaFotoItem[]>();
  readonly indiceInicial = input.required<number>();
  readonly cerrar = output<void>();

  readonly indice = signal(0);
  readonly fotoActual = computed(() => this.fotos()[this.indice()]);

  ngOnInit(): void {
    this.indice.set(this.indiceInicial());
    this.elementoConFocoPrevio = document.activeElement as HTMLElement | null;
  }

  ngAfterViewInit(): void {
    this.dialogRef().nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.elementoConFocoPrevio?.focus();
  }

  anterior(): void {
    const total = this.fotos().length;
    this.indice.set((this.indice() - 1 + total) % total);
  }

  siguiente(): void {
    const total = this.fotos().length;
    this.indice.set((this.indice() + 1) % total);
  }

  onKeydown(event: Event): void {
    if (!(event instanceof KeyboardEvent)) {
      return;
    }
    if (event.key === 'Escape') {
      this.cerrar.emit();
    } else if (event.key === 'ArrowLeft') {
      this.anterior();
    } else if (event.key === 'ArrowRight') {
      this.siguiente();
    }
  }
}
