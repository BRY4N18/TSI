/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApoyoPlegableComponent } from './apoyo-plegable.component';

describe('ApoyoPlegableComponent (Ventas y CRM)', () => {
  let fixture: ComponentFixture<ApoyoPlegableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ApoyoPlegableComponent] });
    fixture = TestBed.createComponent(ApoyoPlegableComponent);
    fixture.componentRef.setInput('bloques', [
      {
        titulo: 'Carga por ejecutivo',
        informe: 'carga-por-ejecutivo',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ idejecutivo: 7, activos: 3, valor_pipeline: 1200, conversiones: 1 }],
          meta: {},
        },
      },
      {
        titulo: 'Pipeline ponderado',
        informe: 'pipeline-ponderado',
        carga: {
          estado: 'dato',
          error: null,
          data: [{ etapa: 'Propuesta', valor_ponderado: 400, peso: 0.6 }],
          meta: { filtros: { nota_pesos: 'Los pesos son una convención de este informe.' } },
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

  it('al_abrirse_muestra_carga_y_pipeline_sin_nombres', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Carga por ejecutivo');
    expect(texto).toContain('Pipeline ponderado');
    expect(texto).toContain('Ejecutivo 7');
    expect(texto).not.toContain('Lucía');
    expect(texto).not.toContain('Ramos');
  });

  it('nota_pesos_when_se_abre_es_visible', () => {
    const details = fixture.nativeElement.querySelector('details') as HTMLDetailsElement;
    details.open = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('convención');
  });
});
