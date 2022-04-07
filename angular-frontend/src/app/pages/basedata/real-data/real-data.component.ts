import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { environment } from "../../../../environments/environment";
import { PopulationService } from "../../population/population.service";
import { Population } from "../../../rest-interfaces";
import { sortBy } from "../../../helpers/utils";
import { SettingsService } from "../../../settings.service";
import { SelectionModel } from "@angular/cdk/collections";

@Component({
  selector: 'app-real-data',
  templateUrl: './real-data.component.html',
  styleUrls: ['./real-data.component.scss']
})
export class RealDataComponent implements AfterViewInit, OnDestroy {
  backend: string = environment.backend;
  mapControl?: MapControl;
  years: number[] = [];
  yearSelection = new SelectionModel<number>(true);
  populations: Population[] = [];

  constructor(private mapService: MapService, private popService: PopulationService,
              private settings: SettingsService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-real-data-map');
    this.popService.fetchPopulations().subscribe(populations => {
      this.populations = sortBy(populations,'year');
      this.populations.forEach(pop => this.yearSelection.select(pop.year))
    });
    this.settings.projectSettings$.subscribe(settings => {
      this.years = Array.from({ length: settings.endYear - settings.startYear + 1 }, (_, i) => i + settings.startYear)
    })
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
