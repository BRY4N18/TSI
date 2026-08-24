/** @marker unit */
/**
 * PG-UI-006 — accesibilidad de las pantallas críticas.
 *
 * **La regla se apoyaba en algo que no existe.** Decía «verificable con axe en
 * la suite E2E», y el proyecto no tiene suite E2E: ni Playwright ni Cypress. Así
 * que llevaba desde el principio sin poder cumplirse, marcada como pendiente sin
 * que estuviera claro que el obstáculo era ese.
 *
 * Se comprueba con axe sobre el DOM que Angular renderiza en Karma. Cubre
 * estructura, etiquetas, roles y nombres accesibles. Lo que **no** cubre —orden
 * de tabulación entre pantallas, foco tras navegar, contraste con los estilos
 * globales cargados— está declarado en `axe.helper.ts`, para que nadie lea
 * «accesibilidad ✅» y suponga más de lo que se comprobó.
 *
 * Las pantallas elegidas son las de la cadena crítica: por donde entra todo el
 * mundo (login) y donde se registra una emergencia.
 */
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { of } from 'rxjs';

import { RegistroAccidentePage } from '../../modules/accidentes/pages/registro-accidente/registro-accidente.page';
import { AccidenteApiService } from '../../modules/accidentes/services/accidente-api.service';
import { GeocodificacionApiService } from '../../modules/accidentes/services/geocodificacion-api.service';
import { UbicacionCatalogoApiService } from '../../modules/accidentes/services/ubicacion-catalogo-api.service';
import { AuthApiService } from '../../modules/cuentas-clientes/auth/services/auth-api.service';
import { LoginPage } from '../../modules/cuentas-clientes/auth/pages/login.page';
import { analizarAccesibilidad, describir } from './axe.helper';

describe('Accesibilidad de las pantallas críticas (PG-UI-006)', () => {
  describe('LoginPage', () => {
    let fixture: ComponentFixture<LoginPage>;

    beforeEach(async () => {
      const authApi = jasmine.createSpyObj('AuthApiService', [
        'login',
        'logout',
        'clearSession',
      ]);

      await TestBed.configureTestingModule({
        imports: [LoginPage, RouterTestingModule],
        providers: [
          provideHttpClient(),
          { provide: AuthApiService, useValue: authApi },
          {
            provide: ActivatedRoute,
            useValue: { snapshot: { queryParamMap: convertToParamMap({}) } },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(LoginPage);
      fixture.detectChanges();
    });

    it('no_tiene_violaciones_wcag_a_ni_aa', async () => {
      const hallazgos = await analizarAccesibilidad(fixture.nativeElement);

      expect(hallazgos.length)
        .withContext(`Violaciones de accesibilidad en el login:\n${describir(hallazgos)}`)
        .toBe(0);
    });

    it('todos_los_campos_tienen_nombre_accesible', async () => {
      // El caso concreto que deja una pantalla inutilizable con lector: un
      // `input` sin `label` asociado se anuncia como «cuadro de edición» y nada
      // más. Con dos campos así, el usuario no sabe cuál es el correo.
      const campos = Array.from(
        fixture.nativeElement.querySelectorAll('input, select, textarea'),
      ) as HTMLElement[];

      expect(campos.length)
        .withContext('No se encontró ningún campo: la pantalla no se renderizó.')
        .toBeGreaterThan(0);

      const sinNombre = campos.filter((campo) => {
        const id = campo.getAttribute('id');
        const etiquetada = id && fixture.nativeElement.querySelector(`label[for="${id}"]`);
        return (
          !etiquetada &&
          !campo.getAttribute('aria-label') &&
          !campo.getAttribute('aria-labelledby') &&
          !campo.closest('label')
        );
      });

      expect(sinNombre.map((c) => c.outerHTML.slice(0, 100))).toEqual([]);
    });

    it('el_aviso_de_sesion_expirada_se_anuncia_solo', async () => {
      // Un aviso que aparece sin `role` no lo lee nadie: el usuario que llega
      // por una sesión caducada (PG-UI-003) se queda sin saber por qué está en
      // el login. Solo tiene sentido comprobarlo si el aviso está visible.
      fixture.componentInstance.sesionExpirada.set(true);
      fixture.detectChanges();

      const aviso = fixture.nativeElement.querySelector('[role="status"], [role="alert"]');
      expect(aviso)
        .withContext('El aviso de sesión expirada no se anuncia a un lector de pantalla.')
        .not.toBeNull();
    });
  });

  describe('RegistroAccidentePage', () => {
    // La pantalla donde se levanta el parte de una emergencia. Un formulario
    // largo es donde más caro sale un campo sin etiqueta: el operador no puede
    // permitirse adivinar cuál es «número de heridos».
    let fixture: ComponentFixture<RegistroAccidentePage>;

    beforeEach(async () => {
      const accidenteApi = jasmine.createSpyObj('AccidenteApiService', [
        'registrar',
        'confirmarReporte',
        'fusionar',
        'deshacerFusion',
      ]);
      const geoApi = jasmine.createSpyObj('GeocodificacionApiService', ['sugerir']);
      geoApi.sugerir.and.returnValue(
        of({ data: { idcalle: 5, en_cobertura_operativa: true, ubicacion: {} }, meta: {} }),
      );
      const catalogoApi = jasmine.createSpyObj('UbicacionCatalogoApiService', [
        'listarPaises',
        'listarEstados',
        'listarCondados',
        'listarCiudades',
        'listarCalles',
        'listarTiposReportado',
        'listarReferenciasEstacion',
      ]);
      catalogoApi.listarPaises.and.returnValue(of([]));
      catalogoApi.listarTiposReportado.and.returnValue(of([{ id: 1, nombre: 'Llamada' }]));
      catalogoApi.listarReferenciasEstacion.and.returnValue(of([{ id: 1, nombre: 'MEX' }]));

      await TestBed.configureTestingModule({
        imports: [RegistroAccidentePage],
        providers: [
          provideHttpClient(),
          { provide: AccidenteApiService, useValue: accidenteApi },
          { provide: GeocodificacionApiService, useValue: geoApi },
          { provide: UbicacionCatalogoApiService, useValue: catalogoApi },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(RegistroAccidentePage);
      fixture.detectChanges();
    });

    it('no_tiene_violaciones_wcag_a_ni_aa', async () => {
      const hallazgos = await analizarAccesibilidad(fixture.nativeElement);

      expect(hallazgos.length)
        .withContext(
          'Violaciones de accesibilidad en el registro de accidente:\n' +
            describir(hallazgos) +
            '\nHTML: ' +
            JSON.stringify(hallazgos.map((h) => h.elementos)),
        )
        .toBe(0);
    });
  });

  it('axe_esta_detectando_de_verdad', async () => {
    // Control de no-vacuidad. Sin esto, un fallo de configuración de axe daría
    // «0 violaciones» en cualquier pantalla y la regla entera quedaría en verde
    // sin comprobar nada — que es exactamente cómo `PG-CFG-005` llevaba meses
    // marcada como cubierta.
    const roto = document.createElement('div');
    roto.innerHTML = '<img src="x.png"><input type="text">';
    document.body.appendChild(roto);

    try {
      const hallazgos = await analizarAccesibilidad(roto);
      expect(hallazgos.length)
        .withContext('axe no detecta una imagen sin alt ni un campo sin etiqueta.')
        .toBeGreaterThan(0);
    } finally {
      roto.remove();
    }
  });
});
