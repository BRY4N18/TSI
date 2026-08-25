/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { PanelDisponibilidadPage } from './panel-disponibilidad.page';
import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { HistorialEstadoUnidadItem } from '../../services/models/evidencia-unidad.types';

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
    condado: 'Cuauhtémoc',
  };

  function setup(historialItems: HistorialEstadoUnidadItem[] = []) {
    const consultarHistorial = jasmine.createSpy('consultarHistorial').and.returnValue(
      of({ data: { items: historialItems }, meta: { pagination: null } }),
    );
    TestBed.configureTestingModule({
      imports: [PanelDisponibilidadPage],
      providers: [
        {
          provide: DisponibilidadUnidadApiService,
          useValue: {
            consultarMiDisponibilidad: () =>
              of({ data: disponibilidadMock, meta: { pagination: null } }),
            consultarHistorial,
          },
        },
        { provide: NotificationService, useValue: { toast: () => {} } },
      ],
    });
    const fixture = TestBed.createComponent(PanelDisponibilidadPage);
    return { fixture, consultarHistorial };
  }

  it('renders_nombre_de_condado_no_el_id', () => {
    // Arrange
    const { fixture } = setup();

    // Act
    fixture.detectChanges();

    // Assert
    const zona = fixture.nativeElement.querySelector('[data-testid="unidad-zona"]');
    expect(zona.textContent).toContain('Cuauhtémoc');
    expect(zona.textContent.trim()).not.toBe('1');
  });

  it('historial_pide_y_pinta_solo_los_10_mas_recientes', () => {
    // Arrange
    const items = Array.from({ length: 15 }, (_, i) => ({
      idhistorialestadosunidadesemergencias: i + 1,
      idunidademergencia: 500,
      estadoanterior: 'Activa' as const,
      estadonuevo: 'Ocupada' as const,
      fechahora: 1_700_000_000_000 + i,
      idusuario: 6,
    }));
    const { fixture, consultarHistorial } = setup(items);

    // Act
    fixture.detectChanges();

    // Assert
    expect(consultarHistorial).toHaveBeenCalledWith(500, { limit: 10 });
    const filas = fixture.nativeElement.querySelectorAll('[data-testid="historial-tabla"] tbody tr');
    expect(filas.length).toBe(10);
  });
});
