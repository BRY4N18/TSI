/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { DetallePage } from './detalle.page';

describe('DetallePage (alta-unidades)', () => {
  let fixture: ComponentFixture<DetallePage>;
  let facade: jasmine.SpyObj<UnidadEmergenciaFacadeService>;

  const unidad = {
    idunidademergencia: 7,
    idcliente: 1,
    idcondado: 10,
    tipopropiedad: 'Externa' as const,
    placa: 'ABC-123',
    capacidad: null,
    contactoproveedor: 'x',
    unidademergencia: 'Ambulancia 1',
    tipounidademergencia: 'Ambulancia' as const,
    activo: true,
    latitud: null,
    longitud: null,
  };

  beforeEach(async () => {
    facade = jasmine.createSpyObj('UnidadEmergenciaFacadeService', ['obtener']);
    facade.obtener.and.returnValue(of({ ok: true, data: unidad }));

    await TestBed.configureTestingModule({
      imports: [DetallePage],
      providers: [
        provideRouter([]),
        { provide: UnidadEmergenciaFacadeService, useValue: facade },
        ListaSeleccionStorage,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => '7' } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetallePage);
  });

  it('muestra_detalles_sin_boton_guardar', () => {
    fixture.detectChanges();
    const html = fixture.nativeElement as HTMLElement;
    expect(html.querySelector('[data-testid="detalle-page"]')).toBeTruthy();
    expect(html.textContent).toContain('Detalles');
    expect(html.querySelector('[data-testid="btn-guardar"]')).toBeNull();
    expect(html.querySelector('[data-testid="detalle-sin-guardar"]')).toBeTruthy();
    expect(html.querySelector('[data-testid="detalle-campos"]')).toBeTruthy();
    expect(html.querySelectorAll('input[disabled]').length).toBeGreaterThan(0);
    expect(html.querySelector('[data-testid="btn-editar-desde-detalle"]')).toBeTruthy();
  });
});
