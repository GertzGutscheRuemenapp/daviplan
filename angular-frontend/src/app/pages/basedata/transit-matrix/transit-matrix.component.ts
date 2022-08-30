import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { ModeVariant, TransportMode } from "../../../rest-interfaces";

@Component({
  selector: 'app-transit-matrix',
  templateUrl: './transit-matrix.component.html',
  styleUrls: ['./transit-matrix.component.scss']
})
export class TransitMatrixComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  variants: ModeVariant[] = [{id: 1, mode: TransportMode.TRANSIT, label: 'Testnetz', network: 1}];
  selectedVariant?: ModeVariant = this.variants[0];
  statusQuoVariant?: ModeVariant;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    // this.mapControl = this.mapService.get('base-reachabilities-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
// /matrixcellplaces/precalculate_traveltime
}
