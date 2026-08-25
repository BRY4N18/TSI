import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KpiRingComponent } from './kpi-ring.component';

const CIRCUNFERENCIA = 2 * Math.PI * 42;

@Component({
  standalone: true,
  imports: [KpiRingComponent],
  template: `
    <app-kpi-ring [valor]="valor" [meta]="meta" etiqueta="Cumplimiento de SLA">
      <span data-testid="cifra">{{ valor }}</span>
    </app-kpi-ring>
  `,
})
class HostComponent {
  valor: number | null = 80;
  meta: number | null = 95;
}

describe('KpiRingComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  const circulos = (): SVGCircleElement[] =>
    Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('circle'));

  const porColor = (color: string): SVGCircleElement | undefined =>
    circulos().find((c) => (c.getAttribute('stroke') ?? '').includes(color));

  const largoDe = (c: SVGCircleElement | undefined): number =>
    Number((c?.getAttribute('stroke-dasharray') ?? '0 0').split(' ')[0]);

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HostComponent] }).compileComponents();
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('pinta el arco conseguido proporcional al valor', () => {
    const logrado = porColor('accent-primary');
    expect(logrado).toBeTruthy();
    expect(largoDe(logrado)).toBeCloseTo((CIRCUNFERENCIA * 80) / 100, 3);
  });

  it('pinta en accent-flow solo el tramo que falta hasta la meta', () => {
    const pendiente = porColor('accent-flow');
    expect(pendiente).toBeTruthy();
    // 95 - 80 = 15 puntos porcentuales, no la meta entera ni el resto del círculo.
    expect(largoDe(pendiente)).toBeCloseTo((CIRCUNFERENCIA * 15) / 100, 3);
    // Arranca donde termina lo conseguido.
    expect(Number(pendiente?.getAttribute('stroke-dashoffset'))).toBeCloseTo(
      -((CIRCUNFERENCIA * 80) / 100),
      3,
    );
  });

  it('no dibuja tramo pendiente cuando el valor ya alcanzó la meta', () => {
    fixture.componentInstance.valor = 97;
    fixture.detectChanges();
    expect(porColor('accent-flow')).toBeUndefined();
    expect(largoDe(porColor('accent-primary'))).toBeCloseTo((CIRCUNFERENCIA * 97) / 100, 3);
  });

  it('sin dato deja solo la pista, sin arco conseguido', () => {
    fixture.componentInstance.valor = null;
    fixture.detectChanges();
    expect(porColor('accent-primary')).toBeUndefined();
    expect(porColor('border-default')).toBeTruthy();
  });

  it('marca la meta sobre la pista y la anuncia en el aria-label', () => {
    const svg = (fixture.nativeElement as HTMLElement).querySelector('svg');
    expect(svg?.querySelector('line')).toBeTruthy();
    expect(svg?.getAttribute('aria-label')).toBe('Cumplimiento de SLA: 80.0 %, meta 95 %');
  });

  it('sin meta no hay ni marca ni tramo pendiente', () => {
    fixture.componentInstance.meta = null;
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('line')).toBeNull();
    expect(porColor('accent-flow')).toBeUndefined();
  });

  it('acota valores fuera de rango en vez de desbordar el círculo', () => {
    fixture.componentInstance.valor = 140;
    fixture.detectChanges();
    expect(largoDe(porColor('accent-primary'))).toBeCloseTo(CIRCUNFERENCIA, 3);
  });

  it('proyecta la cifra de la pantalla sin reformatearla', () => {
    const cifra = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="cifra"]');
    expect(cifra?.textContent?.trim()).toBe('80');
  });
});
