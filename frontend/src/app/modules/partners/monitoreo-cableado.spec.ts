import { NAV_LINKS } from '../../shared/layout/nav-links';
import { PARTNERS_ROUTES } from './partners.routes';
import { administradorGuard } from './guards/administrador.guard';
import { gestorPartnersGuard } from './guards/gestor-partners.guard';
import { partnerIntegracionGuard } from './guards/partner-integracion.guard';

/**
 * Guard de cableado del monitoreo (#08 frontend).
 *
 * Mismo test que se creó en #07 tras el incidente de `decisiones-pendientes.md`
 * #21, donde dos archivos del working tree se revirtieron solos y **nada lo
 * delató**: los tests de cada página seguían pasando porque probaban el
 * componente en aislamiento, no que estuviera enchufado.
 *
 * Aquí se comprueba lo que ningún test de componente ve: que la ruta existe,
 * que carga algo, que tiene el guard correcto, y que el enlace del menú apunta
 * a una ruta real.
 */

const RUTAS_ESPERADAS = [
  { path: 'consola/logs', guard: gestorPartnersGuard },
  { path: 'consola/logs/:idlog', guard: gestorPartnersGuard },
  { path: 'consola/reportes', guard: gestorPartnersGuard },
  { path: 'consola/excepciones', guard: administradorGuard },
  { path: 'portal/consumo', guard: partnerIntegracionGuard },
];

const ENLACES_ESPERADOS = [
  { path: '/partners/consola/logs', roles: ['Administrador', 'DesarrolladorAPIs'] },
  { path: '/partners/consola/reportes', roles: ['Administrador', 'DesarrolladorAPIs'] },
  { path: '/partners/consola/excepciones', roles: ['Administrador'] },
  { path: '/partners/portal/consumo', roles: ['PartnerIntegracion'] },
];

describe('Cableado del monitoreo de API', () => {
  describe('rutas', () => {
    for (const esperada of RUTAS_ESPERADAS) {
      it(`«${esperada.path}» existe, carga un componente y tiene su guard`, () => {
        // Act
        const ruta = PARTNERS_ROUTES.find((r) => r.path === esperada.path);

        // Assert
        expect(ruta)
          .withContext(`Falta la ruta ${esperada.path} en partners.routes.ts`)
          .toBeDefined();
        expect(ruta!.loadComponent).toBeDefined();
        expect(ruta!.canActivate).toContain(esperada.guard);
      });
    }
  });

  describe('🎯 orden de las rutas', () => {
    it('las rutas literales se declaran ANTES de las paramétricas que las capturarían', () => {
      // Angular resuelve por orden de declaración: `consola/:idpartner` captura
      // «excepciones» si se declara antes, y la pantalla acaba pidiendo el
      // detalle de un partner llamado «excepciones». Ningún test de página lo
      // ve, porque cada una funciona perfectamente en aislamiento.
      //
      // Se detectó navegando a la ruta en la app real.
      // Arrange
      const rutas = PARTNERS_ROUTES.map((r) => r.path ?? '');

      // Act / Assert
      for (const literal of RUTAS_ESPERADAS.map((r) => r.path)) {
        const [base, segundo] = literal.split('/');
        if (!segundo) {
          continue;
        }
        const parametrica = rutas.findIndex((r) => r.startsWith(`${base}/:`));
        const indiceLiteral = rutas.indexOf(literal);
        if (parametrica === -1) {
          continue;
        }
        expect(indiceLiteral)
          .withContext(
            `«${literal}» se declara después de «${rutas[parametrica]}», que la captura`,
          )
          .toBeLessThan(parametrica);
      }
    });
  });

  describe('navegación', () => {
    for (const enlace of ENLACES_ESPERADOS) {
      it(`«${enlace.path}» está en el menú con sus roles`, () => {
        // Act
        const item = NAV_LINKS.find((l) => l.path === enlace.path);

        // Assert
        expect(item)
          .withContext(`Falta la entrada ${enlace.path} en nav-links.ts`)
          .toBeDefined();
        expect(item!.roles).toEqual(enlace.roles);
        expect(item!.group).toBe('Partners y API');
      });
    }

    it('todo enlace del menú apunta a una ruta que existe', () => {
      // Un enlace a una ruta inexistente lleva al usuario a un 404 y ningún
      // test de página lo detectaría.
      // Arrange
      const rutas = PARTNERS_ROUTES.map((r) => `/partners/${r.path}`);

      // Act
      const rotos = ENLACES_ESPERADOS.filter((e) => !rutas.includes(e.path));

      // Assert
      expect(rotos).toEqual([]);
    });
  });

  describe('reparto por rol', () => {
    it('🎯 el partner NO ve la consola ni las excepciones', () => {
      // Act
      const suyos = NAV_LINKS.filter(
        (l) => l.group === 'Partners y API' && l.roles.includes('PartnerIntegracion'),
      ).map((l) => l.path);

      // Assert
      expect(suyos).not.toContain('/partners/consola/logs');
      expect(suyos).not.toContain('/partners/consola/excepciones');
      expect(suyos).toContain('/partners/portal/consumo');
    });

    it('🎯 el Desarrollador de APIs NO ve las excepciones de facturación', () => {
      // Decidir qué hacer con un excedente no cobrado es una decisión de
      // negocio, no de plataforma.
      // Act
      const suyos = NAV_LINKS.filter(
        (l) => l.group === 'Partners y API' && l.roles.includes('DesarrolladorAPIs'),
      ).map((l) => l.path);

      // Assert
      expect(suyos).toContain('/partners/consola/logs');
      expect(suyos).not.toContain('/partners/consola/excepciones');
    });

    it('el Administrador sí las ve', () => {
      // Act
      const suyos = NAV_LINKS.filter(
        (l) => l.group === 'Partners y API' && l.roles.includes('Administrador'),
      ).map((l) => l.path);

      // Assert
      expect(suyos).toContain('/partners/consola/excepciones');
    });

    it('ningún enlace del portal del partner se cuela en la consola', () => {
      // Los sidebars no se fusionan (design-system § 5)
      // Act
      const delPartner = NAV_LINKS.filter(
        (l) => l.group === 'Partners y API' && l.path.startsWith('/partners/portal'),
      );

      // Assert
      for (const item of delPartner) {
        expect(item.roles).toEqual(['PartnerIntegracion']);
      }
    });
  });
});
