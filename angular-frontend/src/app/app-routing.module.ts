import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdministrationComponent } from './administration/administration.component';
import { UsersComponent } from './administration/users/users.component';
import { DashComponent } from './dash/dash.component';
import { LoginComponent } from './login/login.component'

const routes: Routes = [
  {
    path: 'admin',
    component: AdministrationComponent,
    children: [
      {
        path: 'settings',
        component: DashComponent
      },
      {
        path: 'users',
        component: UsersComponent
      }
    ]
  },
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'bevoelkerung',
    component: DashComponent
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
