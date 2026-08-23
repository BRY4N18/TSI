import { TestBed } from '@angular/core/testing';

import { PeriodoSelectorComponent } from './periodo-selector.component';

/**
 * ⚠️ Esta prueba existe porque el fallo llegó a pantalla.
 *
 * El selector abría en `hoy - 30`, que son **31 días** contando hoy, mientras el
 * backend por defecto usa 30. La pantalla pedía una ventana y la API otra, y el
 * informe de calidad mostraba 492 casos donde la API devolvía 462. Ninguna de
 * las dos cifras parecía equivocada: el desajuste solo se ve comparándolas.
 */
describe('PeriodoSelectorComponent — ventana por defecto', () => {
  function periodoInicial(hoy: string): { desde: string; hasta: string } {
    jasmine.clock().install();
    jasmine.clock().mockDate(new Date(hoy));
    try {
      const fixture = TestBed.createComponent(PeriodoSelectorComponent);
      fixture.detectChanges();
      const c = fixture.componentInstance;
      return { desde: c.desde, hasta: c.hasta };
    } finally {
      jasmine.clock().uninstall();
    }
  }

  it('abre en una ventana de 30 días que incluye hoy', () => {
    const { desde, hasta } = periodoInicial('2026-08-18T12:00:00Z');
    expect(hasta).toBe('2026-08-18');
    // `- 29` y no `- 30`: del 20/07 al 18/08 hay 30 días contando ambos extremos.
    expect(desde).toBe('2026-07-20');
  });

  it('cruza el cambio de mes sin descuadrar el conteo', () => {
    const { desde, hasta } = periodoInicial('2026-03-05T12:00:00Z');
    expect(hasta).toBe('2026-03-05');
    expect(desde).toBe('2026-02-04');
  });
});
