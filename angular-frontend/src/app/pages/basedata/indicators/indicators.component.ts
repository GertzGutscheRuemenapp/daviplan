import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { MapControl, MapService } from "../../../map/map.service";
import { mockPresetLevels } from "../areas/areas";

interface Indicator {
  id: number;
  name: string;
  description: string;
}

export const mockIndicators: Indicator[] = [
  {id: 1, name: 'Kita U3 Nachfrage', description: 'U3-Kind mit Betreuungswunsch pro Kita mit Krippe'},
  {id: 2, name: 'Kita U3 Erreichbarkeit', description: 'Anzahl der U3-Kinder mit Betreuungswunsch, für die diese Einrichtung am besten erreichbar ist'}
]

@Component({
  selector: 'app-indicators',
  templateUrl: './indicators.component.html',
  styleUrls: ['./indicators.component.scss']
})
export class IndicatorsComponent implements AfterViewInit, OnDestroy {
  backend: string = environment.backend;
  infrastructures = mockInfrastructures;
  indicators = mockIndicators;
  selectedIndicator = this.indicators[0];
  mapControl?: MapControl;
  areaLevels = mockPresetLevels;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-indicators-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
