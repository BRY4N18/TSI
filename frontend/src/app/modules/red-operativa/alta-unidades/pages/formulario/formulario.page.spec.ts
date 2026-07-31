/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import { FormularioPage } from './formulario.page';

describe('FormularioPage (alta-unidades)', () => {
  let fixture: ComponentFixture<FormularioPage>;
  let component: FormularioPage;
  let facade: jasmine.SpyObj<UnidadEmergenciaFacadeService>;

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

    await TestBed.configureTestingModule({
      imports: [FormularioPage],
      providers: [
        provideRouter([]),
        { provide: UnidadEmergenciaFacadeService, useValue: facade },
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

  it('create_exige_gmail_antes_de_guardar', async () => {
    await setup('create');
    fixture.detectChanges();
    expect(component.mode).toBe('create');
    expect(fixture.nativeElement.querySelector('[data-testid="input-gmail"]')).toBeTruthy();

    component.form.idcondado = 1;
    component.form.placa = 'XYZ-1';
    component.form.unidademergencia = 'U1';
    component.form.gmail = '';
    component.guardar();
    expect(component.errorMensaje).toContain('gmail');
    expect(facade.registrar).not.toHaveBeenCalled();
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
});
