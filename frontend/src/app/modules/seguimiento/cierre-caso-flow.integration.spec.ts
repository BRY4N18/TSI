/** @marker integration */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SeguimientoApiService } from './services/seguimiento-api.service';

describe('Cierre de caso - integration flow', () => {
  let service: SeguimientoApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(SeguimientoApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('cerrarCaso_envia_el_reporte_final_y_recibe_confirmacion_de_cierre', () => {
    // Arrange
    const body = { resultado_atencion: 'Atencion completada, unidad liberada' };

    // Act
    service.cerrarCaso('ACC-200', body).subscribe((res) => {
      expect(res.data.estado_caso).toBe('CERRADO');
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/accidentes/ACC-200/cerrar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    req.flush({
      data: {
        idaccidente: 'ACC-200',
        estado_caso: 'CERRADO',
        horafin: Date.now(),
        duracionminutos: 30,
        tiempos: { duracionminutos: 30 },
        despachos_retirados: [1],
      },
      meta: { timestamp: new Date().toISOString() },
    });
  });

  it('cerrarCaso_seguido_de_consulta_de_expediente_refleja_el_estado_cerrado', () => {
    // Arrange
    service.cerrarCaso('ACC-201', { resultado_atencion: 'Cierre' }).subscribe();
    const cerrarReq = httpMock.expectOne('/api/v1/accidentes/ACC-201/cerrar');
    cerrarReq.flush({
      data: {
        idaccidente: 'ACC-201',
        estado_caso: 'CERRADO',
        horafin: Date.now(),
        duracionminutos: 10,
        tiempos: { duracionminutos: 10 },
        despachos_retirados: [],
      },
      meta: { timestamp: new Date().toISOString() },
    });

    // Act
    service.obtenerExpedienteOperador('ACC-201').subscribe((res) => {
      // Assert
      expect(res.data.estado_actual).toBe('CERRADO');
    });

    const expedienteReq = httpMock.expectOne(
      '/api/v1/emergencias/historial/ACC-201/expediente',
    );
    expect(expedienteReq.request.method).toBe('GET');
    expedienteReq.flush({
      data: {
        accidente: {},
        estado_actual: 'CERRADO',
        historial_estados_caso: [],
        despachos: [],
        notas: [],
        evidencias: [],
        trayectoria_gps: [],
      },
      meta: { timestamp: new Date().toISOString() },
    });
  });

  it('cancelarCaso_cuando_el_backend_rechaza_por_estado_invalido_propaga_el_error', () => {
    // Arrange
    let errorStatus: number | undefined;

    // Act
    service
      .cancelarCaso('ACC-202', { motivo: 'Falsa alarma' })
      .subscribe({ error: (err) => (errorStatus = err.status) });

    const req = httpMock.expectOne('/api/v1/accidentes/ACC-202/cancelar');
    req.flush(
      { error: 'invalid_state', detail: 'El caso ya esta cerrado', code: 'invalid_state' },
      { status: 409, statusText: 'Conflict' },
    );

    // Assert
    expect(errorStatus).toBe(409);
  });
});
