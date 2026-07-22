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
});
