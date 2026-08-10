/** @marker unit */
import { routes } from '../../app.routes';
import { NAV_LINKS } from '../../shared/layout/nav-links';
import { PARTNERS_ROUTES } from './partners.routes';

/**
 * Regresión: el módulo `partners` debe seguir CABLEADO a la app.
 *
 * Por qué existe
 * --------------
 * El 2026-08-09, durante la verificación manual, `app.routes.ts` y
 * `nav-links.ts` aparecieron revertidos a su versión de HEAD: el módulo seguía
 * existiendo entero y compilando, pero era **inalcanzable** — sin entrada de
 * rutas y sin enlaces en el sidebar. Ni el type-check ni los 461 tests de
 * componente lo detectaron, porque cada pieza estaba bien por separado; lo que
 * faltaba era el enganche.
 *
 * No se investigó una causa concluyente (no hay hooks de git ni scripts que
 * hagan `restore`; lo más probable es un descarte manual desde el IDE). Da
 * igual la causa: un módulo desconectado en silencio es un fallo caro, y este
 * archivo lo convierte en un test rojo.
 *
 * Si alguna de estas aserciones falla, **no la relajes**: significa que el
 * cableado se perdió y hay que devolverlo.
 */
describe('cableado del módulo partners', () => {
  describe('rutas de la aplicación', () => {
    it('la app registra la entrada lazy de partners', () => {
      // Act — la entrada vive dentro del bloque autenticado
      const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);

      // Assert
      expect(rutas.some((r) => r.path === 'partners')).toBeTrue();
    });

    it('la entrada de partners carga el módulo de forma perezosa', () => {
      // Arrange
      const rutas = routes.flatMap((r) => [r, ...(r.children ?? [])]);

      // Act
      const partners = rutas.find((r) => r.path === 'partners');

      // Assert
      expect(partners?.loadChildren).toBeDefined();
    });
  });

  describe('rutas del módulo', () => {
    it('expone las dos superficies', () => {
      // Act
      const paths = PARTNERS_ROUTES.map((r) => r.path);

      // Assert
      expect(paths).toContain('consola');
      expect(paths).toContain('portal');
    });

    it('la resolución de promoción está protegida por su propio guard', () => {
      // RF-PON-008: el Desarrollador de APIs no debe alcanzarla ni por URL.
      // Act
      const resolver = PARTNERS_ROUTES.find((r) => r.path?.endsWith('resolver'));

      // Assert
      expect(resolver?.canActivate?.length).toBeGreaterThan(0);
    });

    it('NO existe una ruta de edición: el backend no expone PATCH de ficha', () => {
      // Act / Assert — variante Ver-only del design-system (FR-UI-003)
      expect(PARTNERS_ROUTES.some((r) => r.path?.includes('editar'))).toBeFalse();
    });
  });

  describe('navegación por rol', () => {
    const deGrupo = () => NAV_LINKS.filter((l) => l.group === 'Partners y API');

    it('el sidebar incluye el grupo «Partners y API»', () => {
      // Assert
      expect(deGrupo().length).toBeGreaterThan(0);
    });

    it('los gestores tienen sus dos entradas de consola', () => {
      // Act
      const rutasGestor = deGrupo()
        .filter((l) => l.roles.includes('Administrador'))
        .map((l) => l.path);

      // Assert
      expect(rutasGestor).toContain('/partners/consola');
      expect(rutasGestor).toContain('/partners/consola/solicitudes');
    });

    it('el partner tiene sus dos entradas de portal', () => {
      // Act
      const rutasPartner = deGrupo()
        .filter((l) => l.roles.includes('PartnerIntegracion'))
        .map((l) => l.path);

      // Assert
      expect(rutasPartner).toContain('/partners/portal');
      expect(rutasPartner).toContain('/partners/portal/contrato');
    });

    it('consola y portal NO se fusionan: ningún enlace sirve a ambos', () => {
      // Son departamentos distintos (design-system § 5). Un enlace compartido
      // haría que el partner descubriera la consola.
      // Act
      const mezclados = deGrupo().filter(
        (l) =>
          l.roles.includes('PartnerIntegracion') &&
          (l.roles.includes('Administrador') || l.roles.includes('DesarrolladorAPIs')),
      );

      // Assert
      expect(mezclados).toEqual([]);
    });
  });
});
