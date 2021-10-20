import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-capacities',
  templateUrl: './capacities.component.html',
  styleUrls: ['./capacities.component.scss']
})
export class CapacitiesComponent implements AfterViewInit, OnDestroy {
  infrastructures = mockInfrastructures;
  selectedInfrastructure = mockInfrastructures[1];
  services = mockInfrastructures[1].services;
  selectedService = mockInfrastructures[1].services[1];

  mapControl?: MapControl;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-capacities-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
