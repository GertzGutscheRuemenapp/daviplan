import {AfterViewInit, Component, OnDestroy} from '@angular/core';
import { OlMap } from "../../../map/map";
import { MapControl, MapService } from "../../../map/map.service";
import { PopService } from "../population.component";
import { environment } from "../../../../environments/environment";

@Component({
  selector: 'app-pop-statistics',
  templateUrl: './pop-statistics.component.html',
  styleUrls: ['./pop-statistics.component.scss']
})
export class PopStatisticsComponent implements AfterViewInit {
  mapControl?: MapControl;
  backend: string = environment.backend;

  constructor(private mapService: MapService, private popService: PopService) {
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.mapControl.mapDescription = 'Bevölkerungsstatistik > Gemeinden | Wanderung';
    if (this.popService.timeSlider)
      this.setSlider();
    else
      this.popService.ready.subscribe(r => this.setSlider());
  }

  setSlider(): void {
    let slider = this.popService.timeSlider!;
    slider.prognosisEnd = 0;
    slider.years = [2012, 2013, 2014, 2015, 2016];
    slider.value = 2012;
    slider.draw();
  }
}
