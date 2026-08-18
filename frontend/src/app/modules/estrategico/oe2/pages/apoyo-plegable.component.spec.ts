/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (OE2)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Latencia p95, media y muestras',
        informe: 'latencia-por-endpoint',
        carga: {
          estado: 'dato',
          error: null,
          data: [
            {
              endpoint_path: '/v1/x',
              latencia_p95_ms: 90,
              latencia_media_ms: 80,
              muestras: 5,
              percentil_fiable: 0,
            },
          ],
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

  it('al_abrir_muestra_trio_y_no_fiable', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('90');
    expect(texto).toContain('80');
    expect(texto).toContain('5');
    expect(texto).toContain('no fiable');
    expect(texto).not.toContain('zona-visual');
  });
});
