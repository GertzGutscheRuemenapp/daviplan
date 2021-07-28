import {Component, AfterViewInit, OnDestroy} from '@angular/core';
import {MapService} from "../../../map/map.service";
import {OlMap} from "../../../map/map";

@Component({
  selector: 'app-pop-development',
  templateUrl: './pop-development.component.html',
  styleUrls: ['./pop-development.component.scss']
})
export class PopDevelopmentComponent implements AfterViewInit, OnDestroy {
  map?: OlMap;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.map = this.mapService.create('pop-map');
  }

  ngOnDestroy(): void {
    this.mapService.remove('pop-map');
  }

}
