import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { ConversionApiService } from '../../services/conversion-api.service';
import { PipelineApiService } from '../../services/pipeline-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';
import { DetalleProspectoPage } from './detalle-prospecto.page';

describe('DetalleProspectoPage', () => {
  let fixture: ComponentFixture<DetalleProspectoPage>;
  let page: DetalleProspectoPage;
  let prospectoApi: jasmine.SpyObj<ProspectoApiService>;
  let pipelineApi: jasmine.SpyObj<PipelineApiService>;
  let conversionApi: jasmine.SpyObj<ConversionApiService>;

  const base = {
    idprospecto: 1,
    nombres: 'Ana',
    apellidos: 'Pérez',
    gmail: 'a@x.com',
    empresa: 'Acme',
    tipo_organizacion: 'Privado' as const,
    cargo: 'Gerente',
    telefono: '099',
    como_nos_conocio: 'web',
    etapa_actual: 'Nuevo' as const,
    idusuario: 20,
    activo: true,
    motivo_inactividad: null,
  };

  beforeEach(async () => {
    prospectoApi = jasmine.createSpyObj('ProspectoApiService', ['obtener', 'asignar']);
    pipelineApi = jasmine.createSpyObj('PipelineApiService', ['registrarTransicion']);
    conversionApi = jasmine.createSpyObj('ConversionApiService', ['convertir']);
    prospectoApi.obtener.and.returnValue(of({ data: base }));

    await TestBed.configureTestingModule({
      imports: [DetalleProspectoPage],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '1' } } },
        },
        { provide: ProspectoApiService, useValue: prospectoApi },
        { provide: PipelineApiService, useValue: pipelineApi },
        { provide: ConversionApiService, useValue: conversionApi },
        {
          provide: AuthApiService,
          useValue: {
            hasRole: () => true,
            getProfile: () => ({ idusuario: 1, gmail: 'a@tsi.com', roles: ['Administrador'] }),
          },
        },
        { provide: NotificationService, useValue: { toast: jasmine.createSpy('toast') } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleProspectoPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('muestra_titulo_detalles_sin_guardar_ficha', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.textContent).toContain('Detalles');
    expect(root.querySelector('[data-testid="workpanel-titulo"]')).toBeTruthy();
    expect(root.textContent).not.toMatch(/Guardar cambios|Guardar ficha/i);
    expect(root.querySelector('a[routerlink="/ventas-crm/prospectos"]') || root.querySelector('a[href]')).toBeTruthy();
    expect(root.querySelector('input[disabled]')).toBeNull();
  });

  it('conversion_solo_en_negociacion', () => {
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="btn-convertir"]'),
    ).toBeNull();
    prospectoApi.obtener.and.returnValue(
      of({ data: { ...base, etapa_actual: 'Negociación' as const } }),
    );
    page.cargar();
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="btn-convertir"]'),
    ).toBeTruthy();
  });

  it('409_muestra_refrescar', () => {
    pipelineApi.registrarTransicion.and.returnValue(
      throwError(() => ({ status: 409, error: { detail: 'Conflicto' } })),
    );
    page.avanzar();
    fixture.detectChanges();
    expect(page.actionError()).toContain('Conflicto');
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="btn-refrescar-prospecto"]'),
    ).toBeTruthy();
  });
});
