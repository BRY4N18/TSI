/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Suscripciones)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Cobro al primer intento',
        informe: 'cobro-primer-intento',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ pagadas: 10, primer_intento: 7, tras_reintentos: 3 }],
          meta: {},
        },
      },
      {
        titulo: 'Dunning',
        informe: 'efectividad-dunning',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ escalon: 3, recuperadas: 2 }],
          meta: {},
        },
      },
      {
        titulo: 'Sin método',
        informe: 'clientes-sin-metodo-pago',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ nombre_comercial: 'Acme', caduca_en_dias: 12 }],
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

  it('al_abrirse_muestra_los_informes_de_apoyo_y_no_sustituye_el_visual', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Cobro al primer intento');
    expect(texto).toContain('Dunning');
    expect(texto).toContain('Sin método');
    expect(texto).toContain('7 de 10 cobradas al primer intento');
    expect(texto).not.toContain('zona-visual');
  });
});
