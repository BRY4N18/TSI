/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { FacturaApiService } from '../../../suscripciones/services/factura-api.service';
import { TicketApiService } from '../../services/ticket-api.service';
import { MisTicketsPage } from './mis-tickets.page';

const FACTURAS = [
  {
    id_factura: 'f-1',
    numero_factura: 'FAC-202608-00000001',
    periodo: '2026-08',
    estado_pago: 'Pendiente',
  },
  {
    id_factura: 'f-2',
    numero_factura: 'FAC-202607-00000009',
    periodo: '2026-07',
    estado_pago: 'Pagada',
  },
];

describe('MisTicketsPage — disputa de factura (RF-O83.2 / F19)', () => {
  let api: jasmine.SpyObj<TicketApiService>;
  let facturas: jasmine.SpyObj<FacturaApiService>;
  let fixture: ComponentFixture<MisTicketsPage>;
  const html = () => fixture.nativeElement as HTMLElement;

  function montar(queryParams: Record<string, string> = {}): void {
    TestBed.configureTestingModule({
      imports: [MisTicketsPage],
      providers: [
        provideRouter([]),
        { provide: TicketApiService, useValue: api },
        { provide: FacturaApiService, useValue: facturas },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(queryParams) } },
        },
      ],
    });
    fixture = TestBed.createComponent(MisTicketsPage);
    fixture.detectChanges();
  }

  beforeEach(() => {
    api = jasmine.createSpyObj<TicketApiService>('TicketApiService', [
      'listar',
      'listarServicios',
      'registrar',
    ]);
    api.listar.and.returnValue(
      of({ data: { items: [] }, meta: { pagination: null } }) as never,
    );
    api.listarServicios.and.returnValue(of({ data: [], meta: { pagination: null } }) as never);
    api.registrar.and.returnValue(
      of({ data: { id_reclamo: 7, estado: 'Abierto' }, meta: { pagination: null } }) as never,
    );
    facturas = jasmine.createSpyObj<FacturaApiService>('FacturaApiService', ['listar']);
    facturas.listar.and.returnValue(
      of({ data: FACTURAS, meta: { pagination: null } }) as never,
    );
  });

  it('solo ofrece facturas con cobro pendiente', () => {
    // Act — una factura pagada no tiene cargo que discutir
    montar();

    // Assert
    expect(fixture.componentInstance.facturasDisputables().length).toBe(1);
    expect(html().textContent).toContain('FAC-202608-00000001');
    expect(html().textContent).not.toContain('FAC-202607-00000009');
  });

  it('dice que elegir factura detiene el cobro, que es el efecto que importa', () => {
    // Act
    montar();

    // Assert
    expect(html().textContent).toContain('cobro automatico de ese importe se detiene');
  });

  it('llega preseleccionada desde «Disputar este cargo» del historial', () => {
    // Act
    montar({ idfactura: 'f-1' });

    // Assert
    expect(fixture.componentInstance.idfactura).toBe('f-1');
  });

  it('envía idfactura como STRING, porque id_factura es un UUID', () => {
    // Arrange
    montar({ idfactura: 'f-1' });
    fixture.componentInstance.asunto = 'Cargo no reconocido';
    fixture.componentInstance.descripcion = 'El detalle no cuadra con el monto';

    // Act
    fixture.componentInstance.registrar();

    // Assert
    expect(api.registrar.calls.mostRecent().args[0].idfactura).toBe('f-1');
  });

  it('no envía idfactura cuando no se eligió ninguna', () => {
    // Arrange
    montar();
    fixture.componentInstance.asunto = 'Login caído';
    fixture.componentInstance.descripcion = 'No puedo acceder al portal';

    // Act
    fixture.componentInstance.registrar();

    // Assert
    expect('idfactura' in api.registrar.calls.mostRecent().args[0]).toBeFalse();
  });

  it('muestra el motivo real cuando la factura ya tiene una disputa abierta', () => {
    // Arrange — RN-TIC-008; un mensaje genérico haría reintentar a ciegas.
    montar({ idfactura: 'f-1' });
    api.registrar.and.returnValue(
      throwError(() => ({ error: { detail: 'La factura ya tiene una disputa abierta' } })),
    );
    fixture.componentInstance.asunto = 'Cargo no reconocido';
    fixture.componentInstance.descripcion = 'El detalle no cuadra';

    // Act
    fixture.componentInstance.registrar();
    fixture.detectChanges();

    // Assert
    expect(html().querySelector('[data-testid="mensaje"]')?.textContent).toContain(
      'ya tiene una disputa abierta',
    );
  });

  it('que no se puedan listar las facturas no impide abrir un ticket normal', () => {
    // Arrange
    facturas.listar.and.returnValue(throwError(() => new Error('500')));

    // Act
    montar();

    // Assert
    expect(fixture.componentInstance.facturasDisputables()).toEqual([]);
    expect(html().querySelector('[data-testid="mis-tickets"]')).toBeTruthy();
  });
});
