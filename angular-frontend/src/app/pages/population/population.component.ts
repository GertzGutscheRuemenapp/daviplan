import { AfterViewInit, Component, EventEmitter, Injectable, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { PopulationService } from "./population.service";


@Component({
  selector: 'app-population',
  templateUrl: './population.component.html',
  styleUrls: ['./population.component.scss']
})
export class PopulationComponent implements AfterViewInit {
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  mapControl?: MapControl;
  faArrows = faArrowsAlt;

  constructor(private mapService: MapService, public populationService: PopulationService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.populationService.timeSlider = this.timeSlider;
    this.populationService.setReady(true);
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
