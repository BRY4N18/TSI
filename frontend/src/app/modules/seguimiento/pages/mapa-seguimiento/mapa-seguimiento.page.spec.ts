/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EMPTY, of } from 'rxjs';

import { SeguimientoApiService } from '../../services/seguimiento-api.service';
import { SeguimientoSseService } from '../../services/seguimiento-sse.service';
import { MapaSeguimientoPage } from './mapa-seguimiento.page';

describe('MapaSeguimientoPage', () => {
  let fixture: ComponentFixture<MapaSeguimientoPage>;
  let api: jasmine.SpyObj<SeguimientoApiService>;
  let sse: jasmine.SpyObj<SeguimientoSseService>;

  beforeEach(async () => {
    api = jasmine.createSpyObj('SeguimientoApiService', ['obtenerMapa']);
    api.obtenerMapa.and.returnValue(
      of<any>({ data: { accidentes_activos: [], unidades: [] }, meta: {} }),
    );

    sse = jasmine.createSpyObj('SeguimientoSseService', ['connect', 'connectResiliente']);
    sse.connect.and.returnValue(EMPTY);
    sse.connectResiliente.and.returnValue(EMPTY);

    await TestBed.configureTestingModule({
      imports: [MapaSeguimientoPage],
      providers: [
        // RutaService (inyectado por la página para el trazado de rutas OSRM)
        // depende de HttpClient.
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: SeguimientoApiService, useValue: api },
        { provide: SeguimientoSseService, useValue: sse },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MapaSeguimientoPage);
    fixture.detectChanges();
  });

  it('creates_the_component', () => {
    // Assert
    expect(fixture.componentInstance).toBeTruthy();
  });

  // La página es un mapa a sangre completa: el rótulo "Mapa de seguimiento" vive
  // en la navegación, no en el propio contenido. Lo que sí debe renderizar es la
  // leyenda de severidades y estados de unidad.
  it('renders_leyenda_de_severidades_y_estados_de_unidad', () => {
    // Assert
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    for (const etiqueta of ['Fatal', 'Grave', 'Moderado', 'Leve', 'Unidad activa']) {
      expect(text).toContain(etiqueta);
    }
  });

  it('ngAfterViewInit_carga_el_snapshot_inicial', () => {
    // Assert
    expect(api.obtenerMapa).toHaveBeenCalled();
  });
});
