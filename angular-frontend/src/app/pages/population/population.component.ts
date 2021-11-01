import { AfterViewInit, Component, EventEmitter, Injectable, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { Observable } from "rxjs";
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";
import { map, shareReplay } from "rxjs/operators";

@Injectable({ providedIn: 'root' })
export class PopService {
  timeSlider?: TimeSliderComponent;
  ready: EventEmitter<any> = new EventEmitter();
}

@Component({
  selector: 'app-population',
  templateUrl: './population.component.html',
  styleUrls: ['./population.component.scss']
})
export class PopulationComponent implements AfterViewInit {
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  mapControl?: MapControl;
  faArrows = faArrowsAlt;

  constructor(private mapService: MapService, private popService: PopService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.popService.timeSlider = this.timeSlider;
    this.popService.ready.emit();
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
