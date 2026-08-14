import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmDialogHostComponent } from './confirm-dialog-host.component';
import { ConfirmDialogService } from './confirm-dialog.service';

describe('ConfirmDialogHostComponent', () => {
  let fixture: ComponentFixture<ConfirmDialogHostComponent>;
  let dialog: ConfirmDialogService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfirmDialogHostComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(ConfirmDialogHostComponent);
    dialog = TestBed.inject(ConfirmDialogService);
    fixture.detectChanges();
  });

  function abrirDestructivo(): Promise<boolean> {
    const respuesta = dialog.confirm({
      title: 'Descartar borrador',
      message: '¿Descartar el borrador y empezar de nuevo?',
      tone: 'danger',
      confirmLabel: 'Descartar',
      cancelLabel: 'Cancelar',
    });
    fixture.detectChanges();
    return respuesta;
  }

  it('se anuncia como diálogo modal con título y mensaje asociados', () => {
    // Arrange / Act
    void abrirDestructivo();

    // Assert
    const d = fixture.nativeElement.querySelector('[role="dialog"]') as HTMLElement;
    expect(d).not.toBeNull();
    expect(d.getAttribute('aria-modal')).toBe('true');
    expect(
      fixture.nativeElement.querySelector(`#${d.getAttribute('aria-labelledby')}`)?.textContent,
    ).toContain('Descartar borrador');
  });

  it('en tono destructivo el foco inicial va a Cancelar, no a la acción destructiva', () => {
    // Arrange / Act
    void abrirDestructivo();

    // Assert
    expect((document.activeElement as HTMLElement)?.textContent?.trim()).toBe('Cancelar');
  });

  it('Escape equivale a cancelar, nunca a confirmar', async () => {
    // Arrange
    const respuesta = abrirDestructivo();
    const overlay = fixture.nativeElement.querySelector('div') as HTMLElement;

    // Act
    overlay.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();

    // Assert
    await expectAsync(respuesta).toBeResolvedTo(false);
    expect(dialog.active()).toBeNull();
  });
});
