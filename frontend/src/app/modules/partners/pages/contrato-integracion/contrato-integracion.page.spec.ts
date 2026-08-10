/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ContratoApiService } from '../../services/contrato-api.service';
import type { ContratoIntegracion, VersionContrato } from '../../services/models/partner.types';
import { ContratoIntegracionPage } from './contrato-integracion.page';

function version(over: Partial<VersionContrato> = {}): VersionContrato {
  return {
    idversion: 1,
    id_servicio: 1,
    version: 'v1',
    estado: 'vigente',
    spec_url: '',
    fecha_publicacion: 1_700_000_000_000,
    fecha_retiro: 0,
    ...over,
  };
}

function contrato(over: Partial<ContratoIntegracion> = {}): ContratoIntegracion {
  return { ...version(), versiones: [version()], ...over };
}

const sobre = (data: ContratoIntegracion) => ({ data, meta: { pagination: null } });

describe('ContratoIntegracionPage', () => {
  let api: jasmine.SpyObj<ContratoApiService>;
  let fixture: ComponentFixture<ContratoIntegracionPage>;

  function montar(): void {
    TestBed.configureTestingModule({
      imports: [ContratoIntegracionPage],
      providers: [{ provide: ContratoApiService, useValue: api }],
    });
    fixture = TestBed.createComponent(ContratoIntegracionPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    api = jasmine.createSpyObj<ContratoApiService>('ContratoApiService', ['consultar']);
    api.consultar.and.returnValue(of(sobre(contrato())) as never);
  });

  describe('versionado por servicio (FR-UI-028)', () => {
    it('consulta siempre indicando el servicio', () => {
      // Act
      montar();

      // Assert
      expect(api.consultar).toHaveBeenCalledWith(1);
    });

    it('el servicio se elige por nombre legible, nunca tecleando su id', () => {
      // Act
      montar();

      // Assert
      const selector = html().querySelector('[data-testid="selector-servicio"]');
      expect(selector?.tagName).toBe('SELECT');
      expect(selector?.textContent).toContain('API Despacho');
    });

    it('cambiar de servicio reconsulta con el nuevo id', () => {
      // Dos servicios pueden tener ambos una «v1» y no ser la misma cosa.
      // Arrange
      montar();
      api.consultar.calls.reset();

      // Act
      fixture.componentInstance.cambiarServicio(2);

      // Assert
      expect(api.consultar).toHaveBeenCalledWith(2);
    });

    it('destaca la versión vigente', () => {
      // Arrange
      api.consultar.and.returnValue(of(sobre(contrato({ version: 'v2' }))) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="version-vigente"]')?.textContent).toContain('v2');
    });

    it('lista también las soportadas, que es lo que permite planificar la migración', () => {
      // Arrange
      api.consultar.and.returnValue(
        of(
          sobre(
            contrato({
              version: 'v2',
              versiones: [
                version({ idversion: 1, version: 'v1', estado: 'soportada' }),
                version({ idversion: 2, version: 'v2', estado: 'vigente' }),
              ],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      const lista = html().querySelector('[data-testid="lista-versiones"]');
      expect(lista?.textContent).toContain('v1');
      expect(lista?.textContent).toContain('soportada');
    });
  });

  describe('centinelas del contrato (FR-UI-029)', () => {
    it('muestra «Sin retiro planificado», nunca 01/01/1970', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="retiro-1"]')?.textContent).toContain(
        'Sin retiro planificado',
      );
      expect(html().textContent).not.toContain('1970');
    });

    it('muestra la fecha real cuando el retiro está planificado', () => {
      // Arrange
      api.consultar.and.returnValue(
        of(
          sobre(
            contrato({
              versiones: [version({ idversion: 3, fecha_retiro: 1_800_000_000_000 })],
            }),
          ),
        ) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="retiro-3"]')?.textContent).not.toContain(
        'Sin retiro',
      );
    });

    it('no renderiza un enlace roto cuando no hay documento publicado', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="link-spec"]')).toBeNull();
      expect(html().querySelector('[data-testid="sin-spec"]')).toBeTruthy();
    });

    it('enlaza la documentación cuando sí está publicada', () => {
      // Arrange
      api.consultar.and.returnValue(
        of(sobre(contrato({ spec_url: 'https://docs.tsi.local/despacho/v1' }))) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="link-spec"]')).toBeTruthy();
    });
  });

  describe('estados no felices (FR-UI-030)', () => {
    it('explica el 404 como servicio sin versión publicada', () => {
      // Arrange
      api.consultar.and.returnValue(throwError(() => ({ status: 404 })) as never);

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('todavía no tiene una versión publicada');
    });

    it('ofrece Reintentar ante un fallo de red', () => {
      // Arrange
      api.consultar.and.returnValue(throwError(() => ({ status: 0 })) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-reintentar-lista"]')).toBeTruthy();
    });
  });
});
