/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DetalleExpedientePage } from './detalle-expediente.page';

describe('DetalleExpedientePage', () => {
  let fixture: ComponentFixture<DetalleExpedientePage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DetalleExpedientePage],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleExpedientePage);
    fixture.detectChanges();
  });

  it('creates_the_component', () => {
    // Assert
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders_placeholder_text', () => {
    // Assert
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Detalle de expediente');
  });
});
