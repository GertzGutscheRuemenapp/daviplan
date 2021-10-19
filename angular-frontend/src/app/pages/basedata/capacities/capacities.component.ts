import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { infrastructures } from "../../administration/infrastructure/infrastructure.component";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-capacities',
  templateUrl: './capacities.component.html',
  styleUrls: ['./capacities.component.scss']
})
export class CapacitiesComponent implements AfterViewInit, OnDestroy {
  infrastructures = infrastructures;
  selectedInfrastructure = infrastructures[1];
  services = ['Grundschule', 'Gymnasium'];
  selectedService = 'Gymnasium';

  mapControl?: MapControl;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-capacities-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
