import { Component, OnInit } from '@angular/core';
import { mockIndicators } from "../../basedata/indicators/indicators.component";
import { mockPresetLevels } from "../../basedata/areas/areas";
import { CookieService } from "../../../helpers/cookies.service";

@Component({
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss']
})
export class RatingComponent implements OnInit {
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  indicators = mockIndicators;
  areaLevels = mockPresetLevels;
  showScenarioMenu: any = false;

  constructor(public cookies: CookieService) {}

  ngOnInit(): void {
    this.showScenarioMenu = this.cookies.get('exp-planning-scenario');
  }
}
