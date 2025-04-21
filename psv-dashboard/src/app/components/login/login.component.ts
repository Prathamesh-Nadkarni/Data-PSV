import { Component } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { PrimeIcons } from 'primeng/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, HttpClientModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm: FormGroup;
  loginMessage: string = '';
  PrimeIcons = PrimeIcons;

  constructor(
    private http: HttpClient,
    private fb: FormBuilder,
    private router: Router,
    private apiService: ApiService,
    private authService: AuthService
  ) {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  onLogin(): void {
    if (this.loginForm.invalid) return;

    this.apiService.post<{ access_token: string }>('login', this.loginForm.value)
      .subscribe({
        next: (response) => {
          this.authService.setToken(response.access_token);
          this.authService.setUserRole(this.loginForm.value.role);
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          this.loginMessage = error.message;
        }
      });
  }
  goToRegister(): void {
    this.router.navigate(['/register']);
  }
}
