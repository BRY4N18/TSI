/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { TicketApiService } from '../../services/ticket-api.service';
import { ColaAgentePage } from './cola-agente.page';

describe('ColaAgentePage', () => {
  let fixture: ComponentFixture<ColaAgentePage>;
  let api: jasmine.SpyObj<TicketApiService>;

  const ticketAbierto = {
    id_reclamo: 9,
    idcliente: 1,
    asunto: 'Ticket de prueba #9',
    descripcion: 'Detalle',
    tipo: 'Facturación',
    tipo_incidencia: 'Facturación',
    prioridad: 'baja',
    estado: 'Abierto' as const,
    sla_status: 'en curso' as const,
    cierreconfirmadocliente: false,
    fechahora: 1,
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj('TicketApiService', [
      'listar',
      'obtenerDetalle',
      'tomar',
      'comentar',
      'resolver',
    ]);
    api.listar.and.returnValue(of({ data: { items: [] }, meta: {} }));
    api.obtenerDetalle.and.returnValue(
      of({ data: { ticket: ticketAbierto, historial: [] }, meta: {} }),
    );

    await TestBed.configureTestingModule({
      imports: [ColaAgentePage],
      providers: [{ provide: TicketApiService, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(ColaAgentePage);
    fixture.detectChanges();
  });

  it('muestra_empty_state_when_sin_tickets', () => {
    const empty = fixture.nativeElement.querySelector('[data-testid="empty-state"]');
    expect(empty).toBeTruthy();
    expect(empty.textContent).toContain('No hay tickets pendientes.');
    expect(fixture.nativeElement.querySelector('[data-testid="btn-reembolso"]')).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('Nuevo ticket');
  });

  it('muestra_master_detail_y_propaga_filtros', () => {
    api.listar.and.returnValue(of({ data: { items: [ticketAbierto] }, meta: {} }));
    fixture.componentInstance.cargarLista();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[data-testid="master-detail"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="panel-detalle"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="sin-mensajes"]')).toBeTruthy();

    fixture.componentInstance.onFiltroPrioridad('baja');
    expect(api.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ prioridad: 'baja' }),
    );

    fixture.componentInstance.onFiltroEstado('Abierto');
    expect(api.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ prioridad: 'baja', idestadosoporte: 'Abierto' }),
    );
  });
});
