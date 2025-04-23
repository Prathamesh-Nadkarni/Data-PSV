import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule, HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { PrimeIcons } from 'primeng/api';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, HttpClientModule, CommonModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  registerForm: FormGroup;
  registerMessage: string = '';
  errorMessage: string = '';
  PrimeIcons = PrimeIcons;

  constructor(private fb: FormBuilder, private http: HttpClient, private router: Router,
    private authService: AuthService) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      role: ['user', Validators.required],
      password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  onRegister(): void {
    if (this.registerForm.valid) {
      this.http.post('http://localhost:5500/register', this.registerForm.value).subscribe({
        next: () => {
          this.registerMessage = 'Registration successful!';
          this.errorMessage = '';
          this.registerForm.reset({ role: 'user' });
          this.router.navigate(['/login']);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 409) {
            if (error.error && error.error.message) {
              this.errorMessage = error.error.message;
              console.error('Error message from server:', error.error.message);
            } else {
              this.errorMessage = 'Username already exists.';
            }
          } else {
            this.errorMessage = 'Registration failed. Please try again.';
          }
          this.registerMessage = '';
        }
      });
    } else {
      this.errorMessage = 'Please fill out the form correctly.';
      this.registerMessage = '';
    }
  }

  goToLogin(): void {
    this.router.navigate(['/login']);
  }
}
