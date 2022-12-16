import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { sortBy } from "../helpers/utils";
import { WKT } from "ol/format";
import { SettingsService } from "../settings.service";
import { environment } from "../../environments/environment";
import { v4 as uuid } from 'uuid';
import { Feature } from 'ol';
import { Geometry, Polygon, Point } from "ol/geom";
import { getCenter } from 'ol/extent';
import { Icon, Style } from "ol/style";
import { RestCacheService } from "../rest-cache.service";
import {
  MapLayer,
  VectorTileLayer,
  WMSLayer,
  TileLayer,
  VectorLayer,
  VectorLayerOptions, ServiceLayerOptions, LayerOptions, VectorTileLayerOptions
} from "./layers";
import { CookieService } from "../helpers/cookies.service";

interface MapLayerGroupOptions {
  order?: number,
  external?: boolean,
  id?: number
}

export class MapLayerGroup {
  name: string;
  mapControl?: MapControl;
  id?: number | string;
  children: MapLayer[] = [];
  external?: boolean;
  map?: OlMap;
  order?: number;

  constructor(name: string, options?: {
    order?: number,
    external?: boolean,
    mapControl?: MapControl,
    id?: number
  }) {
    this.id = options?.id;
    this.mapControl = options?.mapControl;
    if (this.id === undefined)
      this.id = uuid();
    this.name = name;
    this.external = options?.external;
    this.order = options?.order;
  }

  appendLayer(layer: MapLayer | undefined){
    if (layer) this.children.push(layer);
  }

  addVectorLayer(name: string, options: VectorLayerOptions): VectorLayer | undefined {
    if (!this.mapControl) return;
    const layer = this.mapControl?.addVectorLayer(name, options);
    this.appendLayer(layer);
    return layer;
  }
  addVectorTileLayer(name: string, url: string, options: VectorTileLayerOptions): VectorTileLayer | undefined  {
    if (!this.mapControl) return;
    const layer = this.mapControl.addVectorTileLayer(name, url, options);
    this.appendLayer(layer);
    return layer;
  };
  addServiceLayer(name: string, url: string, type: 'tile' | 'wms', options: ServiceLayerOptions): WMSLayer | TileLayer | undefined {
    if (!this.mapControl) return;
    const layer = this.mapControl.addServiceLayer(name, url, type, options);
    this.appendLayer(layer);
    return layer;
  }

  removeLayer(layer: MapLayer): void {
    const idx = this.children.indexOf(layer);
    if (idx < 0) return;
    this.children.splice(idx, 1);
    layer.removeFromMap();
  }

  clear(): void {
    this.children.forEach(l => l.removeFromMap());
    this.children = [];
  }
}

interface BackgroundLayerDef {
  id: string | number,
  name: string,
  url: string,
  description: string,
  attribution?: string,
  layerName?: string,
  type: 'tiles' | 'wms'
}

const currentYear = new Date().getFullYear();
const backgroundLayerDefs: BackgroundLayerDef[] = [
  {
    id: 'osm-back',
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    description: 'Offizielle Weltkarte von OpenStreetMap',
    attribution: '©<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende<a>',
    type: 'tiles',
  },
  {
    id: 'tpo-back',
    name: 'TopPlusOpen',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Normalausgabe',
    attribution: `©<a target="_blank" href="https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/Datenquellen_TopPlusOpen.html">Bundesamt für Kartographie und Geodäsie (${currentYear})<a>`,
    type: 'wms',
    layerName: 'web'
  },
  {
    id: 'tpo-grey-back',
    name: 'TopPlusOpen grau',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Graustufendarstellung',
    attribution: '©<a target="_blank" href="https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/Datenquellen_TopPlusOpen.html">Bundesamt für Kartographie und Geodäsie (${currentYear})<a>',
    type: 'wms',
    layerName: 'web_grau'
  }
]

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};

  constructor(private http: HttpClient, private restService: RestCacheService, private settings: SettingsService,
              private cookies: CookieService) { }

  get(target: string): MapControl {
    let control = this.controls[target];
    if(!control){
      control = new MapControl(target, this, this.settings, this.cookies);
      control.destroyed.subscribe(target => delete this.controls[target]);
      control.init();
      this.controls[target] = control;
    }
    return control;
  }

  getLayers( options?: { internal?: boolean, external?: boolean, reset?: boolean, active?: boolean } ): Observable<MapLayerGroup[]>{
    const observable = new Observable<MapLayerGroup[]>(subscriber => {
      const observables: Observable<MapLayerGroup[]>[] = [];
      if (options?.internal)
        observables.push(this.fetchInternalLayers(options?.reset));
      if (options?.external)
        observables.push(this.fetchExternalLayers({ reset: options?.reset, active: options?.active }));
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
        const group = new MapLayerGroup('Gebiete', { order: 2, external: false });
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
          const mLayer = new VectorTileLayer(level.name, tileUrl, {
            id: `area-layer-level-${level.id}`,
            description: `Gebiete der Gebietseinteilung ${level.name}`,
            style: level.symbol,
            labelField: '_label',
            zIndex: 20000
          })
          layers.push(mLayer);
        });
        if (layers) {
          layers.forEach(mlayer => group.appendLayer(mlayer));
          groups.push(group);
        }
        subscriber.next(groups);
        subscriber.complete();
      })
    })
    return observable;
  }

  fetchExternalLayers(options?: { reset?: boolean, active?: boolean }): Observable<MapLayerGroup[]> {
    const observable = new Observable<MapLayerGroup[]>(subscriber => {
      this.restService.getLayerGroups({ reset: options?.reset }).subscribe(groups => {
        groups = sortBy(groups, 'order');
        const mGroups: MapLayerGroup[] = groups.map(group =>
          new MapLayerGroup(group.name, { id: group.id, external: group.external, order: group.order }));
        let layerOptions: any = { reset: options?.reset };
        if (options?.active !== undefined)
          layerOptions.active = options?.active;
        this.restService.getLayers(layerOptions).subscribe(layers => {
          layers = sortBy(layers, 'order');
          layers.forEach(layer => {
            const mGroup = mGroups.find(mGroup => { return mGroup.id === layer.group });
            if (mGroup) {
              const mLayer = new WMSLayer(layer.name, layer.url!,{
                id: layer.id,
                layerName: layer.layerName,
                description: layer.description,
                order: layer.order,
                active: layer.active
              })
              mGroup.appendLayer(mLayer);
            }
          })
          subscriber.next(mGroups.filter(g => g.children.length > 0));
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
  mapDescription$ = new BehaviorSubject<string>('');
  layerGroups: MapLayerGroup[] = [];
  private markerLayer?: VectorLayer;
  mapExtents: Record<string, any> = {};
  editMode: boolean = true;
  background?: TileLayer;
  mapSettings: any = {};
  backgroundLayers: TileLayer[] = [];
  markerImg = `${environment.backend}/static/img/map-marker-blue.svg`;
  markerCursorImg = `${environment.backend}/static/img/map-marker-cursor.png`;
  searchCursorImg = `${environment.backend}/static/img/location-searching.png`;


  constructor(target: string, private mapService: MapService, private settings: SettingsService, private cookies: CookieService) {
    this.target = target;
    // call destroy on page reload
    window.onbeforeunload = () => this.destroy();
    this.settings.user?.get('extents').subscribe(extents => {
      this.mapExtents = extents || {};
    })
  }

  init(): void {
    this.map = new OlMap(this.target, { projection: `EPSG:${this.srid}` });
    this.settings.user?.get(this.target).subscribe(mapSettings => {
      this.mapSettings = mapSettings || {};
      const editMode = this.mapSettings['legend-edit-mode'];
      this.editMode = (editMode != undefined)? editMode : true;
      const backgroundId = this.mapSettings['background-layer'] || backgroundLayerDefs[1].id;
      backgroundLayerDefs.forEach(layerDef => {
        const LayerCls = (layerDef.type === 'wms')? WMSLayer: TileLayer;
        const bg = new LayerCls(layerDef.name, layerDef.url, {
          id: layerDef.id,
          description: layerDef.description,
          visible: layerDef.id === backgroundId,
          layerName: layerDef.layerName,
          opacity: this.getCookieLayerAttr(layerDef.id, 'opacity'),
          attribution: layerDef.attribution
        });
        this.backgroundLayers.push(bg);
        bg.addToMap(this.map);
        bg.attributeChanged.subscribe(c => this.setCookieLayerAttr(layerDef.id, c.attribute, c.value));
      });
      this.background = this.backgroundLayers.find(l => { return l.id === backgroundId });
      this.getServiceLayerGroups({ internal: true, external: true });
    })
    this.markerLayer = new VectorLayer('marker-layer', {
      zIndex: 100000
    });
    this.markerLayer.addToMap(this.map);
  }

  addVectorLayer(name: string, options: VectorLayerOptions): VectorLayer | undefined {
    return this._addLayer(name, 'vector', options) as VectorLayer;
  };
  addVectorTileLayer(name: string, url: string, options: VectorTileLayerOptions): VectorTileLayer | undefined  {
    return this._addLayer(name, 'vector-tile', options, url) as VectorTileLayer;
  };
  addServiceLayer(name: string, url: string, type: 'tile' | 'wms', options: ServiceLayerOptions): WMSLayer | TileLayer | undefined {
    const layer = this._addLayer(name, type, options, url);
    if (type === 'tile')
      return layer as TileLayer;
    return layer as WMSLayer;
  }

  private addCookieOptions(layerId: string | number, options: LayerOptions): LayerOptions {
    const clonedOpt = Object.assign({}, options);
    const defaults = [1, true, true];
    const types: ('number' | 'boolean')[] = ['number', 'boolean', 'boolean', 'boolean'];
    ['opacity', 'visible', 'showLabel', 'legendElapsed'].forEach((attr, i) => {
      const key = attr as keyof LayerOptions;
      if (clonedOpt[key] === undefined){
        clonedOpt[key] = this.getCookieLayerAttr(layerId, attr, {default: defaults[i], type: types[i]});
      }
    })
    return clonedOpt;
  }

  private _addLayer(name: string, type: 'wms' | 'tile' | 'vector-tile' | 'vector', options: LayerOptions, url?: string): MapLayer | undefined {
    // restore attributes from cookies by id if it is given in layer options or by name
    options = this.addCookieOptions(options?.id || name, options);
    let layer;
    switch (type) {
      case 'wms':
        if (!url) return;
        layer = new WMSLayer(name, url, options);
        break;
      case 'tile':
        if (!url) return;
        layer = new TileLayer(name, url, options);
        break;
      case 'vector-tile':
        if (!url) return;
        layer = new VectorTileLayer(name, url, options);
        break;
      default:
        layer = new VectorLayer(name, options);
    }
    layer.attributeChanged.subscribe(c => this.setCookieLayerAttr(options?.id || name, c.attribute, c.value));
    layer.addToMap(this.map);
    return layer;
  }

  private createTileLayer(name: string, url: string, options: ServiceLayerOptions): TileLayer {
    options = this.addCookieOptions(name, options);
    const layer = new TileLayer(name, url, options);
    return layer;
  }


  /**
   * store attribute changes of layer in cookies by identifier (name or actual id)
   *
   * @private
   */
  private setCookieLayerAttr(layerId: string | number, attribute: string, value: any) {
    this.cookies.set(`Layer-${layerId}-${attribute}`, value);
  }

  /**
   * get value of layer attribute from cookies, if not in cookies yet defaults to a default value
   *
   * @param layerId
   * @param attribute name of layer attribute
   * @param options type defaults to 'number', default defaults to 1
   * @private
   */
  private getCookieLayerAttr(layerId: string | number, attribute: string, options?: { type?: 'number' | 'boolean', default?: any } ): any {
    const cookieStr = `Layer-${layerId}-${attribute}`;
    // can't pass type to cookies.get directly, TS2769 error
    const value = (options?.type === 'boolean')? this.cookies.get(cookieStr, 'boolean'): this.cookies.get(cookieStr, 'number');
    const defaultVal = (options?.default !== undefined)? options.default: (options?.type === 'boolean')? false: 1;
    return (value !== undefined)? value: defaultVal;
  }

  private getServiceLayerGroups(options?: { internal?: boolean, external?: boolean, reset?: boolean }): void {
    this.mapService.getLayers({ reset: options?.reset, external: options?.external, internal: options?.internal, active: true }).subscribe(layerGroups => {
      // ToDo: remember former checked layers on reset
      layerGroups.forEach(group => {
        if (!group.children) return;
        // clone group because it will be altered when appending
        group = Object.assign({}, group);
        group.children.forEach(layer => {
          layer.setOpacity(this.getCookieLayerAttr(layer.id!, 'opacity'));
          layer.setVisible(this.getCookieLayerAttr(layer.id!, 'visible', { type: 'boolean' }));
          if (layer instanceof VectorTileLayer)
            layer.setShowLabel(this.getCookieLayerAttr(layer.id!, 'showLabel', { type: 'boolean' }));
          layer.attributeChanged.subscribe(c => this.setCookieLayerAttr(layer.id!, c.attribute, c.value));
        })
        this._appendGroup(group);
      })
    })
  }

  getLayers(options?: { internal?: boolean, external?: boolean }): MapLayer[] {
    let layers: MapLayer[] = [];
    let groups = this.layerGroups;
    if (options?.internal || options?.external) groups = groups.filter(g => (options?.external && g.external === true) || (options?.internal && g.external === false));
    groups.forEach(g => layers = layers.concat(g.children));
    // if (this.background) layers.push(this.background);
    return layers;
  }

  getLayer(id: number | string): MapLayer | undefined {
    // ToDo: background as well?
    return this.getLayers().find(l => l.id === id);
  }

  getGroup(id: number | string): MapLayerGroup | undefined {
    // ToDo: background as well?
    return this.layerGroups.find(g => g.id === id);
  }

  addMarker(geometry: Geometry): Feature<any> {
    // this.removeMarker();
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
    this.markerLayer?.addFeatures( [marker]);
    return marker;
  }

  removeMarker(): void {
    this.markerLayer?.clearFeatures();
  }

  refresh(options?: { internal?: boolean, external?: boolean }): void {
    if (options?.internal === false && !options?.external === false) return;
    this.saveMapSettings();
    this.getLayers(options).forEach(l => l.removeFromMap());
    if (options?.internal) this.layerGroups = sortBy(this.layerGroups.filter(g => g.external !== false), 'order');
    if (options?.external) this.layerGroups = sortBy(this.layerGroups.filter(g => g.external !== true), 'order');
    this.getServiceLayerGroups({ reset: true, internal: options?.internal, external: options?.external });
  }

  addGroup(name: string, options: MapLayerGroupOptions): MapLayerGroup {
    const group = new MapLayerGroup(name, options);
    group.mapControl = this;
    this.layerGroups.push(group);
    this.layerGroups = sortBy(this.layerGroups, 'order');
    return group;
  }

  /**
   * add a layer-group to this map only
   * sets unique id if id is undefined
   *
   * @param group
   * @param emit
   */
  private _appendGroup(group: MapLayerGroup): void {
    if (group.id == undefined)
      group.id = uuid();
    if (!group.map) {
      group.map = this.map;
      group.children.forEach(layer => layer.addToMap(this.map));
    }
    group.mapControl = this;
    this.layerGroups.push(group);
    this.layerGroups = sortBy(this.layerGroups, 'order');
  }

  /**
   * remove a layer-group and its children, can only remove groups added specifically to this map
   * (not the global ones)
   *
   * @param id
   * @param emit
   */
  removeGroup(group: MapLayerGroup): void {
    const idx = this.layerGroups.findIndex(g => g === group);
    if (idx < 0) return;
    group.clear();
    this.layerGroups.splice(idx, 1);
  }

  setBackground(id: number | string): void {
    this.background = this.backgroundLayers.find(l => l.id === id);
    this.backgroundLayers.forEach(l => l.setVisible(l.id === id));
  }

  zoomTo(layer: MapLayer): void {
    if (!layer.mapId) return;
    const mapLayer = this.map?.getLayer(layer.mapId),
          _this = this;
    mapLayer!.getSource().once('featuresloadend', (evt: any) => {
      this.map?.zoomToExtent(layer.mapId!);
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

  toggleEditMode(): void {
    this.editMode = !this.editMode;
  }

  saveCurrentExtent(name: string): void {
    this.mapExtents[name] = this.map?.view.calculateExtent();
    this.settings.user?.set('extents', this.mapExtents, { patch: true });
  }

  loadExtent(name: string): void {
    const extent = this.mapExtents[name];
    if (!extent) return;
    this.map?.view.fit(extent);
  }

  removeExtent(name: string): void {
    delete this.mapExtents[name];
    this.settings.user?.set('extents', this.mapExtents, { patch: true });
  }

  saveMapSettings(): void {
    const layers = this.getLayers();
    layers.forEach(layer => {
      if (layer.id != undefined) {
        this.mapSettings[`layer-opacity-${layer.id}`] = layer.opacity;
        this.mapSettings[`layer-visibility-${layer.id}`] = layer.visible;
        if (layer instanceof VectorTileLayer)
          this.mapSettings[`layer-label-${layer.id}`] = layer.showLabel;
      }
    });
    this.backgroundLayers.forEach(layer => {
      this.mapSettings[`layer-opacity-${layer.id}`] = layer.opacity;
    })
    this.mapSettings['background-layer'] = this.background?.id;
    this.mapSettings['legend-edit-mode'] = this.editMode;
    this.settings.user?.set(this.target, this.mapSettings, { patch: true });
  }

  setDescription(text: string): void {
    this.mapDescription$.next(text);

  }

  setCursor(cursor?: 'crosshair' | 'pointer' | 'marker' | 'search' | 'auto' | 'default' ): void {
    let cur: string = cursor || '';
    if (cursor === 'marker')
      cur = `url(${this.markerCursorImg}) 10 30, pointer`;
    if (cursor === 'search')
      cur = `url(${this.searchCursorImg}) 15 15, pointer`;
    this.map?.setCursor(cur);
  }

  destroy(): void {
    this.saveMapSettings();
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }

}
