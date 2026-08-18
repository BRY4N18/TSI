/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Partners)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Participación de ingresos',
        informe: 'participacion-ingresos-api',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ partner: 'Acme', ingreso_base: 100, excedente: 20 }],
          meta: {},
        },
      },
    ]);
    fixture.detectChanges();
  });

  it('nace_plegado_when_se_pinta', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    expect(details.open).toBeFalse();
    expect(details.getAttribute('open')).toBeNull();
  });

  it('al_abrirse_muestra_excedente_aparte_de_base_y_no_sustituye_el_visual', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Participación de ingresos');
    expect(texto).toContain('excedente');
    expect(texto).toContain('base');
    expect(texto).not.toContain('zona-visual');
  });
});
