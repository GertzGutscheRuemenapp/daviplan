import { Injectable, EventEmitter } from '@angular/core';
import { AreaLevel, ExtLayer, ExtLayerGroup, Symbol } from '../rest-interfaces';
import { OlMap } from './map'
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../rest-api";
import { sortBy } from "../helpers/utils";
import { WKT } from "ol/format";
import { SettingsService } from "../settings.service";
import { environment } from "../../environments/environment";
import { v4 as uuid } from 'uuid';
import { SelectionModel } from "@angular/cdk/collections";
import { Feature } from 'ol';
import { Layer as OlLayer } from 'ol/layer'
import { Geometry, Polygon, Point } from "ol/geom";
import { getCenter } from 'ol/extent';
import { Icon, Style } from "ol/style";
import { RestCacheService } from "../rest-cache.service";

const backgroundLayers: any[] = [
  {
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    description: 'Offizielle Weltkarte von OpenStreetMap',
    attribution: '©<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende<a>',
    type: 'tiles',
  },
  {
    name: 'TopPlusOpen',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Normalausgabe',
    type: 'wms',
    layerName: 'web'
  },
  {
    name: 'TopPlusOpen grau',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Graustufendarstellung',
    type: 'wms',
    layerName: 'web_grau'
  }
]


export class MapLayerGroup {
  name: string;
  id?: number | string;
  children: MapLayer[] = [];
  external: boolean;
  mapControl?: MapControl;
  zIndex?: number;

  constructor(name: string, options?: {
    zIndex?: number,
    external?: boolean,
    id?: number
  }) {
    this.id = options?.id;
    this.name = name;
    this.external = options?.external || false;
    this.zIndex = options?.zIndex;
  }

  addLayer(layer: MapLayer) {
    layer.group = this;
    // if not already a child
    if (this.children.indexOf(layer) < 0) {
      this.children.push(layer);
      this.mapControl?.addLayer(layer);
    }
  }
}

abstract class MapLayer {
  featureSelected?: EventEmitter<{ feature: any, selected: boolean }>
  id?: number | string;
  mapId?: string;
  group?: MapLayerGroup;
  name: string;
  url?: string;
  layerName?: string;
  description?: string = '';
  zIndex?: number = 1;
  legend?: {
    colors?: string[],
    labels?: string[],
    elapsed?: boolean
  }
  selectable?: boolean;
  labelField?: string;
  showLabel?: boolean;
  attribution?: string;
  legendUrl?: string;
  opacity?: number = 1;
  visible?: boolean = true;
  symbol?: Symbol;
  type?: "wms" | "vector-tiles" | "tiles" | "vector";
  map?: OlMap;

  constructor(name: string, options?: {
    id?: string,
    group?: MapLayerGroup,
    url?: string,
    layerName?: string,
    description?: string,
    zIndex?: number,
    legend?: {
      colors?: string[],
      labels?: string[],
      elapsed?: boolean
    }
    symbol?: Symbol,
    selectable?: boolean,
    labelField?: string,
    showLabel?: boolean,
    attribution?: string,
    legendUrl?: string,
    opacity?: number,
    visible?: boolean,
    type?: "wms" | "vector-tiles" | "tiles" | "vector"
  }) {
    this.name = name;
    this.id = options?.id;
    this.map = options?.group?.mapControl?.map;
    if (options?.group) options?.group.addLayer(this);
  }

  setRadi() {

  }

  setColors() {

  }

  setOpacity(opacity: number) {
    this.opacity = opacity;
    this.map?.setOpacity(this.mapId!, opacity);
  }

  setVisible(visible: boolean) {
    this.visible = visible;
    this.map?.setVisible(this.mapId!, visible);
  }

  setShowLabel(show: boolean): void {
    this.showLabel = show;
    this.map?.setShowLabel(this.mapId!, show);
  }

  setSelectable(selectable: boolean): void {
    this.selectable = selectable;
    this.map?.setSelectActive(this.mapId!, selectable);
  }

  addFeatures(features: any[], options?: {
    properties?: string, geometry?: string, zIndex?: string
  }): void {
    if (!this.map) return;
    let olFeatures: Feature<any>[] = [];
    const properties = (options?.properties !== undefined) ? options?.properties : 'properties';
    const geometry = (options?.geometry !== undefined) ? options?.geometry : 'geometry';
    features.forEach(feature => {
      const olFeature = new Feature(feature[geometry!]);
      if (feature.id) {
        olFeature.set('id', feature.id);
        olFeature.setId(feature.id);
      }
      olFeature.setProperties(feature[properties]);
      olFeatures.push(olFeature);
    })
    if (options?.zIndex) {
      const attr = options?.zIndex;
      olFeatures = olFeatures.sort((a, b) =>
        (a.get(attr) > b.get(attr)) ? 1 : (a.get(attr) < b.get(attr)) ? -1 : 0);
      olFeatures.forEach((feat, i) => feat.set('zIndex', olFeatures.length - i));
    }
    this.map.addFeatures(this.mapId!, olFeatures);
  }

  clearFeatures(id: number | string): void {
    this.map?.clear(this.mapId!);
  }

  abstract addToMap(map?: OlMap): OlLayer<any> | undefined;
}

export class WMSLayer extends MapLayer {
  addToMap(map?: OlMap): OlLayer<any> | undefined  {
    map = map || this.map;
    if(!map) return;
    const olLayer = map.addTileServer(
      this.name, this.url!, {
        params: { layers: this.layerName },
        visible: this.visible,
        opacity: this.opacity,
        attribution: this.attribution
      });
    if (!this.legendUrl) {
      let url = olLayer.getSource().getLegendUrl(1, { layer: this.layerName });
      if (url) url += '&SLD_VERSION=1.1.0';
      this.legendUrl = url;
    }
    return olLayer;
  }
}

export class TilesLayer extends MapLayer {
  addToMap(map?: OlMap): OlLayer<any> | undefined {
    map = map || this.map;
    if(!map) return;
    const olLayer = map!.addTileServer(
      this.name, this.url!, {
        params: { layers: this.layerName },
        visible: this.visible,
        opacity: this.opacity,
        xyz: true,
        attribution: this.attribution
      });
    return olLayer;
  }
}

export class VectorTileLayer extends MapLayer {
  addToMap(map?: OlMap): void {

  }
}

export class VectorLayer extends MapLayer {
  addToMap(map?: OlMap): OlLayer<any> | undefined {
    map = map || this.map;
    if(!map) return;
    this.mapId = uuid();
    return this.map.addVectorLayer(this.mapId, {
      visible: this.visible,
      opacity: this.opacity,
      valueField: this.valueField,
      mouseOverCursor: this.mouseOver?.cursor,
      multiSelect: this.select?.multi,
      stroke: {
        color: this.symbol?.strokeColor, width: options?.strokeWidth || 2,
        mouseOverColor: this.mouseOver?.strokeColor,
        selectedColor: this.select?.strokeColor
      },
      fill: {
        // color: (options?.colorFunc)? options?.colorFunc: this.symbol?.fillColor,
        // mouseOverColor: options?.mouseOver?.fillColor,
        // selectedColor: options?.select?.fillColor
      },
      // radius: options?.radiusFunc,
      labelField: this.labelField,
      tooltipField: this.tooltipField,
      shape: (this.symbol?.symbol !== 'line')? this.symbol?.symbol: undefined,
      selectable: this.selectable,
      showLabel: this.showLabel
    })
  }
}

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};
  backgroundLayers: any[] = backgroundLayers;
  // layerGroups$?: BehaviorSubject<Array<ExtLayerGroup>>;

  constructor(private http: HttpClient, private restService: RestCacheService, private settings: SettingsService) { }

  get(target: string): MapControl {
    let control = this.controls[target];
    if(!control){
      control = new MapControl(target, this, this.settings);
      control.destroyed.subscribe(target => delete this.controls[target]);
      control.init();
      this.controls[target] = control;
    }
    return control;
  }

  getLayers( options?: { internal?: boolean, external?: boolean, reset?: boolean } ): Observable<MapLayerGroup[]>{
    const observable = new Observable<MapLayerGroup[]>(subscriber => {
      const observables: Observable<MapLayerGroup[]>[] = [];
      if (options?.internal)
        observables.push(this.fetchInternalLayers(options?.reset));
      if (options?.external)
        observables.push(this.fetchExternalLayers(options?.reset));
      forkJoin(...observables).subscribe((merged: MapLayerGroup[]) => {
        // @ts-ignore
        const flatGroups: MapLayerGroup[] = [].concat.apply([], merged);
        subscriber.next(flatGroups);
        subscriber.complete();
      })
    });
    return observable;
  }

  private fetchInternalLayers(reset: boolean = false): Observable<MapLayerGroup[]> {
    const observable = new Observable<MapLayerGroup[]>(subscriber => {
      this.restService.getAreaLevels({ active: true, reset: reset }).subscribe(levels => {
        levels = sortBy(levels, 'order');//.reverse();
        let groups = [];
        const group = new MapLayerGroup('Gebiete', { zIndex: 2, external: false });
        let layers: MapLayer[] = [];
        sortBy(levels, 'order').forEach(level => {
          // skip levels with no symbol (aka should not be displayed)
          if (!level.symbol) return;
          // areas have no fill
          level.symbol.fillColor = '';
          let tileUrl = level.tileUrl!;
          // "force" https in production, backend returns http (running in container)
          if (environment.production) {
            tileUrl = tileUrl.replace('http:', 'https:');
          }
          const mLayer = new MapLayer(level.name, {
            type: "vector-tiles",
            url: tileUrl,
            description: `Gebiete der Gebietseinheit ${level.name}`,
            symbol: level.symbol,
            labelField: level.labelField
          })
          layers.push(mLayer);
        });
        if (layers) {
          layers.forEach(mlayer => group.addLayer(mlayer));
          groups.push(group);
        }
        subscriber.next(groups);
        subscriber.complete();
      })
    })
    return observable;
  }

  private fetchExternalLayers(reset: boolean = false): Observable<MapLayerGroup[]> {
    const observable = new Observable<MapLayerGroup[]>(subscriber => {
      this.restService.getLayerGroups({ reset: reset }).subscribe(groups => {
        groups = sortBy(groups, 'order');
        const mGroups: MapLayerGroup[] = groups.map(group =>
          new MapLayerGroup(group.name, { id: group.id, external: group.external, zIndex: group.order }));
        this.restService.getLayers({ active: true, reset: reset }).subscribe(layers => {
          layers = sortBy(layers, 'order');
          layers.forEach(layer => {
            const mGroup = mGroups.find(mGroup => { return mGroup.id === layer.group });
            if (mGroup) {
              const mLayer = new MapLayer(layer.name, {
                type: 'wms',
                url: layer.url,
                description: layer.description,
                zIndex: layer.order
              })
              mGroup.addLayer(mLayer);
            }
          })
          subscriber.next(mGroups);
          subscriber.complete();
        })
      })
    })
    return observable;
  }
}

export class MapControl {
  srid = 3857;
  target = '';
  destroyed = new EventEmitter<string>();
  map?: OlMap;
  mapDescription = '';
  layerGroups: BehaviorSubject<Array<MapLayerGroup>> = new BehaviorSubject<Array<MapLayerGroup>>([]);
  private _localLayerGroups: MapLayerGroup[] = [];
  private _serviceLayerGroups: MapLayerGroup[] = [];
  private markerLayer?: OlLayer<any>;
  mapExtents: any = {};
  editMode: boolean = true;
  background?: MapLayer;
  markerImg = `${environment.backend}/static/img/map-marker-red.svg`;

  constructor(target: string, private mapService: MapService, private settings: SettingsService) {
    this.target = target;
    // call destroy on page reload
    window.onbeforeunload = () => this.destroy();
    this.settings.user?.get('extents').subscribe(extents => {
      this.mapExtents = extents || {};
    })
  }

  init(): void {
    this.map = new OlMap(this.target, { projection: `EPSG:${this.srid}` });
    this.map.selected.subscribe(evt => {
      if (evt.selected && evt.selected.length > 0)
        this.onFeatureSelected(evt.layer, evt.selected);
      if (evt.deselected && evt.deselected.length > 0)
        this.onFeatureDeselected(evt.layer, evt.deselected);
    })
    this.settings.user?.get(this.target).subscribe(mapSettings => {
      mapSettings = mapSettings || {};
      const editMode = mapSettings['legend-edit-mode'];
      this.editMode = (editMode != undefined)? editMode : true;
      const backgroundId = parseInt(mapSettings[`background-layer`]);
      this.background = (backgroundId)? this.mapService.backgroundLayers.find(
        l => { return l.id === backgroundId }) : this.mapService.backgroundLayers[1];
      if (this.background)
        this.background.s = mapSettings[`layer-opacity-${this.background.id}`] || 1;
      for (let layer of this.mapService.backgroundLayers) {
        layer.opacity = parseFloat(mapSettings[`layer-opacity-${layer.id}`]) || 1;
        this._addLayerToMap(layer, {
          visible: layer === this.background
        });
      }
    })
    this.getServiceLayerGroups();
    this.markerLayer = this.map!.addVectorLayer('marker-layer',
      {stroke: {width: 5, color: 'red'}, fill: {color: 'red'}, radius: 10, visible: true, zIndex: 100});
  }

  private getServiceLayerGroups(reset: boolean = false): void {
    this.mapService.getLayers({ reset: reset }).subscribe(layerGroups => {
      // ToDo: remember former checked layers on reset
      layerGroups.forEach(group => {
        if (!group.children) return;
        for (let layer of group.children!.slice().reverse()) {
          let visible = false;
          // if (Boolean(this.mapSettings[`layer-checked-${layer.id}`])) {
          //   this.checklistSelection.select(layer);
          //   visible = true;
          // }
          // layer.opacity = parseFloat(this.mapSettings[`layer-opacity-${layer.id}`]) || 1;
          this._addLayerToMap(layer, { visible: visible });
        }
      })
      this.layerGroups.next(this._serviceLayerGroups);
    })
  }

  getLayers(): MapLayer[] {
    let layers: MapLayer[] = [];
    this._localLayerGroups.concat(this._serviceLayerGroups).forEach(g => layers.concat(g.children));
    // if (this.background) layers.push(this.background);
    return layers;
  }

  getLayer(id: number |string): MapLayer | undefined {
    // ToDo: background as well?
    return this.getLayers().find(l => l.id === id);
  }

  getGroup(id: number |string): MapLayerGroup | undefined {
    // ToDo: background as well?
    return this.getLayers().find(l => l.id === id);
  }

  addLayer(layer: MapLayer) {
    // let mlayer: MapLayer = (layer instanceof MapLayer)? layer: new MapLayer(layer.name);
    if (layer.mapControl) throw `Layer ${layer.name} already set to another map`;
    const layerGroups = this._localLayerGroups.concat(this._serviceLayerGroups);
    if (!layer.group) {
      let group = layerGroups.find(group => group.name === 'Sonstiges');
      if (!group){
        group = new MapLayerGroup('Sonstiges', { zIndex: 0 });
        this.addGroup(group, false);
      }
      layer.group = group;
    }
    layer.group.children?.push(layer);
    this._addLayerToMap(layer, {
      visible: options?.visible,
      tooltipField: options?.tooltipField,
      colorFunc: options?.colorFunc,
      radiusFunc: options?.radiusFunc,
      valueField: options?.valueField,
      mouseOver: options?.mouseOver,
      select: options?.select,
      selectable: options?.selectable,
      strokeWidth: options?.strokeWidth
    });
    if (options?.selectable){
      layer.featureSelected = new EventEmitter<any>();
    }
    if (options?.visible)
      this.checklistSelection.select(layer);
    else
      this.checklistSelection.deselect(layer);
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
    return layer;
    this._addLayerToMap(layer);
  }
/*

  private _addVectorLayerToMap(layer: MapLayer): OlLayer<any>{

  }

  private _addVectorTileLayerToMap(layer: MapLayer): OlLayer<any>{

  }

  private _addWmsLayerToMap(layer: MapLayer):
*/

  getBackgroundLayers(): ExtLayer[]{
    return this.mapService.backgroundLayers;
  }

  addMarker(geometry: Geometry): Feature<any> {
    this.removeMarker();
    if (geometry instanceof Polygon) {
      geometry = new Point(getCenter(geometry.getExtent()));
    }
    const marker = new Feature(geometry);

    const iconStyle = new Style({
      image: new Icon({
        anchor: [0.5, 0.8],
        anchorXUnits: 'fraction',
        anchorYUnits: 'fraction',
        src: this.markerImg,
        scale: 0.05
      }),
    });

    marker.setStyle(iconStyle);
    this.map?.addFeatures('marker-layer', [marker]);
    return marker;
  }

  removeMarker(): void {
    this.map?.clear('marker-layer');
  }

  refresh(options?: { internal?: boolean, external?: boolean }): void {
    this.getLayers().forEach(l => {
      if (l.mapId !== undefined) this.map?.removeLayer(l.mapId);
    });
    this.getServiceLayerGroups();
  }

  /**
   * add a layer-group to this map only
   * sets unique id if id is undefined
   *
   * @param group
   * @param emit
   */
  addGroup(group: MapLayerGroup, emit= true): void {
    if (group.id == undefined)
      group.id = uuid();
    this._localLayerGroups.push(group);
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
  }

  /**
   * remove a layer-group and its children, can only remove groups added specifically to this map
   * (not the global ones)
   *
   * @param id
   * @param emit
   */
  removeGroup(id: number | string | MapLayerGroup, emit= true): void {
    const idx = this._localLayerGroups.findIndex(group => group.id === id);
    if (idx < 0) return;
    this.clearGroup(id, false);
    this._localLayerGroups.splice(idx, 1);
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
  }

  clearGroup(id: number | string, emit= true): void {
    const group = this._localLayerGroups.find(group => group.id === id);
    if (!(group && group.children)) return;
    group.children.forEach(layer => {
      if (layer.id != undefined) {
        delete this.layerMap[layer.id];
        this._removeLayerFromMap(layer);
      }
    });
    group.children = [];
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
  }

  removeLayer(id: number | string, emit= true): void {
    const layer = this.layerMap[id];
    if (!layer) return;
    const layerGroups = this._localLayerGroups.concat(this._serviceLayerGroups);
    const group = layerGroups.find(group => layer.group === group.id)!;
    if (!group) return;
    const idx = group.children!.indexOf(layer);
    this._removeLayerFromMap(layer);
    if (idx >= 0)
      group.children!.splice(idx, 1);
    delete this.layerMap[id];
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
  }

  private _removeLayerFromMap(layer: ExtLayer){
    this.map?.removeLayer(this.mapId(layer));
  }

  private onFeatureSelected(ollayer: OlLayer<any>, selected: Feature<any>[]): void {
    const layer = this.getLayer(ollayer.get('name'));
    if (layer && layer.featureSelected)
      selected.forEach(feature => layer.featureSelected!.emit({ feature: feature, selected: true }));
  }

  private onFeatureDeselected(ollayer: OlLayer<any>, deselected: Feature<any>[]): void {
    const layer = this.getLayers().find(l => l.mapId === ollayer.get('id'));
    if (layer)
      deselected.forEach(feature => layer.featureSelected!.emit({ feature: feature, selected: false }));
  }

  /**
   * add a layer to this map only
   * sets unique id if id is undefined
   * if layer has no assigned group adds to group 'Sonstiges' (created if not existing)
   *
   * @param layer
   * @param options
   * @param emit
   */
 /* addLayser(layer: ExtLayer, options?: {
    visible?: boolean,
    selectable?: boolean,
    tooltipField?: string,
    colorFunc?: ((d: number) => string),
    radiusFunc?: ((d: number) => number),
    valueField?: string,
    zIndexField?: string,
    mouseOver?: {
      fillColor?: string,
      strokeColor?: string,
      cursor?: string
    },
    strokeWidth?: number,
    select?: {
      multi?: boolean,
      fillColor?: string,
      strokeColor?: string
    }
  }, emit= true): ExtLayer {
    if (layer.id == undefined)
      layer.id = uuid();
    const layerGroups = this._localLayerGroups.concat(this._serviceLayerGroups);
    let group;
    if (!layer.group) {
      group = layerGroups.find(group => group.name === 'Sonstiges') || this.addGroup({
        order: 0,
        name: 'Sonstiges'
      }, false)
    }
    else
      group = layerGroups.find(group => layer.group === group.id)!;
    if (!group.children) group.children = [];
    group.children?.push(layer);
    this._addLayerToMap(layer, {
      visible: options?.visible,
      tooltipField: options?.tooltipField,
      colorFunc: options?.colorFunc,
      radiusFunc: options?.radiusFunc,
      valueField: options?.valueField,
      mouseOver: options?.mouseOver,
      select: options?.select,
      selectable: options?.selectable,
      strokeWidth: options?.strokeWidth
    });
    if (options?.selectable){
      layer.featureSelected = new EventEmitter<any>();
    }
    if (options?.visible)
      this.checklistSelection.select(layer);
    else
      this.checklistSelection.deselect(layer);
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
    return layer;
  }*/

  private _addLayerToMap(layer: MapLayer, options?: {
    visible?: boolean,
    tooltipField?: string,
    colorFunc?: ((d: number) => string),
    radiusFunc?: ((d: number) => number),
    valueField?: string,
    strokeWidth?: number,
    mouseOver?: {
      fillColor?: string,
      strokeColor?: string,
      cursor?: string
    }
  }) {

    const opacity = (layer.opacity !== undefined)? layer.opacity : 1;
    if (layer.type === 'vector') {
      this.map!.addVectorLayer(this.mapId(layer), {
        visible: options?.visible,
        opacity: opacity,
        valueField: options?.valueField,
        mouseOverCursor: options?.mouseOver?.cursor,
        multiSelect: options?.select?.multi,
        stroke: {
          color: layer.symbol?.strokeColor, width: options?.strokeWidth || 2,
          mouseOverColor: options?.mouseOver?.strokeColor,
          selectedColor: options?.select?.strokeColor
        },
        fill: {
          color: (options?.colorFunc)? options?.colorFunc: layer.symbol?.fillColor,
          mouseOverColor: options?.mouseOver?.fillColor,
          selectedColor: options?.select?.fillColor
        },
        radius: options?.radiusFunc,
        labelField: layer.labelField,
        tooltipField: options?.tooltipField,
        shape: (layer.symbol?.symbol !== 'line')? layer.symbol?.symbol: undefined,
        selectable: options?.selectable,
        showLabel: layer.showLabel
      })
    }
    else if (layer.type === 'vector-tiles') {
       this.map!.addVectorTileLayer(this.mapId(layer), layer.url!,{
         visible: options?.visible,
         opacity: opacity,
         stroke: { color: layer.symbol?.strokeColor, width: 2, mouseOverColor: options?.mouseOver?.strokeColor },
         fill: { color: layer.symbol?.fillColor, mouseOverColor: options?.mouseOver?.fillColor },
         tooltipField: options?.tooltipField,
         featureClass: (options?.mouseOver)? 'feature': 'renderFeature',
         labelField: 'label',
         showLabel: layer.showLabel
       });
    }
    else {
      const mapLayer = this.map!.addTileServer(
        this.mapId(layer),  layer.url!, {
          params: { layers: layer.layerName },
          visible: options?.visible,
          opacity: opacity,
          xyz: layer.type == 'tiles',
          attribution: layer.attribution
        });
      if (layer.type === 'wms' && !layer.legendUrl) {
          let url = mapLayer.getSource().getLegendUrl(1, { layer: layer.layerName });
          if (url) url += '&SLD_VERSION=1.1.0';
          layer.legendUrl = url;
        }
    }
    this.layerMap[layer.id!] = layer;
    this.olLayerIds[this.mapId(layer)] = layer.id!;
  }

  setBackground(id: number | string | undefined): void {
    if (id === undefined) return;
    this.background = this.mapService.backgroundLayers.find(l => { return l.id === id });
    this.mapSettings['background-layer'] = id;
    const layer = this.layerMap[id];
    if (layer){
      const mapLayer = this.map?.getLayer(this.mapId(layer));
      this.backgroundOpacity = mapLayer?.getOpacity() || 1;
    }
    this.mapService.backgroundLayers.forEach(layer => this.map?.setVisible(
      this.mapId(layer), layer.id === id));
  }

  private mapId(layer: ExtLayer): string {
    return `${layer.name}-${layer.id}`;
  }

  zoomTo(layer: ExtLayer): void {
    const mapLayer = this.map?.getLayer(this.mapId(layer)),
          _this = this;
    mapLayer!.getSource().once('featuresloadend', (evt: any) => {
      this.map?.centerOnLayer(this.mapId(layer));
    })
  }

  zoomToProject(): void {
    this.settings.projectSettings$.subscribe(settings => {
      if (!settings.projectArea) return;
      const format = new WKT();
      const wktSplit = settings.projectArea.split(';'),
            epsg = wktSplit[0].replace('SRID=','EPSG:'),
            wkt = wktSplit[1];

      const feature = format.readFeature(wkt);
      feature.getGeometry().transform(epsg, `EPSG:${this.srid}`);
      this.map?.map.getView().fit(feature.getGeometry().getExtent());
    })
  }

  selectFeatures(ids: number[], layerId: number | string, options?: { silent?: boolean, clear?: boolean } ): void {
    const layer = this.layerMap[layerId];
    this.map?.selectFeatures(this.mapId(layer), ids, options);
  }

  deselectAllFeatures(layerId: number | string): void {
    const layer = this.layerMap[layerId];
    this.map?.deselectAllFeatures(this.mapId(layer));
  }

  toggleEditMode(): void {
    this.editMode = !this.editMode;
  }

  saveCurrentExtent(name: string): void {
    this.mapExtents[name] = this.map?.view.calculateExtent();
  }

  loadExtent(name: string): void {
    const extent = this.mapExtents[name];
    if (!extent) return;
    this.map?.view.fit(extent);
  }

  removeExtent(name: string): void {
    delete this.mapExtents[name];
  }

  saveSettings(): void {
    let mapSettings: any = {};
    const layers = this.getLayers();
    layers.forEach(layer => {
      if (layer.id != undefined) {
        mapSettings[`layer-opacity-${layer.id}`] = layer.opacity;
        mapSettings[`layer-visibility-${layer.id}`] = layer.visible;
      }
    })
    mapSettings['background-layer'] = this.background?.id;
    mapSettings['legend-edit-mode'] = this.editMode;
    this.settings.user?.set(this.target, mapSettings, { patch: true });
    this.settings.user?.set('extents', this.mapExtents, { patch: true });
  }

  destroy(): void {
    this.saveSettings();
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }

}
