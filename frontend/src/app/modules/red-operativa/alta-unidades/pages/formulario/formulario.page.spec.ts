/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { CatalogoItem } from '../../../../accidentes/services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../../../accidentes/services/ubicacion-catalogo-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { FormularioPage } from './formulario.page';

const PAISES: CatalogoItem[] = [{ id: 1, nombre: 'Ecuador' }];
const ESTADOS: CatalogoItem[] = [{ id: 10, nombre: 'Pichincha' }];
const CONDADOS: CatalogoItem[] = [{ id: 10, nombre: 'Quito' }];

describe('FormularioPage (alta-unidades)', () => {
  let fixture: ComponentFixture<FormularioPage>;
  let component: FormularioPage;
  let facade: jasmine.SpyObj<UnidadEmergenciaFacadeService>;
  let catalogoApi: jasmine.SpyObj<UbicacionCatalogoApiService>;
  let authApi: jasmine.SpyObj<AuthApiService>;

  const unidad = {
    idunidademergencia: 7,
    idcliente: 1,
    idcondado: 10,
    tipopropiedad: 'Externa' as const,
    placa: 'ABC-123',
    capacidad: null,
    contactoproveedor: 'x',
    unidademergencia: 'Ambulancia 1',
    tipounidademergencia: 'Ambulancia' as const,
    activo: true,
    latitud: null,
    longitud: null,
  };

  async function setup(mode: 'create' | 'edit'): Promise<void> {
    facade = jasmine.createSpyObj('UnidadEmergenciaFacadeService', [
      'obtener',
      'registrar',
      'editar',
      'listar',
      'reenviarInvitacion',
    ]);
    facade.obtener.and.returnValue(of({ ok: true, data: unidad }));
    facade.listar.and.returnValue(
      of({
        ok: true,
        data: { items: [unidad], pagination: { next_cursor: null, limit: 20 } },
      }),
    );

    catalogoApi = jasmine.createSpyObj('UbicacionCatalogoApiService', [
      'listarPaises',
      'listarEstados',
      'listarCondados',
    ]);
    catalogoApi.listarPaises.and.returnValue(of(PAISES));
    catalogoApi.listarEstados.and.returnValue(of(ESTADOS));
    catalogoApi.listarCondados.and.returnValue(of(CONDADOS));

    authApi = jasmine.createSpyObj('AuthApiService', ['getProfile']);
    authApi.getProfile.and.returnValue({ idusuario: 1, gmail: 'proveedor@example.com', roles: [] });

    await TestBed.configureTestingModule({
      imports: [FormularioPage],
      providers: [
        provideRouter([]),
        { provide: UnidadEmergenciaFacadeService, useValue: facade },
        { provide: UbicacionCatalogoApiService, useValue: catalogoApi },
        { provide: AuthApiService, useValue: authApi },
        ListaSeleccionStorage,
        NotificationService,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              data: { mode },
              paramMap: convertToParamMap(
                mode === 'edit' ? { idunidademergencia: '7' } : {},
              ),
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FormularioPage);
    component = fixture.componentInstance;
  }

  it('create_permite_guardar_sin_gmail', async () => {
    // Arrange — SRS 3.5.1 / RF-O39.5-6: gmail es opcional en el alta individual.
    await setup('create');
    fixture.detectChanges();
    expect(component.mode).toBe('create');
    expect(fixture.nativeElement.querySelector('[data-testid="input-gmail"]')).toBeTruthy();
    facade.registrar.and.returnValue(
      of({
        ok: true,
        data: {
          idunidademergencia: 9,
          placa: 'XYZ-1',
          activo: true,
          usuario_creado: false,
          invitacion_enviada: false,
        },
      }),
    );

    // Act
    component.form.idcondado = 1;
    component.form.placa = 'XYZ-1';
    component.form.unidademergencia = 'U1';
    component.form.gmail = '';
    component.guardar();

    // Assert
    expect(component.errorMensaje).toBeFalsy();
    expect(facade.registrar).toHaveBeenCalled();
    const body = facade.registrar.calls.mostRecent().args[0];
    expect(body.gmail).toBeUndefined();
  });

  it('create_muestra_cascada_pais_estado_condado', async () => {
    await setup('create');
    fixture.detectChanges();
    expect(catalogoApi.listarPaises).toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('[data-testid="select-pais"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="select-condado"]')).toBeTruthy();

    component.onPaisChange(1);
    expect(catalogoApi.listarEstados).toHaveBeenCalledWith(1);
    expect(component.estados).toEqual(ESTADOS);

    component.onEstadoChange(10);
    expect(catalogoApi.listarCondados).toHaveBeenCalledWith(10);
    expect(component.condados).toEqual(CONDADOS);

    component.onCondadoChange(10);
    expect(component.form.idcondado).toBe(10);
  });

  it('edit_muestra_guardar_cambios', async () => {
    await setup('edit');
    fixture.detectChanges();
    expect(component.mode).toBe('edit');
    const btn = fixture.nativeElement.querySelector(
      '[data-testid="btn-guardar"]',
    ) as HTMLButtonElement;
    expect(btn.textContent?.trim()).toContain('Guardar cambios');
    expect(facade.obtener).toHaveBeenCalledWith(7);
  });

  it('edit_no_muestra_campos_numericos_de_idcliente_ni_idcondado', async () => {
    await setup('edit');
    fixture.detectChanges();
    const html = fixture.nativeElement as HTMLElement;
    expect(html.textContent).toContain('proveedor@example.com');
    expect(html.querySelector('input[name="idcliente"]')).toBeNull();
  });

  it('edit_preselecciona_cascada_segun_idcondado_de_la_unidad', async () => {
    await setup('edit');
    fixture.detectChanges();
    expect(component.cascadaPais).toBe(1);
    expect(component.cascadaEstado).toBe(10);
    expect(component.form.idcondado).toBe(10);
  });
});
