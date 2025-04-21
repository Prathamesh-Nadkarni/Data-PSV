// auth.service.ts
import { BehaviorSubject, Observable } from 'rxjs';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';


@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly ROLE_KEY = 'user_role';
  private roleSubject = new BehaviorSubject<string | null>(null);
  private authStateSubject = new BehaviorSubject<boolean>(false);
  private isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    this.roleSubject.next(this.getUserRoleFromStorage());
    this.authStateSubject.next(this.isLoggedIn());
  }

  getToken(): string | null {
    return this.isBrowser ? localStorage.getItem(this.TOKEN_KEY) : null;
  }

  setToken(token: string): void {
    if (this.isBrowser) {
      localStorage.setItem(this.TOKEN_KEY, token);
      this.authStateSubject.next(true);
    }
  }

  removeToken(): void {
    if (this.isBrowser) {
      localStorage.removeItem(this.TOKEN_KEY);
      this.authStateSubject.next(false);
    }
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  setUserRole(role: string): void {
    if (this.isBrowser) {
      localStorage.setItem(this.ROLE_KEY, role);
      this.roleSubject.next(role);
    }
  }

  getUserRole(): string | null {
    return this.isBrowser ? localStorage.getItem(this.ROLE_KEY) : null;
  }

  private getUserRoleFromStorage(): string | null {
    return this.isBrowser ? localStorage.getItem(this.ROLE_KEY) : null;
  }

  getUserRole$(): Observable<string | null> {
    return this.roleSubject.asObservable();
  }

  get authStateChanged(): Observable<boolean> {
    return this.authStateSubject.asObservable();
  }

  logout(): void {
    this.removeToken();
    if (this.isBrowser) {
      localStorage.removeItem(this.ROLE_KEY);
      this.roleSubject.next(null);
    }
  }
}
