/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ExpedienteClienteApiService } from '../../services/expediente-cliente-api.service';
import { DetalleExpedientePage } from './detalle-expediente.page';

const EXPEDIENTE = {
  accidente: {
    idaccidente: 'ACC-9',
    fechahoraaccidente: 1785542765994,
    idseveridad: 3,
    descripcion: 'Colisión en avenida principal',
    numvehiculos: 2,
    numheridos: 1,
  },
  estado_actual: 'CERRADO',
  historial_estados_caso: [],
  despachos: [{}],
  notas: [{}, {}],
  evidencias: [],
  trayectoria_gps: [{}, {}, {}],
};

describe('DetalleExpedientePage', () => {
  let fixture: ComponentFixture<DetalleExpedientePage>;
  let api: jasmine.SpyObj<ExpedienteClienteApiService>;

  function montar(idaccidente: string | null = 'ACC-9') {
    TestBed.configureTestingModule({
      imports: [DetalleExpedientePage],
      providers: [
        // `provideRouter` va primero: tambien aporta ActivatedRoute y el ultimo
        // proveedor gana, asi que el doble debe declararse despues.
        provideRouter([]),
        { provide: ExpedienteClienteApiService, useValue: api },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => idaccidente } } },
        },
      ],
    });
    fixture = TestBed.createComponent(DetalleExpedientePage);
    fixture.detectChanges();
  }

  beforeEach(() => {
    api = jasmine.createSpyObj('ExpedienteClienteApiService', [
      'listar',
      'obtenerDetalle',
      'descargarPdf',
    ]);
    api.obtenerDetalle.and.returnValue(of({ data: EXPEDIENTE, meta: { pagination: null } } as any));
  });

  it('carga_el_expediente_de_la_ruta', () => {
    // Act
    montar();

    // Assert
    expect(api.obtenerDetalle).toHaveBeenCalledWith('ACC-9');
  });

  it('renderiza_el_chrome_de_workpanel_del_golden_sample', () => {
    // Act
    montar();

    // Assert — link de retorno, eyebrow de modo y h1 con el identificador
    const root = fixture.nativeElement as HTMLElement;
    expect(root.textContent).toContain('Volver a la lista');
    expect(root.querySelector('[data-testid="modo-titulo"]')?.textContent?.trim()).toBe('Detalles');
    expect(root.querySelector('h1')?.textContent?.trim()).toBe('ACC-9');
  });

  it('muestra_los_datos_como_dl_y_no_como_inputs_deshabilitados', () => {
    // Act
    montar();

    // Assert — el design-system prohíbe <input disabled> para fingir solo lectura
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelectorAll('dl').length).toBeGreaterThan(0);
    expect(root.querySelectorAll('input').length).toBe(0);
    expect(root.textContent).toContain('Colisión en avenida principal');
    expect(root.textContent).toContain('Grave');
  });

  it('resume_el_contenido_del_expediente', () => {
    // Act
    montar();

    // Assert
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Despachos');
    expect(texto).toContain('Puntos GPS');
  });

  it('error_404_explica_que_el_expediente_no_es_de_la_cuenta', () => {
    // Arrange
    api.obtenerDetalle.and.returnValue(throwError(() => ({ status: 404 })));

    // Act
    montar();

    // Assert
    const root = fixture.nativeElement as HTMLElement;
    expect(root.textContent).toContain('no pertenece a tu cuenta');
    expect(root.querySelector('[data-testid="btn-reintentar-lista"]')).toBeTruthy();
  });

  it('sin_id_en_la_ruta_no_llama_al_backend', () => {
    // Act
    montar(null);

    // Assert
    expect(api.obtenerDetalle).not.toHaveBeenCalled();
  });
});
