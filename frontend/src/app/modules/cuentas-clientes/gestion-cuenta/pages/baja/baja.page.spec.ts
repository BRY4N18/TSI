import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { CuentaClienteApiService } from '../../services/cuenta-cliente-api.service';
import { BajaPage } from './baja.page';

describe('BajaPage', () => {
  let fixture: ComponentFixture<BajaPage>;
  let api: jasmine.SpyObj<CuentaClienteApiService>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('CuentaClienteApiService', ['darBaja']);
    api.darBaja.and.returnValue(
      of({
        data: { message: 'Cuenta dada de baja', estado: 'Dado de baja', sesiones_expulsadas: 1 },
        meta: { pagination: null },
      }),
    );

    await TestBed.configureTestingModule({
      imports: [BajaPage],
      providers: [{ provide: CuentaClienteApiService, useValue: api }],
    }).compileComponents();

    fixture = TestBed.createComponent(BajaPage);
    fixture.detectChanges();
  });

  it('calls_darBaja_on_confirm', () => {
    // Arrange
    fixture.componentInstance.motivo = 'Cierre operativo';

    // Act
    fixture.componentInstance.confirmar();

    // Assert
    expect(api.darBaja).toHaveBeenCalledWith(1, 'Cierre operativo');
  });
});
