import { Injectable, EventEmitter } from '@angular/core';
import { AreaLevel, Layer, LayerGroup } from '../rest-interfaces';
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

const backgroundLayers: Layer[] = [
  {
    id: -1,
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    description: 'Offizielle Weltkarte von OpenStreetMap',
    attribution: '©<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende<a>',
    type: 'tiles',
    order: 1,

  },
  {
    id: -2,
    name: 'TopPlusOpen',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Normalausgabe',
    type: 'wms',
    order: 2,
    layerName: 'web'
  },
  {
    id: -3,
    name: 'TopPlusOpen grau',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Graustufendarstellung',
    type: 'wms',
    order: 3,
    layerName: 'web_grau'
  }
]

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};
  backgroundLayers: Layer[] = backgroundLayers;
  layerGroups$?: BehaviorSubject<Array<LayerGroup>>;

  constructor(private http: HttpClient, private rest: RestAPI, private settings: SettingsService) { }

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

  getLayers(): BehaviorSubject<Array<LayerGroup>>{
    if (!this.layerGroups$) {
      this.layerGroups$ = new BehaviorSubject<LayerGroup[]>([]);
      this.fetchLayers({ internal: true, external: true });
    }
    return this.layerGroups$;
  }

  fetchLayers( options: { internal?: boolean, external?: boolean } = {}): void {
    const observables: Observable<LayerGroup[]>[] = [];
    if (options.internal)
      observables.push(this.fetchInternalLayers());
    if (options.external)
      observables.push(this.fetchExternalLayers());
    forkJoin(...observables).subscribe((merged: Array<LayerGroup[]>) => {
      // @ts-ignore
      const flatGroups = [].concat.apply([], merged);
      this.layerGroups$!.next(flatGroups);
    })
  }

  private fetchInternalLayers(): Observable<LayerGroup[]> {
    const observable = new Observable<LayerGroup[]>(subscriber => {
      this.http.get<AreaLevel[]>(`${this.rest.URLS.arealevels}?active=true`).subscribe(levels => {
        levels = sortBy(levels, 'order');//.reverse();
        let groups = [];
        const group: LayerGroup = { id: -1, name: 'Gebiete', order: 2 };
        let layers: Layer[] = [];
        levels.forEach(level => {
          // skip levels with no symbol (aka should not be displayed)
          if (!level.symbol) return;
          // areas have no fill
          level.symbol.fillColor = '';
          let tileUrl = level.tileUrl!;
          // "force" https in production, backend returns http (running in container)
          if (environment.production) {
            tileUrl = tileUrl.replace('http:', 'https:');
          }
          const id = -100 - level.id;
          const layer: Layer = {
            id: id,
            type: "vector-tiles",
            order: level.order,
            url: tileUrl,
            name: level.name,
            description: `Gebiete der Gebietseinheit ${level.name}`,
            symbol: level.symbol,
            labelField: level.labelField
          }
          layers.push(layer);
        });
        if (layers) {
          group.children = layers;
          groups.push(group);
        }
        subscriber.next(groups);
        subscriber.complete();
      })
    })
    return observable;
  }

  private fetchExternalLayers(): Observable<LayerGroup[]> {
    const observable = new Observable<LayerGroup[]>(subscriber => {
      this.http.get<LayerGroup[]>(this.rest.URLS.layerGroups).subscribe( groups => {
        groups = sortBy(groups, 'order');
        this.http.get<Layer[]>(`${this.rest.URLS.layers}?active=true`).subscribe( layers => {
          layers = sortBy(layers, 'order');
          layers.forEach(layer => {
            const group = groups.find(group => { return group.id === layer.group });
            if (group) {
              layer.type = 'wms';
              if (!group.children) group.children = [];
              group.children.push(layer);
            }
          })
          subscriber.next(groups);
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
  layerGroups: BehaviorSubject<Array<LayerGroup>> = new BehaviorSubject<Array<LayerGroup>>([]);
  private layerMap: Record<string | number, Layer> = {};
  private olLayerIds: Record<string, string | number> = {};
  private _localLayerGroups: LayerGroup[] = [];
  private _serviceLayerGroups: LayerGroup[] = [];
  private checklistSelection = new SelectionModel<Layer>(true );
  mapSettings: any = {};
  mapExtents: any = {};
  editMode: boolean = true;
  background?: Layer;
  backgroundOpacity = 1;

  isSelected = (layer: Layer) => this.checklistSelection.isSelected(layer);

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
      this.mapSettings = mapSettings;
      const editMode = mapSettings['legend-edit-mode'];
      this.editMode = (editMode != undefined)? editMode : true;
      const backgroundId = parseInt(mapSettings[`background-layer`]);
      this.background = (backgroundId)? this.mapService.backgroundLayers.find(
        l => { return l.id === backgroundId }) : this.mapService.backgroundLayers[1];
      if (this.background)
        this.backgroundOpacity = this.mapSettings[`layer-opacity-${this.background.id}`] || 1;
      for (let layer of this.mapService.backgroundLayers) {
        layer.opacity = parseFloat(this.mapSettings[`layer-opacity-${layer.id}`]) || 1;
        this._addLayerToMap(layer, {
          visible: layer === this.background
        });
      }
    })
    this.mapService.getLayers().subscribe(layerGroups => {
      this.checklistSelection.clear();
      this._serviceLayerGroups = layerGroups;
      layerGroups.forEach(group => {
        if (!group.children) return;
        for (let layer of group.children!.slice().reverse()) {
          let visible = false;
          if (Boolean(this.mapSettings[`layer-checked-${layer.id}`])) {
            this.checklistSelection.select(layer);
            visible = true;
          }
          layer.opacity = parseFloat(this.mapSettings[`layer-opacity-${layer.id}`]) || 1;
          this._addLayerToMap(layer, { visible: visible });
        }
      })
      this.layerGroups.next(this._serviceLayerGroups);
    })
  }

  getBackgroundLayers(): Layer[]{
    return this.mapService.backgroundLayers;
  }

  clear(clearForegroundOnly= false) {
    Object.values(this.layerMap).forEach(layer => {
      if (clearForegroundOnly && this.mapService.backgroundLayers.indexOf(layer) >= 0)
        return;
      this.map?.removeLayer(this.mapId(layer));
    })
  }

  refresh(options: { internal?: boolean, external?: boolean } = {}): void {
    this.clear(true);
    this.mapService.fetchLayers(options);
  }

  /**
   * add a layer-group to this map only
   * sets unique id if id is undefined
   *
   * @param group
   * @param emit
   */
  addGroup(group: LayerGroup, emit= true): LayerGroup {
    if (group.id == undefined)
      group.id = uuid();
    this._localLayerGroups.push(group);
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
    return group;
  }

  /**
   * remove a layer-group and its children, can only remove groups added specifically to this map
   * (not the global ones)
   *
   * @param id
   * @param emit
   */
  removeGroup(id: number | string, emit= true): void {
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

  setShowLabel(id: number | string, show: boolean): void {
    const layer = this.layerMap[id];
    this.map?.setShowLabel(this.mapId(layer), show);
  }

  removeLayer(id: number | string, emit= true): void {
    const layer = this.layerMap[id];
    const layerGroups = this._localLayerGroups.concat(this._serviceLayerGroups);
    const group = layerGroups.find(group => layer.group === group.id)!;
    const idx = group.children!.indexOf(layer);
    this._removeLayerFromMap(layer);
    if (idx >= 0)
      group.children!.splice(idx, 1);
    delete this.layerMap[id];
    if (emit) this.layerGroups.next(this._localLayerGroups.concat(this._serviceLayerGroups));
  }

  private _removeLayerFromMap(layer: Layer){
    this.map?.removeLayer(this.mapId(layer));
  }

  private onFeatureSelected(ollayer: OlLayer<any>, selected: Feature<any>[]): void {
    const layer = this.layerMap[this.olLayerIds[ollayer.get('name')]];
    if (layer && layer.featureSelected)
      selected.forEach(feature => layer.featureSelected!.emit({ feature: feature, selected: true }));
  }

  private onFeatureDeselected(ollayer: OlLayer<any>, deselected: Feature<any>[]): void {
    const layer = this.layerMap[this.olLayerIds[ollayer.get('name')]];
    if (layer.featureSelected)
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
  addLayer(layer: Layer, options?: {
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
    select?: {
      multi?: boolean,
      fillColor?: string,
      strokeColor?: string
    }
  }, emit= true): Layer {
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
      select: options?.select
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
  }

  private _addLayerToMap(layer: Layer, options?: {
    visible?: boolean,
    tooltipField?: string,
    colorFunc?: ((d: number) => string),
    radiusFunc?: ((d: number) => number),
    valueField?: string,
    mouseOver?: {
      fillColor?: string,
      strokeColor?: string
      cursor?: string
    },
    select?: {
      multi?: boolean,
      fillColor?: string,
      strokeColor?: string
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
          color: layer.symbol?.strokeColor, width: 2,
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
        selectable: true,
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

  addFeatures(layerId: number | string, features: any[],
              options?: { properties?: string, geometry?: string, zIndex?: string }): void {
    const layer = this.layerMap[layerId];
    if (!layer) return;
    let olFeatures: Feature<any>[] = [];
    const properties = (options?.properties !== undefined)? options?.properties: 'properties';
    const geometry = (options?.properties !== undefined)? options?.geometry: 'geometry';
    features.forEach( feature => {
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
    this.map?.addFeatures(this.mapId(layer), olFeatures);
  }

  clearFeatures(id: number | string): void {
    const layer = this.layerMap[id];
    this.map?.clear(this.mapId(layer));
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

  private mapId(layer: Layer): string {
    return `${layer.name}-${layer.id}`;
  }

  setLayerAttr(id: number | string | undefined, options: { opacity?: number, visible?: boolean }): void {
    if (id === undefined) return;
    const layer = this.layerMap[id];
    if (!layer) return;
    if (options.opacity != undefined) {
      this.map?.setOpacity(this.mapId(layer), options.opacity);
      this.mapSettings[`layer-opacity-${layer.id}`] = options.opacity;
    };
    if (options.visible != undefined) this.map?.setVisible(this.mapId(layer), options.visible);
  }

  toggleLayer(id: number | string | undefined): void {
    if (id === undefined) return;
    const layer = this.layerMap[id];
    if (!layer) return;
    this.checklistSelection.toggle(layer);
    const isSelected = this.checklistSelection.isSelected(layer);
    this.mapSettings[`layer-checked-${layer.id}`] = isSelected;
    this.map?.setVisible(this.mapId(layer), isSelected);
  }

  zoomTo(layer: Layer): void {
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
    this.mapSettings['legend-edit-mode'] = this.editMode;
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
    if (this.mapSettings)
      this.settings.user?.set(this.target, this.mapSettings, { patch: true });
    this.settings.user?.set('extents', this.mapExtents, { patch: true });
  }

  destroy(): void {
    this.saveSettings();
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }

}
