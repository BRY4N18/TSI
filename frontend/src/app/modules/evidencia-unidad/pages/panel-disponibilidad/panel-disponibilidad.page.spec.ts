/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { PanelDisponibilidadPage } from './panel-disponibilidad.page';
import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';

describe('PanelDisponibilidadPage', () => {
  const disponibilidadMock = {
    idunidademergencia: 500,
    estado_actual: 'Activa' as const,
    incluido_en_despacho: true,
    fechahora_ultimo_cambio: null,
    placa: 'ABC-123',
    tipounidademergencia: 'Ambulancia',
    capacidad: '4',
    idcondado: 1,
  };

  function setup() {
    TestBed.configureTestingModule({
      imports: [PanelDisponibilidadPage],
      providers: [
        {
          provide: DisponibilidadUnidadApiService,
          useValue: {
            consultarMiDisponibilidad: () =>
              of({ data: disponibilidadMock, meta: { pagination: null } }),
            consultarHistorial: () => of({ data: { items: [] }, meta: { pagination: null } }),
          },
        },
        { provide: NotificationService, useValue: { toast: () => {} } },
      ],
    });
    const fixture = TestBed.createComponent(PanelDisponibilidadPage);
    return fixture;
  }

  it('renders_idcondado_instead_of_zonacobertura', () => {
    // Arrange
    const fixture = setup();

    // Act
    fixture.detectChanges();

    // Assert
    const zona = fixture.nativeElement.querySelector('[data-testid="unidad-zona"]');
    expect(zona.textContent).toContain('1');
  });
});
