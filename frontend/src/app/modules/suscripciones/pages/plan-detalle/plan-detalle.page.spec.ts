import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { PlanApiService } from '../../services/plan-api.service';
import { PlanDetallePage } from './plan-detalle.page';

describe('PlanDetallePage', () => {
  let fixture: ComponentFixture<PlanDetallePage>;
  let page: PlanDetallePage;
  let planApi: jasmine.SpyObj<PlanApiService>;

  beforeEach(async () => {
    planApi = jasmine.createSpyObj('PlanApiService', ['buscarPorId']);
    planApi.buscarPorId.and.returnValue(
      of({
        idplan: 7,
        nombre: 'Empresarial',
        precio: 299,
        nivel: 'Empresarial',
        activo: true,
        limites: { unidades_max: 100, usuarios_max: 50, api_calls_mes: 50000, api_calls_minuto: 600 },
      }),
    );

    await TestBed.configureTestingModule({
      imports: [PlanDetallePage],
      providers: [
        provideRouter([]),
        { provide: PlanApiService, useValue: planApi },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '7' } } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PlanDetallePage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads plan in read-only mode without save button', () => {
    expect(planApi.buscarPorId).toHaveBeenCalledWith(7);
    expect(page.plan()?.idplan).toBe(7);
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('[data-testid="plan-detalle-readonly"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="btn-guardar-plan-header"]')).toBeFalsy();
    expect(root.textContent).not.toContain('Guardar cambios');
    expect(root.textContent).not.toContain('Publicar plan');
  });

  it('exposes edit CTA to form route', () => {
    const link = fixture.nativeElement.querySelector(
      '[data-testid="btn-editar-desde-detalle"]',
    ) as HTMLAnchorElement | null;
    expect(link).toBeTruthy();
    expect(link?.getAttribute('href') ?? link?.getAttribute('ng-reflect-router-link')).toBeTruthy();
  });
});
