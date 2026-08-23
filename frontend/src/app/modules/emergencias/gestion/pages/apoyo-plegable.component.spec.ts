/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Latencia de sincronización',
        informe: 'latencia-sincronizacion',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ sin_instante_sincronia: 2, con_instante_sincronia: 8 }],
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

  it('al_abrirse_muestra_los_informes_de_apoyo', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Latencia de sincronización');
    // ⚠️ «sincronizadas» ya no: decía «0 sincronizadas · 50 pendientes» sobre
    // evidencias que el origen marca como sincronizadas. Ahora se declara qué
    // fracción tiene instante con el que medir la latencia.
    expect(fixture.nativeElement.textContent).toContain('latencia medible en');
  });
});
