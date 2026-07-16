import { TestBed } from '@angular/core/testing';
import { THEME_STORAGE_KEY, ThemeService } from './theme.service';

describe('ThemeService', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  function create(): ThemeService {
    TestBed.configureTestingModule({});
    return TestBed.inject(ThemeService);
  }

  it('seeds from localStorage when a valid value is stored', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark');
    const service = create();
    expect(service.theme()).toBe('dark');
    expect(service.isDark()).toBe(true);
  });

  it('falls back to matchMedia when nothing is stored', () => {
    spyOn(window, 'matchMedia').and.returnValue({ matches: true } as MediaQueryList);
    const service = create();
    expect(service.theme()).toBe('dark');
  });

  it('toggle flips the value, applies it to <html> and persists it', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light');
    const service = create();
    TestBed.flushEffects();

    service.toggle();
    TestBed.flushEffects();

    expect(service.theme()).toBe('dark');
    expect(document.documentElement.dataset['theme']).toBe('dark');
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
  });
});
