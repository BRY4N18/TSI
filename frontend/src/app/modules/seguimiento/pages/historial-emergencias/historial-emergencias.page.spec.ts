/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { UbicacionCatalogoApiService } from '../../../accidentes/services/ubicacion-catalogo-api.service';
import { DisponibilidadUnidadApiService } from '../../../evidencia-unidad/services/disponibilidad-unidad-api.service';
import { SeguimientoApiService } from '../../services/seguimiento-api.service';
import { HistorialEmergenciasPage } from './historial-emergencias.page';

describe('HistorialEmergenciasPage', () => {
  let fixture: ComponentFixture<HistorialEmergenciasPage>;
  let api: jasmine.SpyObj<SeguimientoApiService>;

  const item = {
    idaccidente: 'ACC-1',
    fecha: 1720000000000,
    estado: 'CERRADO',
    severidad: 2,
    ubicacion: 'Av. Siempre Viva',
    tiempos: { respuesta_min: 3, transito_min: 8, atencion_min: 20, duracion_total_min: 31 },
    unidad_principal: 'AMB-01',
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj('SeguimientoApiService', ['listarHistorial']);
    api.listarHistorial.and.returnValue(of<any>({ data: { items: [item], next_cursor: null }, meta: {} }));

    const ubicacionCatalogo = jasmine.createSpyObj('UbicacionCatalogoApiService', [
      'listarPaises',
      'listarEstados',
    ]);
    ubicacionCatalogo.listarPaises.and.returnValue(of([]));
    ubicacionCatalogo.listarEstados.and.returnValue(of([]));

    const unidadApi = jasmine.createSpyObj('DisponibilidadUnidadApiService', ['listarUnidades']);
    unidadApi.listarUnidades.and.returnValue(of<any>({ data: { items: [] }, meta: {} }));

    await TestBed.configureTestingModule({
      imports: [HistorialEmergenciasPage],
      providers: [
        { provide: SeguimientoApiService, useValue: api },
        { provide: UbicacionCatalogoApiService, useValue: ubicacionCatalogo },
        { provide: DisponibilidadUnidadApiService, useValue: unidadApi },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HistorialEmergenciasPage);
    fixture.detectChanges();
  });

  it('ngOnInit_carga_el_historial_al_iniciar', () => {
    // Assert
    expect(api.listarHistorial).toHaveBeenCalled();
    expect(fixture.componentInstance.items().length).toBe(1);
    expect(fixture.componentInstance.items()[0].unidad_principal).toBe('AMB-01');
  });

  it('cargar_when_api_error_muestra_estado_de_error', () => {
    // Arrange
    api.listarHistorial.and.returnValue(throwError(() => new Error('network')));

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(fixture.componentInstance.error()).toBe('No se pudo cargar el historial de emergencias.');
  });
});
