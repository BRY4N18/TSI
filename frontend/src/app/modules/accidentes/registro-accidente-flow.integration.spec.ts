/** @marker integration */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NotificationService } from '../../shared/notifications/notification.service';
import { RegistroAccidentePage } from './pages/registro-accidente/registro-accidente.page';

function fillValidForm(component: RegistroAccidentePage, descripcion: string): void {
  component.form.setValue({
    latitudinicio: 19.4326,
    longitudinicio: -99.1332,
    fechahoraaccidente: '2026-07-12T10:00',
    idseveridad: 2,
    descripcion,
    idcalle: 1,
    codigopostal: '',
    numvehiculos: 0,
    numheridos: 0,
    numvictimas: 0,
    numfallecidos: 0,
    idtiporeportado: null,
    registroRetrospectivo: false,
    justificacionRetrospectiva: '',
  });
}

describe('Registro de accidente - integration flow', () => {
  let fixture: ComponentFixture<RegistroAccidentePage>;
  let httpMock: HttpTestingController;
  let notifications: NotificationService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RegistroAccidentePage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(RegistroAccidentePage);
    httpMock = TestBed.inject(HttpTestingController);
    notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();

    // El constructor carga el catálogo de países para la cascada manual de ubicación.
    httpMock.expectOne('/api/v1/accidentes/paises').flush({
      data: [],
      meta: { pagination: null },
    });
  });

  afterEach(() => httpMock.verify());

  it('mover_el_pin_del_mapa_geocodifica_y_registrar_usa_el_idcalle_resuelto', () => {
    // Arrange
    jasmine.clock().install();
    fillValidForm(fixture.componentInstance, 'Choque en interseccion');

    // Act: el operador mueve el pin en el mapa (onCoordsChange), lo que dispara
    // geocodificación automática tras el debounce
    fixture.componentInstance.onCoordsChange({ lat: 19.4326, lng: -99.1332 });
    jasmine.clock().tick(600);
    jasmine.clock().uninstall();

    const geoReq = httpMock.expectOne(
      (req) => req.url === '/api/v1/accidentes/geocodificacion-inversa',
    );
    expect(geoReq.request.method).toBe('GET');
    geoReq.flush({
      data: { idcalle: 42, ubicacion: {}, en_cobertura_operativa: true },
      meta: { pagination: null },
    });

    fixture.componentInstance.registrar(false);

    // Assert: registration request uses the resolved idcalle and reports the outcome
    const registrarReq = httpMock.expectOne(
      (req) => req.url === '/api/v1/accidentes' && req.method === 'POST',
    );
    expect(registrarReq.request.body.idcalle).toBe(42);
    registrarReq.flush({
      data: {
        message: 'Registrado',
        idaccidente: 'ACC-100',
        estado: 'REPORTADO',
        advertencias: [],
        fechahoramodificado: Date.now(),
      },
      meta: { pagination: null },
    });

    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Accidente registrado (ACC-100)', tone: 'success' }),
    ]);
  });

  it('registrar_cuando_hay_advertencia_de_duplicado_permite_confirmar_el_borrador', () => {
    // Arrange
    fillValidForm(fixture.componentInstance, 'Posible duplicado');

    // Act: registration returns a BORRADOR with a duplicate warning
    fixture.componentInstance.registrar(false);

    const registrarReq = httpMock.expectOne(
      (req) => req.url === '/api/v1/accidentes' && req.method === 'POST',
    );
    registrarReq.flush({
      data: {
        message: 'Requiere confirmacion',
        idaccidente: 'ACC-101',
        estado: 'BORRADOR',
        advertencias: [{ code: 'duplicado_posible', detail: 'Similar a ACC-050' }],
        fechahoramodificado: Date.now(),
      },
      meta: { pagination: null },
    });

    expect(fixture.componentInstance.advertencias().length).toBe(1);

    // Act: operator confirms the draft despite the warning
    fixture.componentInstance.confirmarBorrador();

    // Assert
    const confirmarReq = httpMock.expectOne(
      '/api/v1/accidentes/ACC-101/confirmar-reporte',
    );
    expect(confirmarReq.request.method).toBe('POST');
    expect(confirmarReq.request.body).toEqual({ confirmacion: true });
    confirmarReq.flush({
      data: { message: 'Reporte confirmado', idaccidente: 'ACC-101', estado: 'REPORTADO' },
      meta: { pagination: null },
    });

    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Accidente registrado (ACC-101)', tone: 'success' }),
      jasmine.objectContaining({ message: 'Reporte confirmado', tone: 'success' }),
    ]);
    expect(fixture.componentInstance.advertencias()).toEqual([]);
  });

  it('registrar_cuando_backend_responde_409_con_ids_de_fusion_abre_el_dialogo', () => {
    // Arrange
    fillValidForm(fixture.componentInstance, 'Choque reportado dos veces');

    // Act
    fixture.componentInstance.registrar(false);
    const registrarReq = httpMock.expectOne(
      (req) => req.url === '/api/v1/accidentes' && req.method === 'POST',
    );
    registrarReq.flush(
      {
        error: 'conflict',
        detail: 'Accidente duplicado',
        code: 'duplicado_posible',
        idaccidente_similar: 'ACC-050',
        idaccidente_principal_sugerido: 'ACC-050',
        idaccidente_duplicado_sugerido: 'ACC-102',
      },
      { status: 409, statusText: 'Conflict' },
    );

    // Assert: el conflicto queda disponible para que el diálogo de fusión lo consuma
    expect(fixture.componentInstance.duplicadoConflicto()?.idaccidente_duplicado_sugerido).toBe(
      'ACC-102',
    );

    // Act: operador confirma la fusión
    fixture.componentInstance.confirmarFusion('ACC-050');
    const fusionarReq = httpMock.expectOne('/api/v1/accidentes/ACC-102/fusionar');
    expect(fusionarReq.request.method).toBe('POST');
    expect(fusionarReq.request.body).toEqual({
      idaccidenteprincipal: 'ACC-050',
      confirmacion: true,
    });
    fusionarReq.flush({
      data: {
        message: 'Reportes fusionados exitosamente',
        idaccidente_duplicado: 'ACC-102',
        idaccidente_principal: 'ACC-050',
        estado_duplicado: 'FUSIONADO',
      },
      meta: { pagination: null },
    });

    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Reportes fusionados exitosamente', tone: 'success' }),
    ]);
    expect(fixture.componentInstance.duplicadoConflicto()).toBeNull();
  });

  it('registrar_cuando_backend_responde_409_sin_ids_de_fusion_muestra_error_generico', () => {
    // Arrange
    fillValidForm(fixture.componentInstance, 'Choque reportado dos veces');

    // Act
    fixture.componentInstance.registrar(false);
    const registrarReq = httpMock.expectOne(
      (req) => req.url === '/api/v1/accidentes' && req.method === 'POST',
    );
    registrarReq.flush(
      {
        error: 'conflict',
        detail: 'Accidente duplicado',
        code: 'duplicado_posible',
        idaccidente_similar: 'ACC-050',
        idaccidente_principal_sugerido: 'ACC-050',
        idaccidente_duplicado_sugerido: null,
      },
      { status: 409, statusText: 'Conflict' },
    );

    // Assert
    expect(notifications.activeAlert()).toEqual(
      jasmine.objectContaining({ title: 'Error al registrar' }),
    );
  });
});
