/** @marker unit */
import { TestBed } from '@angular/core/testing';

import { ListaSeleccionStorage } from './lista-seleccion.storage';

describe('ListaSeleccionStorage (alta-unidades)', () => {
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
    expect(storage.get()).toBeNull();
  });

  it('set_then_get_returns_lastId', () => {
    storage.set('42');
    expect(storage.get()).toBe('42');
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('clear_removes_lastId', () => {
    storage.set('42');
    storage.clear();
    expect(storage.get()).toBeNull();
  });
});
