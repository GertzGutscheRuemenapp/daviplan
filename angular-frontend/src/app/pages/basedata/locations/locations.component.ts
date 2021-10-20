import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-locations',
  templateUrl: './locations.component.html',
  styleUrls: ['./locations.component.scss']
})
export class LocationsComponent implements AfterViewInit, OnDestroy {
  infrastructures = mockInfrastructures;
  selectedInfrastructure = mockInfrastructures[1];
  mapControl?: MapControl;
  addPlaceMode = false;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-locations-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
