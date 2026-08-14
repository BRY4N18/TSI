/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { EvidenciaApiService } from '../../services/evidencia-api.service';
import { EvidenciaSyncSchedulerService } from '../../services/evidencia-sync-scheduler.service';
import { GaleriaEvidenciasPage } from './galeria-evidencias.page';

describe('GaleriaEvidenciasPage', () => {
  let fixture: ComponentFixture<GaleriaEvidenciasPage>;
  let authApi: jasmine.SpyObj<AuthApiService>;

  async function setup(roles: string[]): Promise<void> {
    const api = jasmine.createSpyObj('EvidenciaApiService', [
      'listarConPendientesLocales',
      'isFotoItem',
      'isNotaItem',
      'sincronizarPendientes',
    ]);
    api.listarConPendientesLocales.and.returnValue(of([]));
    api.isFotoItem.and.returnValue(false);
    api.isNotaItem.and.returnValue(false);

    const scheduler = jasmine.createSpyObj('EvidenciaSyncSchedulerService', ['registrarCaso']);
    authApi = jasmine.createSpyObj('AuthApiService', ['hasAnyRole']);
    authApi.hasAnyRole.and.callFake((pedidos: string[]) =>
      pedidos.some((r) => roles.includes(r)),
    );

    await TestBed.configureTestingModule({
      imports: [GaleriaEvidenciasPage],
      providers: [
        { provide: EvidenciaApiService, useValue: api },
        { provide: EvidenciaSyncSchedulerService, useValue: scheduler },
        { provide: AuthApiService, useValue: authApi },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: { get: () => 'ACC-1' },
              queryParamMap: { get: () => null },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(GaleriaEvidenciasPage);
    fixture.detectChanges();
  }

  it('la unidad vuelve a su seguimiento, no al detalle del accidente', async () => {
    // Arrange / Act — el detalle del accidente es pantalla de Operador: enviar
    // ahi a la unidad la deja en "Acceso denegado", sin vuelta atras.
    await setup(['Unidad']);

    // Assert
    expect(fixture.componentInstance.rutaVolver()).toEqual(['/seguimiento/mi-seguimiento']);
    expect(fixture.componentInstance.etiquetaVolver()).toBe('Volver a mi seguimiento');
  });

  it('el operador vuelve al detalle del accidente', async () => {
    // Arrange / Act
    await setup(['Operador']);

    // Assert
    expect(fixture.componentInstance.rutaVolver()).toEqual(['/accidentes', 'ACC-1']);
    expect(fixture.componentInstance.etiquetaVolver()).toBe('Volver al accidente');
  });
});
