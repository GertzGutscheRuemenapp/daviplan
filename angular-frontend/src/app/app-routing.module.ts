import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdministrationComponent } from './pages/administration/administration.component';
import { UsersComponent } from './pages/administration/users/users.component';
import { DashComponent } from './dash/dash.component';
import { LoginComponent } from './pages/login/login.component'
import { PlanningComponent } from "./pages/planning/planning.component";
import { DemandComponent } from "./pages/planning/demand/demand.component";
import { SupplyComponent } from "./pages/planning/supply/supply.component";
import { WelcomeComponent } from "./pages/welcome.component";
import { AuthGuard } from "./auth.service";

const routes: Routes = [
  {
    path: '',
    component: WelcomeComponent
  },
  {
    path: 'admin',
    component: AdministrationComponent,
    canActivate: [AuthGuard],
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
    path: 'planung',
    component: PlanningComponent,
    children: [
      {
        path: 'nachfrage',
        component: DemandComponent
      },
      {
        path: 'angebot',
        component: SupplyComponent
      }
    ]
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
