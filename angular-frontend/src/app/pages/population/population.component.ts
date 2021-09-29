import { AfterViewInit, Component, OnInit } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-population',
  templateUrl: './population.component.html',
  styleUrls: ['./population.component.scss']
})
export class PopulationComponent implements AfterViewInit {
  mapControl?: MapControl;
  faArrows = faArrowsAlt;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
