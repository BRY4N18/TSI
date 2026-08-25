import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-duplicado-fusion-dialog',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4">
      <dialog
        open
        class="w-full max-w-md tsi-panel tsi-panel--elevado p-6"
      >
        <h2 class="tsi-display m-0 mb-2 text-lg font-semibold text-text-primary">Posible duplicado</h2>
        <p class="m-0 mb-4 text-sm text-text-secondary">
          Ya hay un caso registrado en el mismo punto y a la misma hora. Al fusionar, este
          reporte se guarda marcado como duplicado y apuntando al caso que lo absorbe, que
          sigue su curso sin cambios. Cancele para registrarlo como un caso independiente.
        </p>
        <label for="idPrincipal" class="mb-1.5 block text-sm font-medium text-text-secondary">
          Caso que absorbe este reporte (el más antiguo, sugerido)
        </label>
        <input
          id="idPrincipal"
          class="tsi-input mb-4 w-full"
          [(ngModel)]="idPrincipal"
          name="idPrincipal"
        />
        <div class="flex justify-end gap-3">
          <button
            type="button"
            class="tsi-btn tsi-btn-secondary"
            (click)="cancelar.emit()"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="tsi-btn tsi-btn-primary"
            (click)="confirmar.emit(idPrincipal)"
          >
            Fusionar
          </button>
        </div>
      </dialog>
    </div>
  `,
})
export class DuplicadoFusionDialog implements OnChanges {
  @Input() idPrincipalSugerido = '';
  @Output() confirmar = new EventEmitter<string>();
  @Output() cancelar = new EventEmitter<void>();

  idPrincipal = '';

  ngOnChanges(): void {
    this.idPrincipal = this.idPrincipalSugerido;
  }
}
