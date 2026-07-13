/** @marker unit */
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

    sse = jasmine.createSpyObj('SeguimientoSseService', ['connect']);
    sse.connect.and.returnValue(EMPTY);

    await TestBed.configureTestingModule({
      imports: [MapaSeguimientoPage],
      providers: [
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

  it('renders_page_title', () => {
    // Assert
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Mapa de seguimiento');
  });

  it('ngAfterViewInit_carga_el_snapshot_inicial', () => {
    // Assert
    expect(api.obtenerMapa).toHaveBeenCalled();
  });
});
