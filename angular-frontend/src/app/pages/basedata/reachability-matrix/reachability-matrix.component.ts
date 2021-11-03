import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-reachability-matrix',
  templateUrl: './reachability-matrix.component.html',
  styleUrls: ['./reachability-matrix.component.scss']
})
export class ReachabilityMatrixComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  modes: any = [
    {name: 'Auto', davicon: 'icon-GGR-davicons-Font-Simple-17-PKW', routers: [{id: 1, name: 'Dtl 2020', mode: 'Auto' }, {id: 2, name:'Ausbau der B232', mode: 'Auto'}]},
    {name: 'zu Fuß', icon: 'directions_walk', routers: [{id: 3, name: 'Dtl 2020', mode: 'zu Fuß' }]},
    {name: 'Fahrrad', icon: 'directions_bike', routers: [{id: 4, name: 'Dtl 2020', mode: 'Fahrrad'}, {id: 5, name: 'mit Schnellradweg 2021', mode: 'Fahrrad'}]},
    {name: 'ÖPNV', davicon: 'icon-GGR-davicons-Font-Simple-18-OEPNV', routers: []},
    // {name: 'Pedelec??', icon:'pedal_bike', routers: []},
  ]
  selectedRouter: any = this.modes[0].routers[0];
  statusQuoRouters: any = {'zu Fuß': 3, 'Auto': 1, 'Fahrrad': 5};

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-reachabilities-map');
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
