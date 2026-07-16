/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import * as L from 'leaflet';

import { RutaService } from './ruta.service';

describe('RutaService', () => {
  let service: RutaService;
  let http: HttpTestingController;

  const origen = L.latLng(4.65, -74.08);
  const destino = L.latLng(4.6, -74.07);

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [RutaService],
    });
    service = TestBed.inject(RutaService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('calcularRuta_when_osrm_ok_returns_puntos', () => {
    // Arrange
    const mock = {
      data: { puntos: [{ latitud: 4.65, longitud: -74.08 }, { latitud: 4.6, longitud: -74.07 }] },
      meta: { pagination: null },
    };

    // Act
    let resultado: L.LatLngExpression[] | undefined;
    service.calcularRuta(origen, destino).subscribe((puntos) => (resultado = puntos));

    const req = http.expectOne(
      (r) => r.url === '/api/v1/seguimiento/ruta' && r.params.get('origen') === '4.65,-74.08',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mock);

    // Assert
    expect(resultado?.length).toBe(2);
  });

  it('calcularRuta_when_puntos_vacio_returns_linea_recta', () => {
    // Arrange
    const mock = { data: { puntos: [] }, meta: { pagination: null } };

    // Act
    let resultado: L.LatLngExpression[] | undefined;
    service.calcularRuta(origen, destino).subscribe((puntos) => (resultado = puntos));

    const req = http.expectOne((r) => r.url === '/api/v1/seguimiento/ruta');
    req.flush(mock);

    // Assert
    expect(resultado).toEqual([origen, destino]);
  });

  it('calcularRuta_when_request_falla_returns_linea_recta', () => {
    // Act
    let resultado: L.LatLngExpression[] | undefined;
    service.calcularRuta(origen, destino).subscribe((puntos) => (resultado = puntos));

    const req = http.expectOne((r) => r.url === '/api/v1/seguimiento/ruta');
    req.error(new ProgressEvent('network error'));

    // Assert
    expect(resultado).toEqual([origen, destino]);
  });
});
