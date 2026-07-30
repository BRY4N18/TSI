/** @marker unit */
import { TestBed } from '@angular/core/testing';

import { ListaSeleccionStorage } from './lista-seleccion.storage';

describe('ListaSeleccionStorage', () => {
  let storage: ListaSeleccionStorage;
  let store: Record<string, string>;

  beforeEach(() => {
    store = {};
    spyOn(sessionStorage, 'getItem').and.callFake((key: string) => store[key] ?? null);
    spyOn(sessionStorage, 'setItem').and.callFake((key: string, value: string) => {
      store[key] = value;
    });
    spyOn(sessionStorage, 'removeItem').and.callFake((key: string) => {
      delete store[key];
    });

    TestBed.configureTestingModule({});
    storage = TestBed.inject(ListaSeleccionStorage);
  });

  it('get_returns_null_when_empty', () => {
    // Arrange / Act
    const result = storage.get();

    // Assert
    expect(result).toBeNull();
  });

  it('set_then_get_returns_lastId', () => {
    // Arrange
    storage.set('ACC-1');

    // Act
    const result = storage.get();

    // Assert
    expect(result).toBe('ACC-1');
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('clear_removes_lastId', () => {
    // Arrange
    storage.set('ACC-1');

    // Act
    storage.clear();

    // Assert
    expect(storage.get()).toBeNull();
  });
});
