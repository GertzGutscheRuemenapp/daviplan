import { View, Feature, Map, Overlay, Collection } from 'ol';
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
import { EventEmitter } from "@angular/core";
import { layer } from "@fortawesome/fontawesome-svg-core";

export class OlMap {
  target: string;
  view: View;
  map: Map;
  layers: Record<string, Layer<any>> = {};
  mapProjection: string;
  div: HTMLElement | null;
  tooltipOverlay: Overlay;
  // emits all selected features
  selected = new EventEmitter<{ layer: Layer<any>, selected: Feature<any>[], deselected: Feature<any>[] }>();

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

  getLayer(name: string): Layer<any>{
    return this.layers[name];
  }

  centerOnLayer(name: string): void{
    const layer = this.layers[name],
          source = layer.getSource();
    this.map.getView().fit(source.getExtent());
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

  addVectorLayer(name: string, options?: {
    url?: any, params?: any,
    visible?: boolean, opacity?: number,
    selectable?: boolean, tooltipField?: string,
    stroke?: {color?: string, width?: number, dash?: number[], selectedColor?: string, selectedDash?: number[]},
    fill?: {color?: string, selectedColor?: string},
  }): Layer<any> {

    if (this.layers[name] != null) this.removeLayer(name);
    let sourceOpt = options?.url? {
        format: new GeoJSON(),
        url: (options?.url)? options?.url: undefined,
        strategy: (options?.url)? bboxStrategy: undefined,
      }: {};
    let source = new VectorSource(sourceOpt);
    let layer = new VectorLayer({
      source: source,
      visible: options?.visible === true,
      opacity: (options?.opacity != undefined) ? options?.opacity: 1,
      style: new Style({
        stroke: new Stroke({
          color:  options?.stroke?.color || 'rgba(0, 0, 0, 1.0)',
          width: options?.stroke?.width || 1,
          lineDash: options?.stroke?.dash
        }),
        fill: new Fill({
          color: options?.fill?.color || 'rgba(0, 0, 0, 0)'
        }),
      }),
    });

    if (options?.tooltipField || options?.selectable) {
      layer.set('showTooltip', true);
      this.map.on('pointermove', event => {
        const showTooltip = layer.get('showTooltip') && layer.getVisible();
        if (!showTooltip) return;
        const pixel = event.pixel;
        const f = this.map.forEachFeatureAtPixel(pixel, function (feature, hlayer) {
          if (feature && hlayer === layer) return feature;
          else return;
        });
        if (options?.tooltipField) {
          let tooltip = this.tooltipOverlay.getElement()
          if (f) {
            this.tooltipOverlay.setPosition(event.coordinate);
            // let coords = this.map.getCoordinateFromPixel(pixel);
            tooltip!.innerHTML = f.get(options.tooltipField); // + `<br>${coords[0]}, ${coords[1]}`;
            tooltip!.style.display = '';
          }
          else
            tooltip!.style.display = 'none';
        }
        if (options?.selectable){
          this.div!.style.cursor = f? 'pointer': '';
        }
      });
    }
    if (options?.selectable) {
      const select = new Select({
        condition: click,
        layers: [layer],
        style: new Style({
          stroke: new Stroke({
            color: options.stroke?.selectedColor || 'rgb(255, 129, 0)',
            width: options.stroke?.width || 1,
            lineDash: options?.stroke?.selectedDash
          }),
          fill: new Fill({
            color: options.fill?.selectedColor || 'rgba(0, 0, 0, 0)'
          }),
        }),
        toggleCondition: always,
        multi: true
      })
      this.map.addInteraction(select);
      select.on('select', event => {
        this.selected.emit({ layer: layer, selected: event.selected, deselected: event.deselected });
      })
      layer.set('select', select);
    }

    this.map.addLayer(layer);
    this.layers[name] = layer;

    return layer;
  }

  toggleSelect(layerName: string, active: boolean){
    const layer = this.getLayer(layerName),
          select = layer.get('select');
    select.setActive(active);
  }

  getFeature(layerName: string, id: string){
    const layer = this.layers[layerName],
          features = layer.getSource().getFeatures();
    for (let i = 0; i < features.length; i++){
      const feature = features[i];
      if (feature.getId() == id) return feature
    }
    return null;
  }

  selectFeatures(layerName: string, ids: string[] | Feature<any>[]){
    const layer = this.layers[layerName],
          select = layer.get('select');

    let features: Feature<any>[] = [];
    ids.forEach(f => {
      if (f instanceof String) {
        // @ts-ignore
        f = this.getFeature(layerName, f);
      }
      // @ts-ignore
      features.push(f);
      select.getFeatures().push(f);
    })
    select.dispatchEvent({
      type: 'select',
      selected: features,
      deselected: []
    });
  }

  deselectFeatures(){

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
