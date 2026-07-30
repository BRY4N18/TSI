/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { TicketApiService } from './ticket-api.service';

describe('TicketApiService', () => {
  let service: TicketApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TicketApiService],
    });
    service = TestBed.inject(TicketApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('registrar_when_ok_returns_ticket', () => {
    service
      .registrar({ idcliente: 1, asunto: 'a', descripcion: 'b', tipo: 'tecnico' })
      .subscribe((res) => {
        expect(res.data.id_reclamo).toBe(1);
      });
    const req = http.expectOne('/api/v1/soporte/tickets');
    expect(req.request.method).toBe('POST');
    req.flush({ data: { id_reclamo: 1, estado: 'Abierto' }, meta: {} });
  });

  it('tomar_when_ok_returns_transicion', () => {
    service.tomar(1).subscribe((res) => {
      expect(res.data.estado_nuevo).toBe('En_progreso');
    });
    const req = http.expectOne('/api/v1/soporte/tickets/1/tomar');
    expect(req.request.method).toBe('POST');
    req.flush({ data: { id_reclamo: 1, estado_anterior: 'Abierto', estado_nuevo: 'En_progreso' }, meta: {} });
  });

  it('listar_when_filtros_propaga_query_params', () => {
    service.listar({ prioridad: 'baja', idestadosoporte: 'Abierto' }).subscribe((res) => {
      expect(res.data.items.length).toBe(1);
    });
    const req = http.expectOne(
      (r) =>
        r.url === '/api/v1/soporte/tickets' &&
        r.params.get('prioridad') === 'baja' &&
        r.params.get('idestadosoporte') === 'Abierto',
    );
    expect(req.request.method).toBe('GET');
    req.flush({
      data: {
        items: [{ id_reclamo: 9, asunto: 't', estado: 'Abierto', prioridad: 'baja' }],
      },
      meta: {},
    });
  });

  it('listar_when_sin_filtros_no_envia_query_vacios', () => {
    service.listar({}).subscribe();
    const req = http.expectOne('/api/v1/soporte/tickets');
    expect(req.request.params.keys().length).toBe(0);
    req.flush({ data: { items: [] }, meta: {} });
  });

  it('listarServicios_when_ok_returns_items', () => {
    service.listarServicios().subscribe((res) => {
      expect(res.data.length).toBe(1);
      expect(res.data[0].nombre).toBe('API Despacho');
    });
    const req = http.expectOne('/api/v1/soporte/servicios');
    expect(req.request.method).toBe('GET');
    req.flush({ data: [{ id: 1, nombre: 'API Despacho' }], meta: {} });
  });
});
