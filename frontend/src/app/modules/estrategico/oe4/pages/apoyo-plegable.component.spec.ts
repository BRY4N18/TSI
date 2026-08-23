/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (OE4)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Calidad por origen (central vs campo)',
        informe: 'calidad-por-origen',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ origen: 'central', pct_completitud: 0.9, casos: 10 }],
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

  it('al_abrir_muestra_origen', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent as string).toContain('central');
  });
});
