import { View, Feature, Map, Overlay, Collection } from 'ol';
import { Coordinate } from 'ol/coordinate';
import { ScaleLine, defaults as DefaultControls } from 'ol/control';
import * as olProj from 'ol/proj'
import { Layer } from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer";
import GeoJSON from 'ol/format/GeoJSON';
import { bbox as bboxStrategy } from 'ol/loadingstrategy';
import TileWMS from 'ol/source/TileWMS';
import XYZ from 'ol/source/XYZ';
import { Stroke, Style, Fill, Icon } from 'ol/style';
import { Select } from "ol/interaction";
import { click, singleClick, always } from 'ol/events/condition';
import { EventEmitter } from "@angular/core";
import { Polygon } from "ol/geom";
import { fromExtent } from 'ol/geom/Polygon';
import { saveAs } from 'file-saver';
import MVT from 'ol/format/MVT';
import VectorTileLayer from 'ol/layer/VectorTile';
import VectorTileSource from 'ol/source/VectorTile';
import { defer } from "rxjs";
import RenderFeature from "ol/render/Feature";

export class OlMap {
  target: string;
  view: View;
  map: Map;
  layers: Record<string, Layer<any>> = {};
  overlays: Record<string, Layer<any>> = {};
  mapProjection: string;
  div: HTMLElement | null;
  tooltipOverlay: Overlay;
  // emits all selected features
  selected = new EventEmitter<{ layer: Layer<any>, selected: Feature<any>[], deselected: Feature<any>[] }>();

  constructor( target: string,
               options: { center?: Coordinate, zoom?: number, projection?: string,
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

  getExtent(): Polygon {
    const extent = this.map.getView().calculateExtent(this.map.getSize());
    return fromExtent(extent);
  }

  centerOnLayer(name: string): void{
    const layer = this.layers[name],
          source = layer.getSource();
    this.map.getView().fit(source.getExtent());
  }

  /**
   * animated zoom into/out of map
   *
   * @param zoom - positive: increase zoom, negative: decrease zoom by number
   * @param duration - animation duration
   */
  zoom(zoom: number, duration: number = 250): void {
    this.view.animate({
      zoom: this.view.getZoom()! + zoom,
      duration: duration
    })
  }

  toggleFullscreen(): void {
    if (document.fullscreenElement === this.div){
      document.exitFullscreen();
    }
    else {
      this.div!.requestFullscreen();
    }
  }

  addTileServer(name: string, url: string, options: { params?: any,
    visible?: boolean, opacity?: number, xyz?: boolean, attribution?: string } = {}): Layer<any>{

    if (this.layers[name] != null) this.removeLayer(name)

    const attributions = options.attribution? [options.attribution]: [];
    let source = (options.xyz) ?
      new XYZ({
        url: url,
        attributions: attributions,
        attributionsCollapsible: false,
        crossOrigin: '*'
      }) :
      new TileWMS({
        url: url,
        params: options.params || {},
        serverType: 'geoserver',
        attributions: attributions,
        attributionsCollapsible: false,
        crossOrigin: '*'
    })

    let layer = new TileLayer({
      opacity: (options.opacity != undefined) ? options.opacity: 1,
      source: source,
      visible: options.visible === true
    });
    layer.set('name', name);
    this.map.addLayer(layer);
    this.layers[name] = layer;

    return layer;
  }

  addVectorTileLayer(name: string, url: string, options: {
      params?: any,
      visible?: boolean, opacity?: number,
      stroke?: { color?: string, width?: number, dash?: number[], selectedColor?: string, selectedDash?: number[], mouseOverColor?: string },
      fill?: { color?: string, selectedColor?: string, mouseOverColor?: string },
      tooltipField?: string,
      featureClass?: 'feature' | 'renderFeature'
    } = {}): Layer<any> {
    const source = new VectorTileSource({
      format: new MVT({ featureClass: (options.featureClass === 'feature')? Feature: RenderFeature }),
      url: url
    });
    const layer = new VectorTileLayer({
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
        })
      })
    })
    layer.set('name', name);
    this.setMouseOverLayer(layer, {
      tooltipField: options?.tooltipField,
      fillColor: options?.fill?.mouseOverColor,
      strokeColor: options?.stroke?.mouseOverColor,
      strokeWidth: options?.stroke?.width || 1
    });
    this.map.addLayer(layer);
    this.layers[name] = layer;
    // source.on('tileloadend', function(evt) {
    //   const z = evt.tile.getTileCoord()[0];
    //   // @ts-ignore
    //   const features = evt.tile.getFeatures();
    // });
    return layer;
  }

  addVectorLayer(name: string, options: {
      url?: any, params?: any,
      visible?: boolean, opacity?: number,
      selectable?: boolean, tooltipField?: string,
      stroke?: { color?: string, width?: number, dash?: number[],
        selectedColor?: string, mouseOverColor?: string, selectedDash?: number[],
        mouseOverWidth?: number
      },
      fill?: { color?: string, selectedColor?: string, mouseOverColor?: string },
    } = {}): Layer<any> {

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

    layer.set('name', name);
    this.setMouseOverLayer(layer, {
      tooltipField: options?.tooltipField,
      cursor: (options?.selectable)? 'pointer': undefined,
      fillColor: options?.fill?.mouseOverColor,
      strokeColor: options?.stroke?.mouseOverColor,
      strokeWidth: options?.stroke?.mouseOverWidth || options?.stroke?.width || 1
    });
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

  private setMouseOverLayer(layer: Layer<any>, options: {
    cursor?: string,
    tooltipField?: string,
    fillColor?: string,
    strokeColor?: string,
    strokeWidth?: number
  }){
    // avoid setting map interactions if nothing is defined to set anyway
    if (!(options.cursor || options.tooltipField || options.fillColor || options.strokeColor)) return;

    if (options.tooltipField)
      layer.set('showTooltip', true);

    let hoverStyle: Style | undefined;

    if (options.fillColor || options.strokeColor) {
      this.overlays[layer.get('name')] = new VectorLayer({
        source: new VectorSource(),
        map: this.map,
        style: new Style({
          fill: new Fill({ color: options.fillColor || 'rgba(0,0,0,0)' }),
          stroke: new Stroke({ color: options.strokeColor || 'rgba(0,0,0,0)', width: options.strokeWidth || 1 })
        }),
      });
    }
    this.map.on('pointermove', event => {
      const showTooltip = layer.get('showTooltip') && layer.getVisible();
      if (!showTooltip) return;
      const pixel = event.pixel;
      const hoveredFeat = this.map.forEachFeatureAtPixel(pixel, (feature, hlayer) => {
        if (feature && hlayer === layer) return feature;
        else return;
      });
      const overlay = this.overlays[layer.get('name')];
      if (overlay){
        overlay.getSource().clear();
        // RenderFeatures (VectorTiles) do not have a geometry
        if (hoveredFeat && hoveredFeat instanceof Feature) {
          overlay.getSource().addFeature(hoveredFeat);
        }
      }
      if (options.tooltipField) {
        let tooltip = this.tooltipOverlay.getElement()
        if (hoveredFeat) {
          this.tooltipOverlay.setPosition(event.coordinate);
          // let coords = this.map.getCoordinateFromPixel(pixel);
          tooltip!.innerHTML = hoveredFeat.get(options.tooltipField); // + `<br>${coords[0]}, ${coords[1]}`;
          tooltip!.style.display = '';
        }
        else
          tooltip!.style.display = 'none';
      }
      if (options.cursor && layer.getVisible()){
        this.div!.style.cursor = hoveredFeat? options.cursor: '';
      }
    });
    const overlay = this.overlays[layer.get('name')];
    if (overlay)
      this.map.getViewport().addEventListener('mouseout', event => {
        overlay.getSource().clear();
      });
  }

  addFeatures(layername: string, features: Feature<any>[]){
    const layer = this.layers[layername],
          source = layer.getSource();
    features.forEach(feature => {
      source.addFeature(feature);
    })
  }

  clear(layername: string){
    const layer = this.layers[layername];
    layer.getSource().clear();
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
    // ToDo: remove interactions
    let layer = this.layers[name];
    if (!layer) return;
    delete this.overlays[layer.get('name')];
    this.map.removeLayer(layer);
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

  exportCanvas(): HTMLCanvasElement {
    const mapCanvas = document.createElement('canvas');
    const size = this.map.getSize()!;
    mapCanvas.width = size[0];
    mapCanvas.height = size[1];
    const mapContext = mapCanvas.getContext('2d')!;
    mapContext.fillStyle = 'white';
    mapContext.fillRect(0, 0, mapCanvas.width, mapCanvas.height);
    const canvasList: HTMLCanvasElement[] = Array.from(
      this.map.getViewport().querySelectorAll('.ol-layer canvas, canvas.ol-layer'));
    canvasList.forEach((canvas: HTMLCanvasElement) => {
      if (canvas.width > 0) {
        const opacity =
          canvas.parentElement?.style?.opacity || canvas.style.opacity;
        mapContext.globalAlpha = opacity === '' ? 1 : Number(opacity);

        let matrix: any;
        const transform = canvas.style.transform;
        if (transform) {
          // Get the transform parameters from the style's transform matrix
          matrix = transform.match(/^matrix\(([^\(]*)\)$/)![1]
            .split(',')
            .map(Number);
        } else {
          matrix = [
            parseFloat(canvas.style.width) / canvas.width,
            0,
            0,
            parseFloat(canvas.style.height) / canvas.height,
            0,
            0,
          ];
        }
        // Apply the transform to the export map context
        CanvasRenderingContext2D.prototype.setTransform.apply(
          mapContext,
          matrix
        );
        mapContext.drawImage(canvas, 0, 0);
      }
    });
    return mapCanvas;
  }

  savePNG(): void {
    this.map.once('rendercomplete', evt => {
      const mapCanvas = this.exportCanvas();
      if (navigator.hasOwnProperty('msSaveBlob')) {
        // link download attribute does not work on MS browsers
        // @ts-ignore
        navigator.msSaveBlob(mapCanvas.msToBlob(), 'map.png');
      } else {
        saveAs(mapCanvas.toDataURL(), 'map.png');
      }
    });
    this.map.renderSync();
  }

  print(): void {
    const mapCanvas = this.exportCanvas();
    const data = mapCanvas.toDataURL();

    let html  = '<html><head><title></title></head>';
    html += '<body style="width: 100%; padding: 0; margin: 0;"';
    html += ' onload="window.focus(); window.print(); window.close()">';
    html += `<img src="${data}" /></body></html>`;
    const printWindow = window.open('', 'to_print', 'width=1000,height=600')!;

    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
  }

}
