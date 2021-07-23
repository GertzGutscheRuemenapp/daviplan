import { Component, NgZone, AfterViewInit, Output, Input, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { View, Feature, Map } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls} from 'ol/control';
import Projection from 'ol/proj/Projection';
import * as olProj from 'ol/proj'
import { Extent } from 'ol/extent';
import OSM, { ATTRIBUTION } from 'ol/source/OSM';
import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import {bbox as bboxStrategy} from 'ol/loadingstrategy';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})

export class MapComponent implements AfterViewInit {

  @Input() center: Coordinate = [13.3392,52.5192];
  @Input() zoom: number = 8;
  view?: View;
  map?: Map;
  @Output() mapReady = new EventEmitter<Map>();

  baseLayers: any = {
    'OSM': new TileLayer({ source: new OSM({}), visible: true }),
    'Ahocevar' : new VectorLayer({source: new VectorSource({
        format: new GeoJSON(),
        url: function (extent) {
          return (
            'https://ahocevar.com/geoserver/wfs?service=WFS&' +
            'version=1.1.0&request=GetFeature&typename=osm:water_areas&' +
            'outputFormat=application/json&srsname=EPSG:3857&' +
            'bbox=' +
            extent.join(',') +
            ',EPSG:3857'
          );
        },
        strategy: bboxStrategy,
      }), visible: false
    })
  }

  constructor(private zone: NgZone, private cd: ChangeDetectorRef) { }

  ngAfterViewInit():void {
    if (! this.map) {
      this.zone.runOutsideAngular(() => this.initMap())
    }
    setTimeout(()=>this.mapReady.emit(this.map));
  }

  private initMap(): void{
    this.view = new View({
      center: olProj.fromLonLat(this.center),
      zoom: this.zoom
    });

    this.map = new Map({
      layers: Object.values(this.baseLayers),
      target: 'map',
      view: this.view,
      controls: DefaultControls().extend([
        new ScaleLine({}),
      ]),
    });
  }

  public removeLayer(name: string) {
    let layer = this.baseLayers[name];
    if (layer) {
      this.map?.removeLayer(layer);
    }
  }
}
