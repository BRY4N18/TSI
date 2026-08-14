/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { Factura } from '../../services/models/suscripciones.types';
import { FacturaApiService } from '../../services/factura-api.service';
import { HistorialFacturasPage } from './historial-facturas.page';

function factura(over: Partial<Factura> = {}): Factura {
  return {
    id_factura: 'f-1',
    numero_factura: 'FAC-202608-00000001',
    periodo: '2026-08',
    estado_pago: 'Pendiente',
    monto_base: 63.5,
    impuestos: 0,
    monto_total: 63.5,
    fecha_emision: 1786600000000,
    reintentos: 0,
    ...over,
  } as Factura;
}

describe('HistorialFacturasPage — disputa de factura (RF-O83.2 / F19)', () => {
  let api: jasmine.SpyObj<FacturaApiService>;
  let fixture: ComponentFixture<HistorialFacturasPage>;
  const html = () => fixture.nativeElement as HTMLElement;

  function montar(f: Factura): void {
    api.listar.and.returnValue(of({ data: [f], meta: { pagination: null } }) as never);
    api.obtener.and.returnValue(of({ data: f, meta: { pagination: null } }) as never);
    TestBed.configureTestingModule({
      imports: [HistorialFacturasPage],
      providers: [provideRouter([]), { provide: FacturaApiService, useValue: api }],
    });
    fixture = TestBed.createComponent(HistorialFacturasPage);
    fixture.detectChanges();
    fixture.componentInstance.verDetalle(f);
    fixture.detectChanges();
  }

  beforeEach(() => {
    api = jasmine.createSpyObj<FacturaApiService>('FacturaApiService', ['listar', 'obtener']);
  });

  it('ofrece disputar la factura con cobro pendiente y la enlaza al ticket', () => {
    // Act — sin esta puerta, el backend aceptaba la disputa y el cliente no
    // tenía por dónde abrirla.
    montar(factura());

    // Assert
    const boton = html().querySelector('[data-testid="btn-disputar"]') as HTMLAnchorElement;
    expect(boton).toBeTruthy();
    expect(boton.getAttribute('href')).toContain('/soporte-cliente/mis-tickets');
    expect(boton.getAttribute('href')).toContain('idfactura=f-1');
  });

  it('dice que disputar detiene el cobro, que es la razón para hacerlo', () => {
    // Act
    montar(factura());

    // Assert
    expect(html().textContent).toContain('no se te reintentara el cobro');
  });

  it('no ofrece disputar una factura ya pagada', () => {
    // Act — no queda cargo que discutir
    montar(factura({ estado_pago: 'Pagada' }));

    // Assert
    expect(html().querySelector('[data-testid="btn-disputar"]')).toBeNull();
  });

  it('en una factura ya en disputa explica que el cobro está detenido, en vez de ofrecer una segunda', () => {
    // Act — el backend rechaza la segunda con 422 (RN-TIC-008): ofrecer el
    // botón solo llevaría al error.
    montar(factura({ estado_pago: 'En disputa' }));

    // Assert
    expect(html().querySelector('[data-testid="btn-disputar"]')).toBeNull();
    const aviso = html().querySelector('[data-testid="aviso-en-disputa"]');
    expect(aviso?.textContent).toContain('cobro esta detenido');
  });
});
