import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { LoginComponent } from './components/login/login.component';
import { RegisterComponent } from './components/register/register.component';
import { AddComponent } from './components/products/add/add.component';
import { ManageComponent } from './components/products/manage/manage.component';

export const routes: Routes = [
  { path: 'dashboard', component: DashboardComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  {path: 'product/add', component: AddComponent},
  {path: 'product/manage', component: ManageComponent}
];
