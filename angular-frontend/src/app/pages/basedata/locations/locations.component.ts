import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { Infrastructure } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";

@Component({
  selector: 'app-locations',
  templateUrl: './locations.component.html',
  styleUrls: ['./locations.component.scss']
})
export class LocationsComponent implements AfterViewInit, OnDestroy {
  infrastructures: Infrastructure[] = [];
  selectedInfrastructure?: Infrastructure;
  mapControl?: MapControl;
  addPlaceMode = false;

  constructor(private mapService: MapService, private restService: RestCacheService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-locations-map');
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
    })
  }
  onInfrastructureChange(): void {
    console.log(this.selectedInfrastructure);
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
