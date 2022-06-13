import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { environment } from "../../../../environments/environment";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { PlanningService } from "../planning.service";
import {
  AreaLevel,
  Indicator,
  Infrastructure,
  LayerGroup,
  PlanningProcess,
  RasterCell,
  Service
} from "../../../rest-interfaces";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";
import { SelectionModel } from "@angular/cdk/collections";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements AfterViewInit {
  @ViewChild('diagramDialog') diagramDialogTemplate!: TemplateRef<any>;
  backend: string = environment.backend;
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  indicators: Indicator[] = [];
  areaLevels: AreaLevel[] = [];
  infrastructures?: Infrastructure[];
  selectedService?: Service;
  selectedIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  selectedInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;
  serviceSelection = new SelectionModel<Service>(false);

  constructor(private dialog: MatDialog, public cookies: CookieService, private http: HttpClient,
              public planningService: PlanningService, private rest: RestAPI) {
    this.planningService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.planningService.getInfrastructures().subscribe(infrastructures => {
        this.infrastructures = infrastructures;
        this.applyUserSettings();
      });
    })
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
  }

  ngAfterViewInit(): void {
  }

  applyUserSettings(): void {
    this.selectedAreaLevel = this.areaLevels.find(al => al.id === this.cookies.get('planning-area-level', 'number'));
    this.selectedInfrastructure = this.infrastructures?.find(i => i.id === this.cookies.get('planning-infrastructure', 'number'));
    this.selectedService = this.selectedInfrastructure?.services.find(i => i.id === this.cookies.get('planning-service', 'number'));
    this.onServiceChange();
  }

  onAreaLevelChange(): void {
    this.cookies.set('planning-area-level', this.selectedAreaLevel?.id);
  }

  onInfrastructureChange(): void {
    this.serviceSelection.select();
    this.cookies.set('planning-infrastructure', this.selectedInfrastructure?.id);
    const services = this.selectedInfrastructure!.services;
    this.selectedService = (services.length > 0)? services[0]: undefined;
    this.onServiceChange();
  }

  onServiceChange(): void {
    this.cookies.set('planning-service', this.selectedService?.id);
    if (!this.selectedService) {
      this.indicators = [];
      this.selectedIndicator = undefined;
      return;
    }
    this.planningService.getIndicators(this.selectedService.id).subscribe(indicators => {
      this.indicators = indicators;
      this.selectedIndicator = indicators?.find(i => i.name === this.cookies.get('planning-indicator', 'string'));
    })
  }

  onIndicatorChange(): void {
    console.log(this.selectedIndicator)
    this.cookies.set('planning-indicator', this.selectedIndicator?.name);
  }

  onFullscreenDialog(): void {
    this.dialog.open(SimpleDialogComponent, {
      autoFocus: false,
      data: {
        template: this.diagramDialogTemplate
      }
    });
  }
}
