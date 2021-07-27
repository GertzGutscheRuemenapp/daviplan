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
import {BasedataComponent} from "./pages/basedata/basedata.component";
import {PopulationComponent} from "./pages/population/population.component";
import {PopDevelopmentComponent} from "./pages/population/pop-development/pop-development.component";
import {PopStatisticsComponent} from "./pages/population/pop-statistics/pop-statistics.component";
import {RatingComponent} from "./pages/planning/rating/rating.component";
import {ReachabilitiesComponent} from "./pages/planning/reachabilities/reachabilities.component";

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
    redirectTo: 'planung/nachfrage',
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
      },
      {
        path: 'erreichbarkeiten',
        component: ReachabilitiesComponent
      },
      {
        path: 'bewertung',
        component: RatingComponent
      }
    ]
  },
  {
    path: 'grundlagendaten',
    component: BasedataComponent
  },
  {
    path: 'bevoelkerung',
    redirectTo: 'bevoelkerung/entwicklung',
  },
  {
    path: 'bevoelkerung',
    component: PopulationComponent,
    children: [
      {
        path: 'entwicklung',
        component: PopDevelopmentComponent
      },
      {
        path: 'statistik',
        component: PopStatisticsComponent
      }
    ]
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
