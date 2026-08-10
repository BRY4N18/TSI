/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { PartnerApiService } from '../../services/partner-api.service';
import type { PartnerListItem } from '../../services/models/partner.types';
import { ListaPartnersPage } from './lista-partners.page';

function partner(over: Partial<PartnerListItem> = {}): PartnerListItem {
  return {
    idpartner: 1,
    idcliente: 100,
    nombrepartner: 'Aseguradora Norte',
    planapi: 'Profesional',
    limitellamadasmes: 10000,
    limitellamadasminuto: 120,
    activo: true,
    estado: 'Plan asignado',
    ...over,
  };
}

const sobre = (data: PartnerListItem[], next: number | null = null) => ({
  data,
  meta: { pagination: { next_cursor: next, limit: 20 } },
});

describe('ListaPartnersPage', () => {
  let api: jasmine.SpyObj<PartnerApiService>;
  let fixture: ComponentFixture<ListaPartnersPage>;

  function montar(): void {
    fixture = TestBed.createComponent(ListaPartnersPage);
    fixture.detectChanges();
  }

  const html = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    api = jasmine.createSpyObj<PartnerApiService>('PartnerApiService', ['listar']);
    api.listar.and.returnValue(of(sobre([partner()])) as never);

    TestBed.configureTestingModule({
      imports: [ListaPartnersPage],
      providers: [provideRouter([]), { provide: PartnerApiService, useValue: api }],
    });
    localStorage.clear();
  });

  describe('variante Ver-only (FR-UI-003)', () => {
    it('ofrece la acción Ver', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-ver-1"]')).toBeTruthy();
    });

    it('NO ofrece un lápiz de edición: el backend no expone PATCH de ficha', () => {
      // Un `pencil` deshabilitado tampoco vale — no se expone lo que no se puede hacer.
      // Act
      montar();

      // Assert
      expect(html().textContent).not.toContain('Editar');
      expect(html().querySelector('[data-testid="btn-editar-1"]')).toBeNull();
    });

    it('la acción Ver lleva aria-label descriptivo', () => {
      // Act
      montar();

      // Assert
      const boton = html().querySelector('[data-testid="btn-ver-1"]');
      expect(boton?.getAttribute('aria-label')).toContain('Aseguradora Norte');
    });
  });

  describe('centinelas en la tabla', () => {
    it('muestra «Sin asignar» en vez de un cupo de -1', () => {
      // Arrange
      api.listar.and.returnValue(
        of(sobre([partner({ limitellamadasmes: -1, planapi: '', estado: 'Registrado' })])) as never,
      );

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('Sin asignar');
      expect(html().textContent).not.toContain('-1');
    });

    it('muestra «Sin plan» en vez de una celda vacía', () => {
      // Arrange
      api.listar.and.returnValue(of(sobre([partner({ planapi: '' })])) as never);

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('Sin plan');
    });
  });

  describe('estados no felices (FR-UI-030)', () => {
    it('muestra el skeleton mientras carga, no un spinner', () => {
      // Arrange — observable que nunca emite
      api.listar.and.returnValue(new (class {
        subscribe() {
          return { unsubscribe() {} };
        }
      })() as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('app-list-loading-skeleton')).toBeTruthy();
    });

    it('muestra el estado de error con Reintentar cuando la carga falla', () => {
      // Arrange
      api.listar.and.returnValue(throwError(() => new Error('red caída')) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="error-state"]')).toBeTruthy();
    });

    it('muestra el estado vacío con su copy propio', () => {
      // Arrange
      api.listar.and.returnValue(of(sobre([])) as never);

      // Act
      montar();

      // Assert
      expect(html().textContent).toContain('Todavía no hay partners registrados');
    });
  });

  describe('paginación por cursor (FR-UI-001)', () => {
    it('no ofrece «Cargar más» en la última página', () => {
      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-cargar-mas"]')).toBeNull();
    });

    it('ofrece «Cargar más» cuando hay cursor siguiente', () => {
      // Arrange
      api.listar.and.returnValue(of(sobre([partner()], 55)) as never);

      // Act
      montar();

      // Assert
      expect(html().querySelector('[data-testid="btn-cargar-mas"]')).toBeTruthy();
    });

    it('acumula la página siguiente en vez de reemplazar la actual', () => {
      // Arrange
      api.listar.and.returnValue(of(sobre([partner({ idpartner: 1 })], 55)) as never);
      montar();
      api.listar.and.returnValue(
        of(sobre([partner({ idpartner: 2, nombrepartner: 'Segunda' })])) as never,
      );

      // Act
      fixture.componentInstance.cargarMas();
      fixture.detectChanges();

      // Assert
      expect(fixture.componentInstance.partners().length).toBe(2);
    });
  });

  describe('filtro por estado', () => {
    it('reconsulta al backend con el estado elegido', () => {
      // Arrange
      montar();
      api.listar.calls.reset();

      // Act
      fixture.componentInstance.cambiarEstado('Pendiente de aprobación');

      // Assert
      expect(api.listar).toHaveBeenCalledWith(
        jasmine.objectContaining({ estado: 'Pendiente de aprobación' }),
      );
    });

    it('«Todos» no envía filtro de estado', () => {
      // Arrange
      montar();
      api.listar.calls.reset();

      // Act
      fixture.componentInstance.cambiarEstado('');

      // Assert
      expect(api.listar).toHaveBeenCalledWith(jasmine.objectContaining({ estado: undefined }));
    });
  });
});
