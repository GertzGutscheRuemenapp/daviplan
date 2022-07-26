import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'
import { forkJoin, Observable } from "rxjs";
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
import { MapLayerGroup, MapLayer, VectorTileLayer, WMSLayer, TileLayer, VectorLayer } from "./layers";

interface BackgroundLayerDef {
  id: string | number,
  name: string,
  url: string,
  description: string,
  attribution?: string,
  layerName?: string,
  type: 'tiles' | 'wms'
}

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
    type: 'wms',
    layerName: 'web'
  },
  {
    id: 'tpo-grey-back',
    name: 'TopPlusOpen grau',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Graustufendarstellung',
    type: 'wms',
    layerName: 'web_grau'
  }
]



@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};

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
            description: `Gebiete der Gebietseinheit ${level.name}`,
            style: level.symbol,
            labelField: '_label'
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
              mGroup.addLayer(mLayer);
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
  mapDescription = '';
  layerGroups: MapLayerGroup[] = [];
  private markerLayer?: VectorLayer;
  mapExtents: any = {};
  editMode: boolean = true;
  background?: TileLayer;
  mapSettings: any = {};
  backgroundLayers: TileLayer[] = [];
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
    this.settings.user?.get(this.target).subscribe(mapSettings => {
      this.mapSettings = mapSettings || {};
      const editMode = this.mapSettings['legend-edit-mode'];
      this.editMode = (editMode != undefined)? editMode : true;
      const backgroundId = this.mapSettings['background-layer'] || backgroundLayerDefs[1].id;
      backgroundLayerDefs.forEach(layerDef => {
        const opacity = parseFloat(this.mapSettings[`layer-opacity-${layerDef.id}`]) || 1;
        const LayerCls = (layerDef.type === 'wms')? WMSLayer: TileLayer;
        const bg = new LayerCls(layerDef.name, layerDef.url, {
          id: layerDef.id,
          description: layerDef.description,
          visible: layerDef.id === backgroundId,
          layerName: layerDef.layerName,
          opacity: opacity,
          attribution: layerDef.attribution
        });
        this.backgroundLayers.push(bg);
        bg.addToMap(this.map);
      });
      this.background = this.backgroundLayers.find(l => { return l.id === backgroundId });
      this.getServiceLayerGroups({ internal: true, external: true });
    })
    this.markerLayer = new VectorLayer('marker-layer', {
      order: 100
    });
    this.markerLayer.addToMap(this.map);
  }

  private getServiceLayerGroups(options?: { internal?: boolean, external?: boolean, reset?: boolean }): void {
    this.mapService.getLayers({ reset: options?.reset, external: options?.external, internal: options?.internal, active: true }).subscribe(layerGroups => {
      // ToDo: remember former checked layers on reset
      layerGroups.forEach(group => {
        if (!group.children) return;
        group.children.forEach(layer => {
          layer.opacity = parseFloat(this.mapSettings[`layer-opacity-${layer.id}`]) || 1;
          layer.visible = this.mapSettings[`layer-visibility-${layer.id}`];
          if (layer instanceof VectorTileLayer)
            layer.showLabel = this.mapSettings[`layer-label-${layer.id}`] || true;
        })
        this.addGroup(group);
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

  addLayer(layer: MapLayer): void {
    // if (layer.map) throw `Layer ${layer.name} already set to another map`;
    if (layer.map !== this.map) layer.map = this.map;
    if (!layer.group) {
      let group = this.layerGroups.find(group => group.name === 'Sonstiges');
      if (!group){
        group = new MapLayerGroup('Sonstiges', { order: 0 });
        this.addGroup(group);
      }
      group.addLayer(layer);
    }
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
    this.saveSettings();
    this.getLayers(options).forEach(l => l.removeFromMap());
    if (options?.internal) this.layerGroups = this.layerGroups.filter(g => g.external !== false);
    if (options?.external) this.layerGroups = this.layerGroups.filter(g => g.external !== true);
    this.getServiceLayerGroups({ reset: true, internal: options?.internal, external: options?.external });
  }

  /**
   * add a layer-group to this map only
   * sets unique id if id is undefined
   *
   * @param group
   * @param emit
   */
  addGroup(group: MapLayerGroup): void {
    if (group.id == undefined)
      group.id = uuid();
    if (!group.map) {
      group.map = this.map;
      group.children.forEach(layer => layer.addToMap(this.map));
    }
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
      this.map?.centerOnLayer(layer.mapId!);
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
    this.settings.user?.set('extents', this.mapExtents, { patch: true });
  }

  destroy(): void {
    this.saveSettings();
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }

}
