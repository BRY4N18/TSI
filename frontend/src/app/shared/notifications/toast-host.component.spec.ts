/** @marker unit */
import { TestBed } from '@angular/core/testing';

import { ToastHostComponent } from './toast-host.component';
import { NotificationService } from './notification.service';

describe('ToastHostComponent', () => {
  function setup() {
    TestBed.configureTestingModule({ imports: [ToastHostComponent] });
    const fixture = TestBed.createComponent(ToastHostComponent);
    const notifications = TestBed.inject(NotificationService);
    fixture.detectChanges();
    return { fixture, notifications };
  }

  it('success_usa_fondo_semantico_no_card_surface', () => {
    // Arrange
    const { fixture, notifications } = setup();

    // Act
    notifications.toast('Estado actualizado a Ocupada.', 'success');
    fixture.detectChanges();

    // Assert
    const toast = fixture.nativeElement.querySelector('[data-testid="app-toast"]') as HTMLElement;
    expect(toast).toBeTruthy();
    expect(toast.getAttribute('data-tone')).toBe('success');
    expect(toast.classList.contains('tsi-toast--success')).toBeTrue();
    expect(toast.classList.contains('bg-bg-surface')).toBeFalse();
    expect(toast.textContent).toContain('Estado actualizado a Ocupada.');
  });
});
