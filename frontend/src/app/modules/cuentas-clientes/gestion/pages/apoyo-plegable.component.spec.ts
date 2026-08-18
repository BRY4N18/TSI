/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Cuentas)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Antigüedad media',
        informe: 'antiguedad-media',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ tipo_cliente: 'empresa', plan: 'Pro', dias_mediana: 400 }],
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

  it('al_abrirse_muestra_antiguedad_y_no_sustituye_el_visual', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Antigüedad media');
    expect(texto).toContain('empresa');
    expect(texto).not.toContain('zona-visual');
  });
});
