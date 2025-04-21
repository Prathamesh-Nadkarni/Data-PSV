import { Component, Input, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-menu',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './menu.component.html',
  styleUrl: './menu.component.css'
})
export class MenuComponent implements OnDestroy {
  @Input() isOpen: boolean = false;
  @Output() closeMenu = new EventEmitter<void>();
  userRole: string | null = null;
  private roleSub: Subscription;

  constructor(private authService: AuthService) {
    this.roleSub = this.authService.getUserRole$().subscribe(role => {
      this.userRole = role;
    });
  }

  ngOnDestroy() {
    if (this.roleSub) {
      this.roleSub.unsubscribe();
    }
  }

  onClose() {
    this.closeMenu.emit();
  }

  logout() {
    try {
      // Call the logout method without subscribing
      this.authService.logout();
      
      // Close the menu after logout
      this.onClose();
      
      // Navigation should be handled by the auth service
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }
}
