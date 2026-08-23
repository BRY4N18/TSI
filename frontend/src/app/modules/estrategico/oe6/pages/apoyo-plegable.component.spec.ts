/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (OE6)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Rechazo y timeout (con denominador)',
        informe: 'rechazo-y-timeout-por-unidad',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ unidad: 'U-1', rechazados: 2, ofrecidos: 10 }],
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

  it('al_abrir_muestra_denominador', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('10');
    expect(texto).toContain('ofrecidos');
  });
});
