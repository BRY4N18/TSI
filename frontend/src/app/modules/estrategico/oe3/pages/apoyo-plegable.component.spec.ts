/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (OE3)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Pérdida de señal (con recuento)',
        informe: 'perdida-de-senal',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ unidad: 'U-1', huecos: 2, intervalos_medidos: 40 }],
          meta: {},
        },
      },
    ]);
    fixture.detectChanges();
  });

  it('nace_plegado', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    expect(details.open).toBeFalse();
  });

  it('al_abrir_muestra_recuento', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('40');
    expect(texto).toContain('intervalos');
  });
});
