/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ExpedienteClienteApiService } from '../../services/expediente-cliente-api.service';
import { ListaExpedientesPage } from './lista-expedientes.page';

function envelope(items: unknown[], next: string | null = null) {
  return { data: { items, next_cursor: next }, meta: { pagination: null } } as any;
}

const EXPEDIENTE = {
  idaccidente: 'ACC-9',
  fecha: 1785542765994,
  estado: 'CERRADO',
  severidad: 3,
  ubicacion: 'Av. Reforma, Ciudad de México',
  tiempos: {},
  unidad_principal: 'Ambulancia 01',
};

describe('ListaExpedientesPage', () => {
  let fixture: ComponentFixture<ListaExpedientesPage>;
  let component: ListaExpedientesPage;
  let api: jasmine.SpyObj<ExpedienteClienteApiService>;
  let router: Router;

  beforeEach(async () => {
    api = jasmine.createSpyObj('ExpedienteClienteApiService', [
      'listar',
      'obtenerDetalle',
      'descargarPdf',
    ]);
    api.listar.and.returnValue(of(envelope([])));

    await TestBed.configureTestingModule({
      imports: [ListaExpedientesPage],
      providers: [
        { provide: ExpedienteClienteApiService, useValue: api },
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ListaExpedientesPage);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
  });

  it('carga_los_expedientes_al_iniciar', () => {
    // Act
    fixture.detectChanges();

    // Assert
    expect(api.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ limit: 20, cursor: undefined }),
    );
  });

  it('renderiza_la_tabla_con_los_expedientes_del_cliente', () => {
    // Arrange
    api.listar.and.returnValue(of(envelope([EXPEDIENTE])));

    // Act
    fixture.detectChanges();

    // Assert
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="tabla-expedientes"]')).toBeTruthy();
    expect(root.textContent).toContain('ACC-9');
    expect(root.textContent).toContain('Grave');
  });

  it('sin_expedientes_muestra_estado_vacio', () => {
    // Act
    fixture.detectChanges();

    // Assert
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="empty-state"]')).toBeTruthy();
  });

  it('error_muestra_estado_de_error_con_reintentar', () => {
    // Arrange
    api.listar.and.returnValue(throwError(() => new Error('boom')));

    // Act
    fixture.detectChanges();

    // Assert
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="btn-reintentar-lista"]')).toBeTruthy();
  });

  it('paginaSiguiente_pide_la_pagina_siguiente_con_el_cursor', () => {
    // Arrange
    api.listar.and.returnValue(of(envelope([EXPEDIENTE], 'ACC-9')));
    fixture.detectChanges();
    api.listar.calls.reset();

    // Act
    component.paginaSiguiente();

    // Assert
    expect(api.listar).toHaveBeenCalledWith(jasmine.objectContaining({ cursor: 'ACC-9' }));
  });

  it('ver_detalle_navega_al_expediente', () => {
    // Arrange
    api.listar.and.returnValue(of(envelope([EXPEDIENTE])));
    fixture.detectChanges();

    // Act
    component.verDetalle('ACC-9');

    // Assert
    expect(router.navigate).toHaveBeenCalledWith(['/seguimiento/expedientes', 'ACC-9']);
  });
});
