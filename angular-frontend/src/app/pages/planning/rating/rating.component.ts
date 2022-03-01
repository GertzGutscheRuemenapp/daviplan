import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { Indicator, mockIndicators } from "../../basedata/indicators/indicators.component";
import { CookieService } from "../../../helpers/cookies.service";
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { environment } from "../../../../environments/environment";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { PlanningService } from "../planning.service";
import { AreaLevel, Infrastructure, PlanningProcess } from "../../../rest-interfaces";

const mockCustomIndicators: Indicator[] = [
  {id: 6, service: mockInfrastructures[0].services[0].id, name: 'Test + langer Text der die maximale Größe des Containers überschreiten sollte', description: 'eigener Testindikator'},
  {id: 7, service: mockInfrastructures[0].services[0].id, name: 'zweiter Indikator', description: 'noch ein eigener Testindikator'},
]

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements OnInit {
  @ViewChild('diagramDialog') diagramDialogTemplate!: TemplateRef<any>;
  backend: string = environment.backend;
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  indicators = mockIndicators;
  selectedAreaLevel?: AreaLevel;
  areaLevels?: AreaLevel[];
  customIndicators = mockCustomIndicators;
  showScenarioMenu: boolean = false;
  activeIndicator = mockIndicators[0];
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;

  constructor(private dialog: MatDialog, public cookies: CookieService,
              private planningService: PlanningService) {
    this.planningService.infrastructures$.subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.selectedInfrastructure = infrastructures[0];
    });
    this.planningService.areaLevels$.subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.selectedAreaLevel = areaLevels[0];
    })
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      if (!process) this.cookies.set('exp-planning-scenario', false);
      this.showScenarioMenu = !!this.cookies.get('exp-planning-scenario');
    })
  }

  ngOnInit(): void {
  }

  onIndicatorChange(id: number): void {
    this.activeIndicator = this.indicators.concat(this.customIndicators).filter(ind => ind.id === id)[0];
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
