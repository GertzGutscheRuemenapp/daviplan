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
import { MatGridListModule } from '@angular/material/grid-list';
import { MatCardModule } from '@angular/material/card';
import { MatMenuModule } from '@angular/material/menu';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { CardComponent } from "./dash/dash-card.component";
import { MatDialogModule } from "@angular/material/dialog";
import { ConfirmDialogComponent } from "./dialogs/confirm-dialog/confirm-dialog.component";
import { InputCardComponent } from "./dash/input-card.component";
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
import { MatExpansionModule } from "@angular/material/expansion";
import { MatSliderModule } from "@angular/material/slider";
import { PopulationComponent } from './pages/population/population.component';
import { PopDevelopmentComponent } from './pages/population/pop-development/pop-development.component';
import { PopStatisticsComponent } from './pages/population/pop-statistics/pop-statistics.component';
import { ReachabilitiesComponent } from './pages/planning/reachabilities/reachabilities.component';
import { RatingComponent } from './pages/planning/rating/rating.component';
import { SettingsComponent } from './pages/administration/settings/settings.component';
import { ColorPickerModule } from "ngx-color-picker";
import { MaterialFileInputModule } from "ngx-material-file-input";
import { AreasComponent } from './pages/basedata/areas/areas.component';
import { LogComponent } from './log/log.component';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { StackedBarchartComponent } from './diagrams/stacked-barchart/stacked-barchart.component';
import { MultilineChartComponent } from './diagrams/multiline-chart/multiline-chart.component';
import { CKEditorModule } from '@ckeditor/ckeditor5-angular';
import { DragDirective } from './helpers/dragndrop.directive'
import { MatSlideToggleModule } from "@angular/material/slide-toggle";
import { MapControlsComponent } from './map/map-controls/map-controls.component';
import { EcoFabSpeedDialModule } from "@ecodev/fab-speed-dial";
import { ScenarioMenuComponent } from './pages/planning/scenario-menu/scenario-menu.component';
import { MatRadioModule } from "@angular/material/radio";
import { SideToggleComponent } from './elements/side-toggle/side-toggle.component';
import { LegendComponent } from './map/legend/legend.component';
import { DragDropModule } from "@angular/cdk/drag-drop";
import { TimeSliderComponent } from './elements/time-slider/time-slider.component';
import { TooltipModule } from 'ng2-tooltip-directive';
import { PopRasterComponent } from './pages/basedata/pop-raster/pop-raster.component';
import { CookieService} from 'ngx-cookie-service';
import { RealDataComponent } from './pages/basedata/real-data/real-data.component';
import { PrognosisDataComponent } from './pages/basedata/prognosis-data/prognosis-data.component';
import { StatisticsComponent } from './pages/basedata/statistics/statistics.component';
import { InfrastructureComponent } from './pages/administration/infrastructure/infrastructure.component';

@NgModule({
  declarations: [
    AppComponent,
    UsersComponent,
    CardComponent,
    MainNavComponent,
    AdministrationComponent,
    SideNavComponent,
    InputCardComponent,
    ConfirmDialogComponent,
    LoginComponent,
    DemandComponent,
    PlanningComponent,
    SupplyComponent,
    WelcomeComponent,
    BasedataComponent,
    PopulationComponent,
    PopDevelopmentComponent,
    PopStatisticsComponent,
    ReachabilitiesComponent,
    RatingComponent,
    SettingsComponent,
    AreasComponent,
    LogComponent,
    StackedBarchartComponent,
    MultilineChartComponent,
    DragDirective,
    MapControlsComponent,
    ScenarioMenuComponent,
    SideToggleComponent,
    LegendComponent,
    TimeSliderComponent,
    PopRasterComponent,
    RealDataComponent,
    PrognosisDataComponent,
    StatisticsComponent,
    InfrastructureComponent
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
        MatSliderModule,
        ColorPickerModule,
        MaterialFileInputModule,
        FontAwesomeModule,
        CKEditorModule,
        MatSlideToggleModule,
        EcoFabSpeedDialModule,
        MatRadioModule,
        DragDropModule,
        TooltipModule
    ],
  providers: [
    [CookieService],
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
