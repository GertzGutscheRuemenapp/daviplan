import { View, Feature, Map, Overlay } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls } from 'ol/control';
import OSM from 'ol/source/OSM';
import Projection from 'ol/proj/Projection';
import * as olProj from 'ol/proj'
import { Extent } from 'ol/extent';
import { Layer } from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import GeoJSON from 'ol/format/GeoJSON';
import { bbox as bboxStrategy } from 'ol/loadingstrategy';
import TileWMS from 'ol/source/TileWMS';
import XYZ from 'ol/source/XYZ';
import { Stroke, Style, Fill } from 'ol/style';
import { Select } from "ol/interaction";
import { click, singleClick, always } from 'ol/events/condition';

export class OlMap {
  target: string;
  view: View;
  map: Map;
  layers: Record<string, Layer<any>> = {};
  mapProjection: string;
  div: HTMLElement | null;
  tooltipOverlay: Overlay;

  constructor( target: string, options: {
    center?: Coordinate, zoom?: number, projection?: string,
    showDefaultControls?: boolean} = {}) {
    // this.layers = layers;
    const zoom = options.zoom || 8;
    const center = options.center || [13.3392,52.5192];
    const projection = options.projection || 'EPSG:3857';
    this.target = target;
    this.view = new View({
      center: olProj.fromLonLat(center),
      zoom: zoom
    });

    let controls = (options.showDefaultControls) ? DefaultControls().extend([
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
    this.div = document.getElementById(target);
    let tooltip = document.createElement('div');
    tooltip.classList.add('oltooltip');
    this.div!.appendChild(tooltip);
    this.tooltipOverlay = new Overlay({
      element: tooltip,
      offset: [10, 0],
      positioning: 'bottom-left'
    });
    this.map.addOverlay(this.tooltipOverlay);
    this.map.getViewport().addEventListener('mouseout', event => {
      tooltip.style.display = 'none';
    });
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

  addWFS(options: {
    name: string, url: any, params?: any,
    visible?: boolean, opacity?: number, xyz?: boolean,
    selectable?: boolean, tooltipField?: string }): Layer<any>{
    if (this.layers[options.name] != null) this.removeLayer(options.name);
    let source = new VectorSource({
      format: new GeoJSON(),
      url: options.url,
      strategy: bboxStrategy,
    });
    let layer = new VectorLayer({
      source: source,
      visible: options.visible === true,
      opacity: (options.opacity != undefined) ? options.opacity: 1,
      style: new Style({
        stroke: new Stroke({
          color: 'rgba(0, 0, 0, 1.0)',
          width: 1,
        }),
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.8)'
        }),
      }),
    });

    this.map.on("pointermove", event => {
      const pixel = event.pixel;
      const f = this.map.forEachFeatureAtPixel(pixel, function (feature, hlayer) {
        if (feature && hlayer === layer) return feature;
        return;
      });
      this.div!.style.cursor = f? 'pointer': '';
    })

    if (options.tooltipField || options.selectable) {
      this.map.on('pointermove', event => {
        const pixel = event.pixel;
        const f = this.map.forEachFeatureAtPixel(pixel, function (feature, hlayer) {
          if (feature && hlayer === layer) return feature;
          else return;
        });
        if (options.tooltipField) {
          let tooltip = this.tooltipOverlay.getElement()
          if (f) {
            this.tooltipOverlay.setPosition(event.coordinate);
            tooltip!.innerHTML = f.get(options.tooltipField);
            tooltip!.style.display = '';
          }
          else
            tooltip!.style.display = 'none';
        }
        if (options.selectable){
          this.div!.style.cursor = f? 'pointer': '';
        }
      });
    }
    if (options.selectable) {
      const select = new Select({
        condition: click,
        layers: [layer],
        style: new Style({
          stroke: new Stroke({
            color: 'rgb(255, 129, 0)',
            width: 1,
          }),
          fill: new Fill({
            color: 'rgba(250, 181, 51, 0.8)'
          }),
        }),
        toggleCondition: always,
        multi: true
      })
      this.map.addInteraction(select);
    }

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
