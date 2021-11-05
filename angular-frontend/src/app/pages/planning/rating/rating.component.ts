import { Component, OnInit } from '@angular/core';
import { Indicator, mockIndicators } from "../../basedata/indicators/indicators.component";
import { mockPresetLevels } from "../../basedata/areas/areas";
import { CookieService } from "../../../helpers/cookies.service";
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { environment } from "../../../../environments/environment";

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
  backend: string = environment.backend;
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  indicators = mockIndicators;
  areaLevels = mockPresetLevels;
  customIndicators = mockCustomIndicators;
  showScenarioMenu: any = false;
  activeIndicator = mockIndicators[0];

  constructor(public cookies: CookieService) {}

  ngOnInit(): void {
    this.showScenarioMenu = this.cookies.get('exp-planning-scenario');
  }

  onIndicatorChange(id: number): void {
    this.activeIndicator = this.indicators.concat(this.customIndicators).filter(ind => ind.id === id)[0];
  }
}
