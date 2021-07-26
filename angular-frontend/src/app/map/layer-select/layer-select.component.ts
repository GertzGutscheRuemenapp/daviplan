import { Component, Input, AfterViewInit } from '@angular/core';
import {MapService} from "../map.service";
import {OlMap} from "../map";

@Component({
  selector: 'app-layer-select',
  templateUrl: './layer-select.component.html',
  styleUrls: ['./layer-select.component.scss']
})
export class LayerSelectComponent implements AfterViewInit {
  @Input() target!: string;
  overlayLayers: string[] = [];
  backgroundLayers: string[] = [];
  map?: OlMap;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.mapService.mapCreated.subscribe( map => {
      if (map.target = this.target) {
        this.map = map;
        this.initSelect();
      }
    })
  }

  initSelect(): void {
    if (!this.map) return;
    this.backgroundLayers = Object.keys(this.map.layers);
  }
}
