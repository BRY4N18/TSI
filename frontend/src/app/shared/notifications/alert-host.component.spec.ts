import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AlertHostComponent } from './alert-host.component';
import { NotificationService } from './notification.service';

describe('AlertHostComponent', () => {
  let fixture: ComponentFixture<AlertHostComponent>;
  let notifications: NotificationService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [AlertHostComponent] }).compileComponents();
    fixture = TestBed.createComponent(AlertHostComponent);
    notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();
  });

  function abrir(): void {
    notifications.alert('Fecha futura no permitida', 'Error al registrar');
    fixture.detectChanges();
  }

  it('no renderiza nada mientras no hay alerta', () => {
    expect(fixture.nativeElement.querySelector('[role="alertdialog"]')).toBeNull();
  });

  it('se anuncia como diálogo modal con título y mensaje asociados', () => {
    // Arrange / Act
    abrir();

    // Assert — el overlay bloquea la pantalla; sin esto, para un lector de
    // pantalla la aplicación simplemente deja de responder.
    const dialogo = fixture.nativeElement.querySelector('[role="alertdialog"]') as HTMLElement;
    expect(dialogo).not.toBeNull();
    expect(dialogo.getAttribute('aria-modal')).toBe('true');
    const titulo = fixture.nativeElement.querySelector(`#${dialogo.getAttribute('aria-labelledby')}`);
    const mensaje = fixture.nativeElement.querySelector(`#${dialogo.getAttribute('aria-describedby')}`);
    expect(titulo?.textContent).toContain('Error al registrar');
    expect(mensaje?.textContent).toContain('Fecha futura no permitida');
  });

  it('lleva el foco al botón de reconocimiento al abrirse', () => {
    // Arrange / Act
    abrir();

    // Assert
    const boton = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(document.activeElement).toBe(boton);
  });

  it('se cierra con Escape', () => {
    // Arrange
    abrir();
    const overlay = fixture.nativeElement.querySelector('div') as HTMLElement;

    // Act
    overlay.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();

    // Assert
    expect(notifications.activeAlert()).toBeNull();
    expect(fixture.nativeElement.querySelector('[role="alertdialog"]')).toBeNull();
  });
});
