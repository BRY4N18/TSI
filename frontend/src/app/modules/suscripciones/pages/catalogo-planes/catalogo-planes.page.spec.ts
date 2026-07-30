import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { PlanApiService } from '../../services/plan-api.service';
import { CatalogoPlanesPage } from './catalogo-planes.page';

describe('CatalogoPlanesPage', () => {
  let fixture: ComponentFixture<CatalogoPlanesPage>;
  let page: CatalogoPlanesPage;
  let planApi: jasmine.SpyObj<PlanApiService>;

  beforeEach(async () => {
    planApi = jasmine.createSpyObj('PlanApiService', ['listar', 'actualizar']);
    planApi.listar.and.returnValue(
      of({
        data: [
          {
            idplan: 1,
            nombre: 'Profesional',
            precio: 149,
            nivel: 'Profesional',
            activo: true,
            limites: { unidades_max: 25, usuarios_max: 10, api_calls_mes: 10000 },
          },
        ],
      }),
    );
    planApi.actualizar.and.returnValue(of({ data: { idplan: 1, activo: false } }));

    await TestBed.configureTestingModule({
      imports: [CatalogoPlanesPage],
      providers: [
        provideRouter([]),
        { provide: PlanApiService, useValue: planApi },
        {
          provide: AuthApiService,
          useValue: { hasRole: (r: string) => r === 'DirectorEstrategia' },
        },
        {
          provide: NotificationService,
          useValue: { toast: jasmine.createSpy('toast') },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoPlanesPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads all plans for Director', () => {
    expect(page.esDirector()).toBe(true);
    expect(planApi.listar).toHaveBeenCalledWith(false);
  });

  it('requires confirmation before deactivating', () => {
    page.pedirDesactivar({ idplan: 1, nombre: 'Profesional', activo: true });
    expect(page.planPendienteDesactivar()?.idplan).toBe(1);
    expect(planApi.actualizar).not.toHaveBeenCalled();
    page.confirmarDesactivar();
    expect(planApi.actualizar).toHaveBeenCalled();
  });
});
