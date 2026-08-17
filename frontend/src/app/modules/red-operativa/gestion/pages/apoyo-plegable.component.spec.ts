/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Red Operativa)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Pendientes de primer acceso',
        informe: 'pendientes-primer-acceso',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ unidad: 'A' }, { unidad: 'B' }],
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
    expect(fixture.nativeElement.textContent).toContain('Pendientes de primer acceso');
    expect(fixture.nativeElement.textContent).toContain('2 unidades pendientes');
  });

  it('vacio_when_tiene_medida_exacta_la_muestra', () => {
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Casos al despublicar',
        informe: 'casos-activos-al-despublicar',
        carga: {
          estado: 'vacio',
          error: null,
          data: [],
          meta: { medida_exacta_desde: '2026-08-14' },
        },
      },
    ]);
    fixture.detectChanges();
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('2026-08-14');
    expect(fixture.nativeElement.textContent).toContain('nunca haya pasado');
  });
});
