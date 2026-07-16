/** @marker unit */
import { TestBed } from '@angular/core/testing';

import { TablerIconComponent, TablerIconName, tablerIconPaths } from './tabler-icon.component';

describe('TablerIconComponent', () => {
  function createComponent(name: TablerIconName, size?: number) {
    const fixture = TestBed.createComponent(TablerIconComponent);
    fixture.componentInstance.name = name;
    if (size !== undefined) {
      fixture.componentInstance.size = size;
    }
    fixture.detectChanges();
    return fixture;
  }

  it('paths_when_icon_valido_returns_svg_paths', () => {
    // Arrange / Act
    const fixture = createComponent('bell');

    // Assert
    expect(fixture.componentInstance.paths.length).toBeGreaterThan(0);
    const pathEls = fixture.nativeElement.querySelectorAll('path');
    expect(pathEls.length).toBe(fixture.componentInstance.paths.length);
  });

  it('paths_when_icon_inexistente_returns_empty_array', () => {
    // Arrange / Act
    const fixture = createComponent('icono-que-no-existe' as TablerIconName);

    // Assert
    expect(fixture.componentInstance.paths).toEqual([]);
    expect(fixture.nativeElement.querySelectorAll('path').length).toBe(0);
  });

  it('svg_size_when_size_input_set_reflects_width_height', () => {
    // Arrange / Act
    const fixture = createComponent('menu', 32);

    // Assert
    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg.getAttribute('width')).toBe('32');
    expect(svg.getAttribute('height')).toBe('32');
  });

  it('tablerIconPaths_when_icon_inexistente_returns_empty_array', () => {
    // Arrange / Act / Assert
    expect(tablerIconPaths('icono-que-no-existe' as TablerIconName)).toEqual([]);
  });
});
