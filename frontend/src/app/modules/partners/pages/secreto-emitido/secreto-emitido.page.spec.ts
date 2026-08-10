/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';

import type { CredencialEmitida } from '../../services/models/partner.types';
import { ESTADO_CREDENCIAL_EMITIDA, SecretoEmitidoPage } from './secreto-emitido.page';

const SECRETO = 'zK3n-secreto-irrecuperable-9x7Q';

const CREDENCIAL: CredencialEmitida = {
  idcredencial: 501,
  nombre_credencial: 'plataforma-siniestros',
  entorno: 'Sandbox',
  activo: true,
  fecha_creacion: 1,
  fecha_expiracion: 1_900_000_000_000,
  client_id: 'tsi-p7-c100',
  client_secret: SECRETO,
};

describe('SecretoEmitidoPage', () => {
  let fixture: ComponentFixture<SecretoEmitidoPage>;

  /** Monta la página simulando la navegación que trae la credencial. */
  function montarCon(credencial: CredencialEmitida | null): void {
    TestBed.configureTestingModule({
      imports: [SecretoEmitidoPage],
      providers: [provideRouter([])],
    });
    const router = TestBed.inject(Router);
    spyOn(router, 'getCurrentNavigation').and.returnValue(
      credencial
        ? ({ extras: { state: { [ESTADO_CREDENCIAL_EMITIDA]: credencial } } } as never)
        : (null as never),
    );
    fixture = TestBed.createComponent(SecretoEmitidoPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('entrega del secreto (FR-UI-020)', () => {
    it('muestra el secreto recibido por estado de navegación', () => {
      // Act
      montarCon(CREDENCIAL);

      // Assert
      expect(html().querySelector('[data-testid="valor-client-secret"]')?.textContent).toContain(
        SECRETO,
      );
    });

    it('avisa de la irreversibilidad ANTES del valor', () => {
      // Si el aviso llegara después, el usuario ya habría pasado de largo.
      // Act
      montarCon(CREDENCIAL);

      // Assert
      const cuerpo = html().innerHTML;
      const posAviso = cuerpo.indexOf('una sola vez');
      const posSecreto = cuerpo.indexOf(SECRETO);
      expect(posAviso).toBeGreaterThan(-1);
      expect(posAviso).toBeLessThan(posSecreto);
    });

    it('la salida está DESHABILITADA hasta confirmar el guardado', () => {
      // Act
      montarCon(CREDENCIAL);

      // Assert
      const boton = html().querySelector('[data-testid="btn-continuar"]') as HTMLButtonElement;
      expect(boton.disabled).toBeTrue();
    });

    it('la salida se habilita al confirmar', () => {
      // Arrange
      montarCon(CREDENCIAL);

      // Act
      fixture.componentInstance.alternarConfirmacion();
      fixture.detectChanges();

      // Assert
      const boton = html().querySelector('[data-testid="btn-continuar"]') as HTMLButtonElement;
      expect(boton.disabled).toBeFalse();
    });

    it('no navega mientras no se haya confirmado', () => {
      // Arrange
      montarCon(CREDENCIAL);
      const router = TestBed.inject(Router);
      const navegar = spyOn(router, 'navigate');

      // Act
      fixture.componentInstance.continuar();

      // Assert
      expect(navegar).not.toHaveBeenCalled();
    });

    it('ofrece copiar por separado el id y el secreto', () => {
      // Act
      montarCon(CREDENCIAL);

      // Assert
      expect(html().querySelector('[data-testid="btn-copiar-id"]')).toBeTruthy();
      expect(html().querySelector('[data-testid="btn-copiar-secreto"]')).toBeTruthy();
    });
  });

  describe('no fuga del secreto (FR-UI-021, SC-004)', () => {
    it('no queda en localStorage ni en sessionStorage', () => {
      // Act
      montarCon(CREDENCIAL);

      // Assert
      expect(JSON.stringify(localStorage)).not.toContain(SECRETO);
      expect(JSON.stringify(sessionStorage)).not.toContain(SECRETO);
    });

    it('no aparece en la URL', () => {
      // Una URL se comparte, se guarda en el historial y llega a logs de proxy.
      // Act
      montarCon(CREDENCIAL);

      // Assert
      expect(location.href).not.toContain(SECRETO);
    });

    it('no aparece en el título del documento', () => {
      // Act
      montarCon(CREDENCIAL);

      // Assert
      expect(document.title).not.toContain(SECRETO);
    });

    it('se descarta de memoria al destruir el componente', () => {
      // Arrange
      montarCon(CREDENCIAL);

      // Act
      fixture.componentInstance.ngOnDestroy();

      // Assert
      expect(fixture.componentInstance.credencial()).toBeNull();
    });
  });

  describe('recarga sin estado (FR-UI-022)', () => {
    it('explica que el secreto ya no está disponible, sin romperse', () => {
      // Act — sin estado de navegación, como tras un F5
      montarCon(null);

      // Assert
      expect(html().querySelector('[data-testid="secreto-no-disponible"]')).toBeTruthy();
      expect(html().textContent).toContain('El secreto ya no está disponible');
    });

    it('dice cómo recuperarse y que emitir otra no rompe las existentes', () => {
      // Act
      montarCon(null);

      // Assert
      expect(html().textContent).toContain('no interrumpe las credenciales que ya tienes');
      expect(html().querySelector('[data-testid="link-volver-integracion"]')).toBeTruthy();
    });

    it('no muestra ningún campo de secreto', () => {
      // Act
      montarCon(null);

      // Assert
      expect(html().querySelector('[data-testid="valor-client-secret"]')).toBeNull();
    });
  });
});
