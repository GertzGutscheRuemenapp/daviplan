import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdministrationComponent } from './pages/administration/administration.component';
import { UsersComponent } from './pages/administration/users/users.component';
import { LoginComponent } from './pages/login/login.component'
import { PlanningComponent } from "./pages/planning/planning.component";
import { DemandComponent } from "./pages/planning/demand/demand.component";
import { SupplyComponent } from "./pages/planning/supply/supply.component";
import { WelcomeComponent } from "./pages/welcome.component";
import { AboutComponent } from "./pages/about.component";
import { PrivacyComponent } from "./pages/privacy.component";
import { AuthGuard } from "./auth.service";
import { BasedataComponent } from "./pages/basedata/basedata.component";
import { PopulationComponent } from "./pages/population/population.component";
import { PopDevelopmentComponent } from "./pages/population/pop-development/pop-development.component";
import { PopStatisticsComponent } from "./pages/population/pop-statistics/pop-statistics.component";
import { RatingComponent } from "./pages/planning/rating/rating.component";
import { ReachabilitiesComponent } from "./pages/planning/reachabilities/reachabilities.component";
import { SettingsComponent } from "./pages/administration/settings/settings.component";
import { AreasComponent } from "./pages/basedata/areas/areas.component";
import { PopRasterComponent } from "./pages/basedata/pop-raster/pop-raster.component";
import { RealDataComponent } from "./pages/basedata/real-data/real-data.component";
import { PrognosisDataComponent } from "./pages/basedata/prognosis-data/prognosis-data.component";
import { StatisticsComponent } from "./pages/basedata/statistics/statistics.component";
import { InfrastructureComponent } from "./pages/administration/infrastructure/infrastructure.component";
import { ProjectDefinitionComponent } from "./pages/administration/project-definition/project-definition.component";
import { CoordinationComponent } from "./pages/administration/coordination/coordination.component";
import { LocationsComponent } from "./pages/basedata/locations/locations.component";
import { ServicesComponent } from "./pages/basedata/services/services.component";
import { DemandQuotasComponent } from "./pages/basedata/demand-quotas/demand-quotas.component";
import { ExternalLayersComponent } from "./pages/basedata/external-layers/external-layers.component";
import { RoadNetworkComponent } from "./pages/basedata/road-network/road-network.component";
import { TransitMatrixComponent } from "./pages/basedata/transit-matrix/transit-matrix.component";

const routes: Routes = [
  {
    path: '',
    component: WelcomeComponent,
    canActivate: [AuthGuard],
    pathMatch: 'full'
  },
  {
    path: 'impressum',
    component: AboutComponent,
    canActivate: [AuthGuard]
  },
  {
    path: 'datenschutz',
    component: PrivacyComponent,
    canActivate: [AuthGuard]
  },
  {
    path: 'admin',
    redirectTo: 'admin/einstellungen'
  },
  {
    path: 'admin',
    component: AdministrationComponent,
    canActivate: [AuthGuard],
    data: {
      expectedRole: 'admin'
    },
    children: [
      {
        path: 'einstellungen',
        component: SettingsComponent
      },
      {
        path: 'benutzer',
        component: UsersComponent
      },
      {
        path: 'infrastruktur',
        component: InfrastructureComponent
      },
      {
        path: 'basisdefinitionen',
        component: ProjectDefinitionComponent
      },
      {
        path: 'koordination',
        component: CoordinationComponent
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
    canActivate: [AuthGuard],
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
    redirectTo: 'grundlagendaten/gebiete',
  },
  {
    path: 'grundlagendaten',
    component: BasedataComponent,
    canActivate: [AuthGuard],
    data: {
      expectedRole: 'dataEditor'
    },
    children: [
      {
        path: 'gebiete',
        component: AreasComponent
      },
/*      {
        path: 'einwohnerraster',
        component: PopRasterComponent
      },*/
      {
        path: 'realdaten',
        component: RealDataComponent
      },
      {
        path: 'prognosedaten',
        component: PrognosisDataComponent
      },
      {
        path: 'statistiken',
        component: StatisticsComponent
      },
      {
        path: 'standorte',
        component: LocationsComponent
      },
      {
        path: 'leistungen',
        component: ServicesComponent
      },
      {
        path: 'nachfrage',
        component: DemandQuotasComponent
      },
      {
        path: 'strassennetz',
        component: RoadNetworkComponent
      },
      {
        path: 'oepnvnetz',
        component: TransitMatrixComponent
      },
      {
        path: 'layer',
        component: ExternalLayersComponent
      },
    ]
  },
  {
    path: 'bevoelkerung',
    redirectTo: 'bevoelkerung/entwicklung',
  },
  {
    path: 'bevoelkerung',
    component: PopulationComponent,
    canActivate: [AuthGuard],
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
  imports: [RouterModule.forRoot(routes, {onSameUrlNavigation: 'reload'})],
  exports: [RouterModule]
})
export class AppRoutingModule { }
