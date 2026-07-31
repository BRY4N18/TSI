import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError, TimeoutError } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';
import { ListadoProspectosPage } from './listado-prospectos.page';

describe('ListadoProspectosPage', () => {
  let fixture: ComponentFixture<ListadoProspectosPage>;
  let page: ListadoProspectosPage;
  let api: jasmine.SpyObj<ProspectoApiService>;

  const sample = {
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
    api = jasmine.createSpyObj('ProspectoApiService', ['listar']);
    api.listar.and.returnValue(
      of({
        data: [sample],
        meta: { pagination: { next_cursor: 2, limit: 20 } },
      }),
    );

    await TestBed.configureTestingModule({
      imports: [ListadoProspectosPage],
      providers: [
        provideRouter([]),
        { provide: ProspectoApiService, useValue: api },
        {
          provide: AuthApiService,
          useValue: { hasRole: (r: string) => r === 'Administrador' },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ListadoProspectosPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga_con_limit_20', () => {
    expect(api.listar).toHaveBeenCalledWith(jasmine.objectContaining({ limit: 20, cursor: null }));
  });

  it('filtros_resetean_cursor', () => {
    page.cursor = 9;
    page.filtroEstado = 'activo';
    page.onFiltroChange();
    expect(api.listar).toHaveBeenCalledWith(
      jasmine.objectContaining({ cursor: null, activo: true, limit: 20 }),
    );
  });

  it('admin_ve_cta_entrada_directa_y_ojo_sin_lapiz', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('[data-testid="btn-entrada-directa"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="btn-ver-prospecto"]')).toBeTruthy();
    expect(root.querySelector('[aria-label="Editar"]')).toBeNull();
    expect(root.querySelector('[data-testid="btn-editar-prospecto"]')).toBeNull();
  });

  it('timeout_muestra_reintentar', fakeAsync(() => {
    api.listar.and.returnValue(throwError(() => new TimeoutError()));
    page.cargar({ resetCursor: true });
    tick();
    fixture.detectChanges();
    expect(page.error()).toContain('tardó demasiado');
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="btn-reintentar-lista"]'),
    ).toBeTruthy();
  }));
});
