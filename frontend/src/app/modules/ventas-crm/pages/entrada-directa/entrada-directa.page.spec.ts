import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { ConversionApiService } from '../../services/conversion-api.service';
import { EntradaDirectaPage } from './entrada-directa.page';

describe('EntradaDirectaPage', () => {
  let fixture: ComponentFixture<EntradaDirectaPage>;
  let api: jasmine.SpyObj<ConversionApiService>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('ConversionApiService', ['entradaDirecta']);
    api.entradaDirecta.and.returnValue(
      of({
        data: {
          idcliente: 1,
          idprospecto: null,
          nombre: 'X',
          razon_social: 'Y',
          tipo: 'Municipio',
          nit_identificacion: '1',
          estado: 'Activo',
          estado_onboarding: 'Pendiente',
        },
      }),
    );

    await TestBed.configureTestingModule({
      imports: [EntradaDirectaPage],
      providers: [
        provideRouter([]),
        { provide: ConversionApiService, useValue: api },
        { provide: NotificationService, useValue: { toast: jasmine.createSpy('toast') } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(EntradaDirectaPage);
    fixture.detectChanges();
  });

  it('submit_llama_entrada_directa', () => {
    const page = fixture.componentInstance;
    page.form.setValue({
      nombre: 'N',
      razon_social: 'R',
      tipo: 'Municipio',
      nit_identificacion: '999',
      admin_nombres: 'Ana',
      admin_apellidos: 'Admin',
      admin_gmail: 'ana.admin@ex.com',
    });
    page.enviar();
    expect(api.entradaDirecta).toHaveBeenCalledWith(
      jasmine.objectContaining({
        admin_local: { nombres: 'Ana', apellidos: 'Admin', gmail: 'ana.admin@ex.com' },
      }),
    );
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="entrada-directa-ok"]'),
    ).toBeTruthy();
  });

  it('chrome_volver_link_sin_ids_tecnicos', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.textContent).toContain('Volver a la lista');
    expect(root.textContent).not.toMatch(/idcliente|idusuario|idcondado/i);
  });
});
