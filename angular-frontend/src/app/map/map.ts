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
import { Stroke, Style, Fill, Text as OlText, RegularShape } from 'ol/style';
import { Select } from "ol/interaction";
import { click, singleClick, always } from 'ol/events/condition';
import { EventEmitter } from "@angular/core";
import { Polygon } from "ol/geom";
import { fromExtent } from 'ol/geom/Polygon';
import { saveAs } from 'file-saver';
import MVT from 'ol/format/MVT';
import VectorTileLayer from 'ol/layer/VectorTile';
import VectorTileSource from 'ol/source/VectorTile';
import RenderFeature from "ol/render/Feature";
import CircleStyle from "ol/style/Circle";

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
      featureClass?: 'feature' | 'renderFeature',
      labelField?: string,
      showLabel?: boolean
    } = {}): Layer<any> {
    const source = new VectorTileSource({
      format: new MVT({
        featureClass: (options.featureClass === 'feature')? Feature: RenderFeature,
        idProperty: 'id'
      }),
      url: url
    });

    const style = new Style({
      stroke: new Stroke({
        color:  options?.stroke?.color || 'rgba(0, 0, 0, 1.0)',
        width: options?.stroke?.width || 1,
        lineDash: options?.stroke?.dash
      }),
      fill: new Fill({
        color: options?.fill?.color || 'rgba(0, 0, 0, 0)'
      }),
      text: new OlText({
        font: '14px Calibri,sans-serif',
        overflow: true,
        placement: 'point',
        fill: new Fill({
          color: options?.stroke?.color || 'black'
        }),
        stroke: new Stroke({
          color: 'black',
          width: 1
        })
      })
    })
    const _this = this;
    const layer = new VectorTileLayer({
      source: source,
      declutter: true,
      visible: options?.visible === true,
      opacity: (options?.opacity != undefined) ? options?.opacity: 1,
      style: function(feature) {
        if (options?.labelField && layer.get('showLabel')) {
          const text = (_this.view.getZoom()! > 10 )? String(feature.get(options?.labelField)) : ''
          style.getText().setText(text);
        }
        else {
          style.getText().setText('');
        }
        return style;
      }
    })
    layer.set('name', name);

    // mouseover effects are a bit trickier with vector-tiles, need to add new layer with same source
    // to inspect and style features
    if (options.fill?.mouseOverColor || options?.stroke?.mouseOverColor) {
      let hoveredFeatId: number | undefined | string;
      const hoverStyle = new Style({
        fill: new Fill({ color: options.fill?.mouseOverColor || 'rgba(0,0,0,0)' }),
        stroke: new Stroke({
          color: options?.stroke?.mouseOverColor || 'rgba(0,0,0,0)',
          width: options?.stroke?.width || 1
        })
      })
      const selectionLayer = new VectorTileLayer({
        map: this.map,
        renderMode: 'vector',
        source: layer.getSource(),
        style: function (feature) {
          if (feature.getId() === hoveredFeatId) {
            return hoverStyle;
          }
          return;
        },
      });

      this.map.on('pointermove', event => {
        layer.getFeatures(event.pixel).then((features: Feature<any>[]) => {
          if (features.length === 0) {
            hoveredFeatId = undefined;
            selectionLayer.changed();
            return;
          }
          if (hoveredFeatId === features[0].getId()) return;
          hoveredFeatId = features[0].getId();
          selectionLayer.changed();
        });
      });
      this.map.getViewport().addEventListener('mouseout', event => {
        hoveredFeatId = undefined;
        selectionLayer.changed();
      });
    }

    this.setMouseOverLayer(layer, {
      tooltipField: options?.tooltipField
    });
    this.map.addLayer(layer);
    this.layers[name] = layer;
    return layer;
  }

  private getShape(shape: 'circle' | 'square' | 'star' | 'x' | 'triangle'): any {
    if (shape === 'circle')
      return new CircleStyle({
        radius: 5,
        fill: new Fill(),
        stroke: new Stroke
      })
    if (shape === 'square')
      return new RegularShape({
        points: 4,
        radius: 10,
        angle: Math.PI / 4,
        fill: new Fill(),
        stroke: new Stroke
      });
    if (shape === 'triangle')
      return new RegularShape({
        points: 3,
        radius: 10,
        rotation: Math.PI / 4,
        angle: 0,
        fill: new Fill(),
        stroke: new Stroke
      });
    if (shape === 'star')
      return new RegularShape({
        points: 5,
        radius: 10,
        radius2: 4,
        angle: 0,
        fill: new Fill(),
        stroke: new Stroke
      });
    if (shape === 'x')
      return new RegularShape({
        points: 4,
        radius: 10,
        radius2: 0,
        angle: Math.PI / 4,
        fill: new Fill(),
        stroke: new Stroke
      })
  }

  addVectorLayer(name: string, options: {
      url?: any, params?: any,
      visible?: boolean, opacity?: number,
      selectable?: boolean, tooltipField?: string,
      multiSelect?: boolean,
      shape?: 'circle' | 'square' | 'star' | 'x',
      mouseOverCursor?: string,
      stroke?: {
        color?: string, width?: number, dash?: number[],
        selectedColor?: string, mouseOverColor?: string, selectedDash?: number[],
        mouseOverWidth?: number
      },
      fill?: {
        color?: string | ((d: number) => string),
        selectedColor?: string, mouseOverColor?: string },
      radius?: number | ((d: number) => number),
      labelField?: string,
      valueField?: string,
      showLabel?: boolean
    } = {}): Layer<any> {

    // @ts-ignore
    const fillColor: string = (typeof(options?.fill?.color) === 'string')? options?.fill?.color: 'rgba(0, 0, 0, 0)';
    const strokeColor = options?.stroke?.color || 'rgba(0, 0, 0, 1.0)';
    const text = new OlText({
      font: '14px Calibri,sans-serif',
      overflow: true,
      placement: 'point',
      offsetX: 10,
      offsetY: 10,
      fill: new Fill({
        color: 'black'
      }),
      stroke: new Stroke({
        color: 'white',
        width: 2
      })
    });
    const style = new Style({
      stroke: new Stroke({
        color: strokeColor,
        width: options?.stroke?.width || 1,
        lineDash: options?.stroke?.dash
      }),
      fill: new Fill({
        color: fillColor
      }),
      text: text
    });

    const _this = this;
    if (this.layers[name] != null) this.removeLayer(name);
    let sourceOpt = options?.url? {
        format: new GeoJSON(),
        url: (options?.url)? options?.url: undefined,
        strategy: (options?.url)? bboxStrategy: undefined,
      }: {};
    let source = new VectorSource(sourceOpt);
    const styleFunc = function(feature: any) {
      if (options?.labelField && layer.get('showLabel')) {
        const text = (_this.view.getZoom()! > 9 )? String(feature.get(options?.labelField)) : ''
        style.getText().setText(text);
      }
      else {
        style.getText().setText('');
      }
      const zIndex = feature.get('zIndex');
      if (zIndex !== undefined)
        style.setZIndex(zIndex);
      const valueField = options?.valueField || 'value';
      if (options?.shape) {
        const shape = _this.getShape(options?.shape);
        if (options?.radius){
          const radius = (typeof options?.radius === 'function')? options.radius(Number(feature.get(valueField))): options.radius;
          console.log(radius)
          shape.setRadius(Math.round(radius));
        }
        shape.getFill().setColor(fillColor);
        shape.getStroke().setColor(strokeColor);
        style.setImage(shape);
      }
      if (typeof options?.fill?.color === 'function'){
        const color = options.fill.color(Number(feature.get(valueField)));
        style.getFill().setColor(color);
        if (options?.shape)
          // @ts-ignore
          style.getImage().getFill().setColor(color);
      }
      return style;
    };
    let layer = new VectorLayer({
      source: source,
      visible: options?.visible === true,
      opacity: (options?.opacity != undefined) ? options?.opacity: 1,
      style: styleFunc
    });

    layer.set('showLabel', (options?.showLabel !== undefined)? options?.showLabel: true);
    layer.set('name', name);
    this.setMouseOverLayer(layer, {
      tooltipField: options?.tooltipField,
      cursor: (options?.mouseOverCursor)? options?.mouseOverCursor: (options?.selectable)? 'pointer': undefined,
      fillColor: options?.fill?.mouseOverColor,
      strokeColor: options?.stroke?.mouseOverColor,
      strokeWidth: options?.stroke?.mouseOverWidth || options?.stroke?.width || 1
    });
    if (options?.selectable) {
      const selectStrokeColor = options.stroke?.selectedColor;
      const selectFillColor = options.fill?.selectedColor;
      let selectStyle;
      if (selectFillColor || selectStrokeColor) {
        selectStyle = new Style({
          stroke: new Stroke({
            color: selectStrokeColor || options.stroke?.color,
            width: options.stroke?.width || 1,
            lineDash: options?.stroke?.selectedDash
          }),
          fill: new Fill({
            color: selectFillColor || 'rgba(0,0,0,0)'
          }),
        });
        if (options?.shape) {
          const shape = this.getShape(options?.shape);
          shape.getFill().setColor(selectFillColor);
          shape.getStroke().setColor(selectStrokeColor);
          selectStyle.setImage(shape);
        }
      }
      const select = new Select({
        condition: click,
        layers: [layer],
        style: selectStyle || styleFunc,
        toggleCondition: always
      })
      this.map.addInteraction(select);
      select.on('select', event => {
        if (!options.multiSelect) {
          select.getFeatures().clear();
          if (event.selected.length > 0)
            select.getFeatures().push(event.selected[0]);
        }
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
    if (!(options.cursor || options.tooltipField || options.fillColor || options.strokeColor) || !layer.getVisible()) return;

    if (options.tooltipField)
      layer.set('showTooltip', true);

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
      layer.getFeatures(event.pixel).then((features: Feature<any>[]) => {
        const overlay = this.overlays[layer.get('name')];
        if (overlay) {
          overlay.getSource().clear();
          overlay.getSource().addFeatures(features);
        }
        if (options.tooltipField) {
          let tooltip = this.tooltipOverlay.getElement()
          if (features.length > 0) {
            this.tooltipOverlay.setPosition(event.coordinate);
            // let coords = this.map.getCoordinateFromPixel(pixel);
            tooltip!.innerHTML = features[0].get(options.tooltipField); // + `<br>${coords[0]}, ${coords[1]}`;
            tooltip!.style.display = '';
          } else
            tooltip!.style.display = 'none';
        }
        if (options.cursor && layer.getVisible()) {
          this.div!.style.cursor = features.length > 0 ? options.cursor : '';
        }
      });
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

  setSelectActive(layerName: string, active: boolean){
    const layer = this.getLayer(layerName),
          select = layer.get('select');
    select.setActive(active);
  }

  setShowLabel(layerName: string, show: boolean){
    const layer = this.getLayer(layerName);
    layer.set('showLabel', show);
    layer.changed();
  }

  getFeature(layerName: string, id: string | number){
    const layer = this.layers[layerName],
          features = layer.getSource().getFeatures();
    for (let i = 0; i < features.length; i++){
      const feature = features[i];
      if (feature.getId() == id) return feature
    }
    return null;
  }

  selectFeatures(layerName: string, ids: string[] | number[] | Feature<any>[], options?: { silent?: boolean, clear?: boolean }){
    const layer = this.layers[layerName],
          select = layer.get('select');

    let features: Feature<any>[] = [];
    if (options?.clear)
      select.getFeatures().clear();
    ids.forEach(f => {
      if (typeof(f) === 'number' || f instanceof String || typeof(f) === 'string') {
        // @ts-ignore
        f = this.getFeature(layerName, f);
      }
      if (!f) return;
      // @ts-ignore
      features.push(f);
      select.getFeatures().push(f);
    })
    if (!options?.silent)
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
