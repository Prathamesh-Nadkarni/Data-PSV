// api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = 'http://localhost:5500';

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private router: Router
  ) {}

  private getHeaders(): HttpHeaders {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Access-Control-Allow-Origin': 'http://localhost:4200',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Credentials': 'true'
    });

    const token = this.authService.getToken();
    if (token) {
      return headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    if (error.status === 401) {
      this.authService.removeToken();
      this.router.navigate(['/login']);
    }
    
    if (error.status === 0) {
      console.error('CORS Error:', error);
      return throwError(() => 'Unable to connect to the server. Please check if the server is running and accessible.');
    }
    
    return throwError(() => error.error?.error || 'An error occurred');
  }

  // Public methods
  post<T>(endpoint: string, body: any): Observable<T> {
    return this.http.post<T>(
      `${this.baseUrl}/${endpoint}`,
      body,
      { 
        headers: this.getHeaders(),
        withCredentials: true
      }
    ).pipe(catchError(this.handleError.bind(this)));
  }

  get<T>(endpoint: string, params?: any): Observable<T> {
    return this.http.get<T>(
      `${this.baseUrl}/${endpoint}`,
      { 
        headers: this.getHeaders(),
        params,
        withCredentials: true
      }
    ).pipe(catchError(this.handleError.bind(this)));
  }
}
