import { View, Feature, Map } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls } from 'ol/control';
import OSM from 'ol/source/OSM';
import Projection from 'ol/proj/Projection';
import * as olProj from 'ol/proj'
import * as olStyle from 'ol/style'
import { Extent } from 'ol/extent';
import { Layer } from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import GeoJSON from 'ol/format/GeoJSON';
import { bbox as bboxStrategy } from 'ol/loadingstrategy';
import TileWMS from 'ol/source/TileWMS';

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
    let osmLayer = new TileLayer({
      source: new OSM(),
    })
    this.layers = { 'OSM': osmLayer };

    this.map = new Map({
      layers: [osmLayer],
      target: target,
      view: this.view,
      controls: DefaultControls().extend([
        new ScaleLine({}),
      ]),
    });
    this.mapProjection = projection;
  }

  addWMS(name: string, url: string, params: any = {}, visible: boolean = true, opacity: number = 1): Layer<any>{

    if (this.layers[name] != null) this.removeLayer(name)

    let source = new TileWMS({
      url: url,
      params: params,
      serverType: 'geoserver',
    })

    let layer = new TileLayer({
      opacity: opacity,
      source: source,
      visible: visible
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

  setVisible(name: string, visible: boolean): void{
    let layer = this.layers[name];
    layer?.setVisible(visible);
  }
}
