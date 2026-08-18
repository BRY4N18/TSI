/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Soporte al Cliente)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Tickets por servicio',
        informe: 'tickets-por-servicio',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ servicio: 'sin servicio', tickets: 14, incumplidos: 8 }],
          declaraciones: [
            { codigo: 'servicio_no_registrado', mensaje: 'La operación no asigna servicio.' },
          ],
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
    expect(details.getAttribute('data-testid')).toBe('zona-apoyo');
  });

  it('al_abrirse_muestra_sin_servicio_sin_sustituir_el_visual', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('sin servicio');
    expect(texto).toContain('14');
    expect(details.className).not.toContain('lg:col-span-8');
  });
});
