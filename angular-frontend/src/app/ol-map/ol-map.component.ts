import { Component, NgZone, AfterViewInit, Output, Input, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { View, Feature, Map } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls} from 'ol/control';
import VectorLayer from 'ol/layer/Vector';
import Projection from 'ol/proj/Projection';
import * as olProj from 'ol/proj'
import { Extent } from 'ol/extent';
import TileLayer from 'ol/layer/Tile';
import OSM, { ATTRIBUTION } from 'ol/source/OSM';

@Component({
  selector: 'app-ol-map',
  templateUrl: './ol-map.component.html',
  styleUrls: ['./ol-map.component.scss']
})

export class OlMapComponent implements  AfterViewInit {

  @Input() center: Coordinate = [13.3392,52.5192];
  @Input() zoom: number = 8;
  view?: View;
  Map?: Map;
  @Output() mapReady = new EventEmitter<Map>();

  constructor(private zone: NgZone, private cd: ChangeDetectorRef) { }


  ngAfterViewInit():void {
    if (! this.Map) {
      this.zone.runOutsideAngular(() => this.initMap())
    }
    setTimeout(()=>this.mapReady.emit(this.Map));
  }

  private initMap(): void{
    this.view = new View({
      center: olProj.fromLonLat(this.center),
      zoom: this.zoom
    });
    this.Map = new Map({
      layers: [new TileLayer({
        source: new OSM({})
      })],
      target: 'map',
      view: this.view,
      controls: DefaultControls().extend([
        new ScaleLine({}),
      ]),
    });
  }
}
