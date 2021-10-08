import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-prognosis-data',
  templateUrl: './prognosis-data.component.html',
  styleUrls: ['./prognosis-data.component.scss']
})
export class PrognosisDataComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  prognoses = ['Trendfortschreibung', 'mehr Zuwanderung', 'mehr Abwanderung'];
  selectedPrognosis = 'Trendfortschreibung';

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-prog-data-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
