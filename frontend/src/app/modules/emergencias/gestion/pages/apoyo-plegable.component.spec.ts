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
          data: [{ pendientes: 2, sincronizadas: 8 }],
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
    expect(fixture.nativeElement.textContent).toContain('sincronizadas');
  });
});
