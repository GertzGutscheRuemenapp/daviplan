import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { UsersComponent } from './pages/administration/users/users.component';
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { LayoutModule } from '@angular/cdk/layout';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MainNavComponent } from './navigation/main-nav/main-nav.component';
import { AdministrationComponent } from './pages/administration/administration.component';
import { SideNavComponent } from './navigation/side-nav/side-nav.component';
import { DashComponent } from './dash/dash.component';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatCardModule } from '@angular/material/card';
import { MatMenuModule } from '@angular/material/menu';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { CardComponent } from "./dash/dash-card.component";
import { MatDialogModule } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "./dialogs/confirm-dialog.component";
import { DataCardComponent } from "./dash/data-card.component";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";
import { MatCheckboxModule } from "@angular/material/checkbox";
import { LoginComponent } from './pages/login/login.component';
import { TokenInterceptor } from './auth.service';
import { DemandComponent } from './pages/planning/demand/demand.component';
import { PlanningComponent } from './pages/planning/planning.component';
import { MatSelectModule } from "@angular/material/select";
import { SupplyComponent } from './pages/planning/supply/supply.component';
import { WelcomeComponent } from './pages/welcome.component';
import { BasedataComponent } from './pages/basedata/basedata.component';
import {MatExpansionModule} from "@angular/material/expansion";
import { LayerSelectComponent } from './map/layer-select/layer-select.component';
import {MatSliderModule} from "@angular/material/slider";
import { PopulationComponent } from './population/population.component';
import { PopDevelopmentComponent } from './population/pop-development/pop-development.component';
import { PopStatisticsComponent } from './population/pop-statistics/pop-statistics.component';

@NgModule({
  declarations: [
    AppComponent,
    UsersComponent,
    CardComponent,
    MainNavComponent,
    AdministrationComponent,
    SideNavComponent,
    DashComponent,
    DataCardComponent,
    ConfirmDialogComponent,
    LoginComponent,
    DemandComponent,
    PlanningComponent,
    SupplyComponent,
    WelcomeComponent,
    BasedataComponent,
    LayerSelectComponent,
    PopulationComponent,
    PopDevelopmentComponent,
    PopStatisticsComponent
  ],
    imports: [
        BrowserModule,
        AppRoutingModule,
        FlexLayoutModule,
        HttpClientModule,
        FormsModule,
        BrowserAnimationsModule,
        LayoutModule,
        MatToolbarModule,
        MatButtonModule,
        MatSidenavModule,
        MatIconModule,
        MatListModule,
        MatGridListModule,
        MatCardModule,
        MatMenuModule,
        MatDialogModule,
        MatFormFieldModule,
        MatProgressSpinnerModule,
        ReactiveFormsModule,
        MatInputModule,
        MatCheckboxModule,
        MatSelectModule,
        MatExpansionModule,
        MatSliderModule
    ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
