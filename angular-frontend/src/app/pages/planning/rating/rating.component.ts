import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { CookieService } from "../../../helpers/cookies.service";
import { environment } from "../../../../environments/environment";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { PlanningService } from "../planning.service";
import { AreaLevel, Indicator, Infrastructure, PlanningProcess } from "../../../rest-interfaces";

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
  indicators: Indicator[] = [];
  activeIndicator?: Indicator;
  selectedAreaLevel?: AreaLevel;
  areaLevels?: AreaLevel[];
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;

  constructor(private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService) {
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.selectedInfrastructure = infrastructures[0];
    });
    this.planningService.getAreaLevels({ active: true }).subscribe(areaLevels => {
      this.areaLevels = areaLevels;
      this.selectedAreaLevel = areaLevels[0];
    })
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
  }

  onIndicatorChange(id: number): void {
    this.activeIndicator = this.indicators.find(ind => ind.id === id);
  }

  ngOnInit(): void {
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
