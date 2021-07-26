import { View, Feature, Map } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls } from 'ol/control';
import Projection from 'ol/proj/Projection';
import * as olProj from 'ol/proj'
import * as olStyle from 'ol/style'
import { Extent } from 'ol/extent';
import OSM, { ATTRIBUTION } from 'ol/source/OSM';
import { Layer } from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import GeoJSON from 'ol/format/GeoJSON';
import { bbox as bboxStrategy } from 'ol/loadingstrategy';

export class OlMap {
  target: string;
  view: View;
  map: Map;
  layers: Record<string, Layer<any>>;
  mapProjection: string;

  constructor( target: string, center: Coordinate = [13.3392,52.5192], zoom: number = 8, projection: string = 'EPSG:3857' ) {
    // this.layers = layers;
    this.target = target;
    this.view = new View({
      center: olProj.fromLonLat(center),
      zoom: zoom
    });
    this.layers={};

    this.map = new Map({
      layers: [new TileLayer({ source: new OSM({}), visible: true })],
      target: target,
      view: this.view,
      controls: DefaultControls().extend([
        new ScaleLine({}),
      ]),
    });
    this.mapProjection = projection;
  }

  addWFSLayer(name: string, url: string, opacity: number = 1): Layer<any>{

    if (this.layers[name] != null) this.removeLayer(name)

    let source = new VectorSource({
        format: new GeoJSON(),
        url: function (extent) {
          return (
            url + '?service=WFS&' +
            'version=1.1.0&request=GetFeature&typename=osm:water_areas&' +
            'outputFormat=application/json&srsname=EPSG:3857&' +
            'bbox=' +
            extent.join(',') +
            ',EPSG:3857'
          );
        },
        strategy: bboxStrategy
      })

    let layer = new VectorLayer({
      opacity: opacity,
      source: source
    });
    this.map.addLayer(layer);

    this.layers[name] = layer;
    return layer;
  }

  removeLayer(name: string){
    let layer = this.layers[name];
    if (!layer) return;
    this.map.removeLayer(layer)
    delete this.layers[name];
  }

  unset(): void {
    this.map.setTarget(null as any);
  }
}
