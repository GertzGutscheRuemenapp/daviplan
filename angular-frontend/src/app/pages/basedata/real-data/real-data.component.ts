import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import { Population, Year } from "../../../rest-interfaces";
import { sortBy } from "../../../helpers/utils";
import { SettingsService } from "../../../settings.service";
import { SelectionModel } from "@angular/cdk/collections";
import { RestAPI } from "../../../rest-api";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  backend: string = environment.backend;
  mapControl?: MapControl;
  years: Year[] = [];
  realYears: number[] = [];
  yearSelection = new SelectionModel<Year>(true);
  populations: Population[] = [];

  constructor(private mapService: MapService, private popService: PopulationService,
              private settings: SettingsService, private rest: RestAPI, private http: HttpClient) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
    this.popService.fetchPopulations().subscribe(populations => {
      this.populations = sortBy(populations,'year');
      // this.populations.forEach(pop => this.yearSelection.select(pop.year))
    });
    this.http.get<Year[]>(this.rest.URLS.years).subscribe(years => {
      this.years = years;
      years.forEach(year => {
        if (year.isReal) {
          this.yearSelection.select(year);
          this.realYears.push(year.year);
        }
      })
    });
    // this.settings.projectSettings$.subscribe(settings => {
    //   this.availableYears = Array.from({ length: settings.endYear - settings.startYear + 1 }, (_, i) => i + settings.startYear)
    // })
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
