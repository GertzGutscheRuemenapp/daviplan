import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { mockPresetLevels } from "../../basedata/areas/areas";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { AreaLevel, Infrastructure, PlanningProcess } from "../../../rest-interfaces";

@Component({
  selector: 'app-demand',
  templateUrl: './demand.component.html',
  styleUrls: ['./demand.component.scss']
})
export class DemandComponent implements OnInit {
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  selectedAreaLevel?: AreaLevel;
  areaLevels?: AreaLevel[];
  showScenarioMenu: boolean = false;
  activeProcess?: PlanningProcess;

  constructor(public cookies: CookieService,
              private planningService: PlanningService) {
    this.planningService.infrastructures$.subscribe(infrastructures => {
      this.infrastructures = infrastructures;
    });
    this.planningService.areaLevels$.subscribe(areaLevels => {
      this.areaLevels = areaLevels;
    });
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
      if (!process) this.cookies.set('exp-planning-scenario', false);
      this.showScenarioMenu = !!this.cookies.get('exp-planning-scenario');
    })
  }

  ngOnInit(): void {
  }
}
