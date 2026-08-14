/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { HistorialTicketItem } from '../../services/models/soporte.types';
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

  it('destaca los tickets sin compromiso de tiempo (B43)', () => {
    // Arrange — un ticket clasificado sin plazo aplicable se veía igual que uno
    // cronometrado, y nadie reparaba en que no había nada vigilándolo.
    api.listar.and.returnValue(
      of({
        data: {
          items: [{ ...ticketAbierto, sla_status: 'sin compromiso' as const }],
        },
        meta: {},
      }),
    );

    // Act
    fixture.componentInstance.cargarLista();
    fixture.detectChanges();

    // Assert
    const aviso = fixture.nativeElement.querySelector('[data-testid="sla-sin-compromiso"]');
    expect(aviso).toBeTruthy();
    expect(aviso.textContent).toContain('sin compromiso de tiempo');
  });

  function conHistorial(entradas: HistorialTicketItem[]) {
    api.listar.and.returnValue(of({ data: { items: [ticketAbierto] }, meta: {} }));
    api.obtenerDetalle.and.returnValue(
      of({ data: { ticket: ticketAbierto, historial: entradas }, meta: {} }),
    );
    fixture.componentInstance.cargarLista();
    fixture.detectChanges();
  }

  it('el historial se lee en frases, no en identificadores internos (F20)', () => {
    // Act
    conHistorial([
      {
        id_historial: 1,
        id_reclamo: 9,
        tipo_accion: 'escalado_automatico_sla',
        es_nota_interna: false,
        idusuario: null,
        fecha_accion: 1,
      },
    ]);

    // Assert
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Escalado automáticamente por incumplimiento de SLA');
    expect(texto).not.toContain('escalado_automatico_sla');
  });

  it('marca como «Sistema» lo que no hizo una persona (R-03)', () => {
    // Act — con un guion, una acción automática es indistinguible de un dato
    // que falta, que es justo lo que R-03 quiere poder separar.
    conHistorial([
      {
        id_historial: 1,
        id_reclamo: 9,
        tipo_accion: 'escalado_automatico_sla',
        es_nota_interna: false,
        idusuario: null,
        fecha_accion: 1,
      },
      {
        id_historial: 2,
        id_reclamo: 9,
        tipo_accion: 'comentario',
        mensaje: 'Revisando',
        es_nota_interna: false,
        idusuario: 3,
        fecha_accion: 2,
      },
    ]);

    // Assert — solo la automática lleva la marca
    expect(
      fixture.nativeElement.querySelectorAll('[data-testid="autor-sistema"]').length,
    ).toBe(1);
  });
});
