/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { convertToParamMap, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { EvidenciaApiService } from '../../../evidencia-unidad/services/evidencia-api.service';
import { DespachoApiService } from '../../../despacho/services/despacho-api.service';
import { DetalleAccidentePage } from './detalle-accidente.page';

describe('DetalleAccidentePage', () => {
  let fixture: ComponentFixture<DetalleAccidentePage>;
  let api: jasmine.SpyObj<AccidenteApiService>;
  let evidenciaApi: jasmine.SpyObj<EvidenciaApiService>;
  let despachoApi: jasmine.SpyObj<DespachoApiService>;
  let authApi: jasmine.SpyObj<AuthApiService>;
  let notifications: NotificationService;

  const detalleBase = {
    idaccidente: 'ACC-1',
    estado_actual: 'REGISTRADO',
    descripcion: 'Choque',
    numvehiculos: 2,
    historial_estados: [],
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj('AccidenteApiService', [
      'detalle',
      'actualizar',
      'descartar',
      'escalarSeveridad',
    ]);
    api.detalle.and.returnValue(of<any>({ data: detalleBase, meta: {} }));

    evidenciaApi = jasmine.createSpyObj('EvidenciaApiService', ['listarServidor', 'isFotoItem']);
    evidenciaApi.listarServidor.and.returnValue(of<any>({ data: { items: [] }, meta: {} }));
    evidenciaApi.isFotoItem.and.callFake((item: any): item is any => item?.tipo === 'foto');

    despachoApi = jasmine.createSpyObj('DespachoApiService', ['obtenerEstado']);
    despachoApi.obtenerEstado.and.returnValue(
      of<any>({ data: { unidades_activas: [], intentos: [] }, meta: {} }),
    );

    authApi = jasmine.createSpyObj('AuthApiService', ['hasAnyRole']);
    authApi.hasAnyRole.and.returnValue(true);

    await TestBed.configureTestingModule({
      imports: [DetalleAccidentePage],
      providers: [
        { provide: AccidenteApiService, useValue: api },
        { provide: EvidenciaApiService, useValue: evidenciaApi },
        { provide: DespachoApiService, useValue: despachoApi },
        { provide: AuthApiService, useValue: authApi },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ idaccidente: 'ACC-1' }) } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleAccidentePage);
    notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();
  });

  it('ngOnInit_loads_accidente_detail', () => {
    // Assert
    expect(api.detalle).toHaveBeenCalledWith('ACC-1');
    expect(fixture.componentInstance.accidente()?.idaccidente).toBe('ACC-1');
    expect(fixture.componentInstance.numvehiculos).toBe(2);
  });

  it('guardar_updates_and_reloads', () => {
    // Arrange
    api.actualizar.and.returnValue(of<any>({ data: { message: 'ok' }, meta: {} }));
    fixture.componentInstance.numvehiculos = 3;

    // Act
    fixture.componentInstance.guardar();

    // Assert
    expect(api.actualizar).toHaveBeenCalledWith('ACC-1', {
      numvehiculos: 3,
      numheridos: 0,
      numfallecidos: 0,
      descripcion: 'Choque',
    });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Actualizado', tone: 'success' }),
    ]);
    expect(api.detalle).toHaveBeenCalledTimes(2);
  });

  it('ngOnInit_when_tecnico_role_does_not_load_despacho', () => {
    // Arrange
    despachoApi.obtenerEstado.calls.reset();
    authApi.hasAnyRole.and.returnValue(false);

    // Act
    fixture.componentInstance.cargar();

    // Assert
    expect(despachoApi.obtenerEstado).not.toHaveBeenCalled();
    expect(fixture.componentInstance.puedeVerDespacho()).toBe(false);
  });

  it('descartar_discards_case_and_reloads', () => {
    // Arrange
    api.descartar.and.returnValue(of<any>({ data: { message: 'ok' }, meta: {} }));

    // Act
    fixture.componentInstance.descartar();

    // Assert
    expect(api.descartar).toHaveBeenCalledWith('ACC-1', { motivo: 'Descartado por operador' });
    expect(notifications.toasts()).toEqual([
      jasmine.objectContaining({ message: 'Caso descartado', tone: 'success' }),
    ]);
  });
});
