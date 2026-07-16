/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import * as L from 'leaflet';
import { of } from 'rxjs';

import { RutaService } from '../../services/ruta.service';
import { ReadOnlyRouteMapComponent } from './read-only-route-map.component';

describe('ReadOnlyRouteMapComponent', () => {
  let fixture: ComponentFixture<ReadOnlyRouteMapComponent>;
  let rutaService: jasmine.SpyObj<RutaService>;

  beforeEach(async () => {
    rutaService = jasmine.createSpyObj('RutaService', ['calcularRuta']);
    rutaService.calcularRuta.and.returnValue(of([L.latLng(19.43, -99.13), L.latLng(19.44, -99.14)]));

    await TestBed.configureTestingModule({
      imports: [ReadOnlyRouteMapComponent],
      providers: [{ provide: RutaService, useValue: rutaService }],
    }).compileComponents();

    fixture = TestBed.createComponent(ReadOnlyRouteMapComponent);
  });

  afterEach(() => {
    fixture.destroy();
  });

  it('ngAfterViewInit_when_solo_destino_no_calcula_ruta', () => {
    // Arrange
    fixture.componentInstance.destinoLat = 19.43;
    fixture.componentInstance.destinoLng = -99.13;

    // Act
    fixture.detectChanges();

    // Assert
    expect(rutaService.calcularRuta).not.toHaveBeenCalled();
  });

  it('ngAfterViewInit_when_origen_y_destino_calcula_ruta', () => {
    // Arrange
    fixture.componentInstance.destinoLat = 19.43;
    fixture.componentInstance.destinoLng = -99.13;
    fixture.componentInstance.origenLat = 19.44;
    fixture.componentInstance.origenLng = -99.14;

    // Act
    fixture.detectChanges();

    // Assert
    expect(rutaService.calcularRuta).toHaveBeenCalledTimes(1);
    const [origenArg, destinoArg] = rutaService.calcularRuta.calls.mostRecent().args;
    expect(origenArg.lat).toBe(19.44);
    expect(destinoArg.lat).toBe(19.43);
  });

  it('ngOnChanges_when_origen_aparece_despues_calcula_ruta', () => {
    // Arrange
    fixture.componentInstance.destinoLat = 19.43;
    fixture.componentInstance.destinoLng = -99.13;
    fixture.detectChanges();
    expect(rutaService.calcularRuta).not.toHaveBeenCalled();

    // Act
    fixture.componentInstance.origenLat = 19.44;
    fixture.componentInstance.origenLng = -99.14;
    fixture.componentInstance.ngOnChanges({
      origenLat: { currentValue: 19.44, previousValue: null, firstChange: false, isFirstChange: () => false },
    } as any);

    // Assert
    expect(rutaService.calcularRuta).toHaveBeenCalledTimes(1);
  });
});
