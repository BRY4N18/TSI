/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { CatalogoItem } from '../../../../accidentes/services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../../../accidentes/services/ubicacion-catalogo-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { DetallePage } from './detalle.page';

const PAISES: CatalogoItem[] = [{ id: 1, nombre: 'Ecuador' }];
const ESTADOS: CatalogoItem[] = [{ id: 10, nombre: 'Pichincha' }];
const CONDADOS: CatalogoItem[] = [{ id: 10, nombre: 'Quito' }];

describe('DetallePage (alta-unidades)', () => {
  let fixture: ComponentFixture<DetallePage>;
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

  beforeEach(async () => {
    facade = jasmine.createSpyObj('UnidadEmergenciaFacadeService', ['obtener']);
    facade.obtener.and.returnValue(of({ ok: true, data: unidad }));

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
      imports: [DetallePage],
      providers: [
        provideRouter([]),
        { provide: UnidadEmergenciaFacadeService, useValue: facade },
        { provide: UbicacionCatalogoApiService, useValue: catalogoApi },
        { provide: AuthApiService, useValue: authApi },
        ListaSeleccionStorage,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => '7' } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetallePage);
  });

  it('muestra_detalles_sin_boton_guardar', () => {
    fixture.detectChanges();
    const html = fixture.nativeElement as HTMLElement;
    expect(html.querySelector('[data-testid="detalle-page"]')).toBeTruthy();
    expect(html.textContent).toContain('Detalles');
    expect(html.querySelector('[data-testid="btn-guardar"]')).toBeNull();
    expect(html.querySelector('[data-testid="detalle-sin-guardar"]')).toBeTruthy();
    expect(html.querySelector('[data-testid="detalle-campos"]')).toBeTruthy();
    expect(html.querySelector('[data-testid="btn-editar-desde-detalle"]')).toBeTruthy();
  });

  it('muestra_dueno_y_condado_legibles_en_vez_de_ids', () => {
    fixture.detectChanges();
    const html = fixture.nativeElement as HTMLElement;
    expect(html.textContent).toContain('proveedor@example.com');
    expect(html.textContent).toContain('Quito');
    expect(html.querySelector('input[disabled]')).toBeNull();
  });
});
