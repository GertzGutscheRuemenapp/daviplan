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
import XYZ from 'ol/source/XYZ';

export class OlMap {
  target: string;
  view: View;
  map: Map;
  layers: Record<string, Layer<any>> = {};
  mapProjection: string;

  constructor( target: string, center: Coordinate = [13.3392,52.5192], zoom: number = 8, projection: string = 'EPSG:3857', showDefaultControls: boolean = false ) {
    // this.layers = layers;
    this.target = target;
    this.view = new View({
      center: olProj.fromLonLat(center),
      zoom: zoom
    });

    let controls = (showDefaultControls) ? DefaultControls().extend([
        new ScaleLine({}),
      ]) : DefaultControls({ zoom : false, //attribution : false,
    })

    this.map = new Map({
      layers: [],
      target: target,
      view: this.view,
      controls: controls,
    });
    this.mapProjection = projection;
  }

  addTileServer(options: { name: string, url: string, params?: any, visible?: boolean, opacity?: number, xyz?: boolean}): Layer<any>{

    if (this.layers[options.name] != null) this.removeLayer(options.name)

    let source = (options.xyz) ? new XYZ({ url: options.url }) :
      new TileWMS({
      url: options.url,
      params: options.params || {},
      serverType: 'geoserver',
    })

    let layer = new TileLayer({
      opacity: (options.opacity != undefined) ? options.opacity: 1,
      source: source,
      visible: options.visible === true
    });

    this.map.addLayer(layer);
    this.layers[options.name] = layer;

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

  setOpacity(name: string, opacity: number): void{
    let layer = this.layers[name];
    layer?.setOpacity(opacity);
  }
}
