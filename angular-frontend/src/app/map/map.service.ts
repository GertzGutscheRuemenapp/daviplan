import { Injectable, EventEmitter } from '@angular/core';
import { AreaLevel, Layer, LayerGroup } from '../rest-interfaces';
import { OlMap } from './map'
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../rest-api";
import { sortBy } from "../helpers/utils";
import { ProjectSettings } from "../pages/administration/project-definition/project-definition.component";
import { WKT } from "ol/format";
import { SettingsService } from "../settings.service";
import { environment } from "../../environments/environment";

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
  layerGroups?: BehaviorSubject<Array<LayerGroup>>;
  projectSettings?: ProjectSettings;

  constructor(private http: HttpClient, private rest: RestAPI, private settings: SettingsService) {
    this.http.get<ProjectSettings>(this.rest.URLS.projectSettings).subscribe(projectSettings => {
      this.projectSettings = projectSettings;
    })
  }

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
    if (!this.layerGroups) {
      this.layerGroups = new BehaviorSubject<LayerGroup[]>([]);
      this.fetchLayers({ internal: true, external: true });
    }
    return this.layerGroups;
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
      this.layerGroups!.next(flatGroups);
    })
  }

  private fetchInternalLayers(): Observable<LayerGroup[]> {
    const observable = new Observable<LayerGroup[]>(subscriber => {
      this.http.get<AreaLevel[]>(`${this.rest.URLS.arealevels}?active=true`).subscribe(levels => {
        levels = sortBy(levels, 'order');
        let groups = [];
        const group: LayerGroup = { id: -1, name: 'Gebiete', order: 2 };
        let i = -100;
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
          const layer: Layer = {
            id: i,
            type: "vector-tiles",
            order: i,
            url: tileUrl,
            name: level.name,
            description: `Gebiete der Gebietseinheit ${level.name}`,
            symbol: level.symbol
          }
          i -= 1;
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
            layer.checked = false;
            const group = groups.find(group => { return group.id === layer.group });
            if (group) {
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
  private layerMap: Record<number, Layer> = [];

  constructor(target: string, private mapService: MapService, private settings: SettingsService) {
    this.target = target;
  }

  refresh(options: { internal?: boolean, external?: boolean } = {}): void {
    this.mapService.fetchLayers(options);
  }

  getBackgroundLayers(): Layer[] {
    return this.mapService.backgroundLayers;
  }

  addLayer(layer: Layer, visible: boolean = true) {
    if (layer.type === 'vector-tiles') {
       this.map!.addVectorTileLayer(this.mapId(layer), layer.url,{
         visible: false,
         opacity: 1,
         stroke: { color: layer.symbol?.strokeColor, width: 2 },
         fill: { color: layer.symbol?.fillColor }
       });
    }
    else {
      const mapLayer = this.map!.addTileServer(
        this.mapId(layer),  layer.url, {
          params: { layers: layer.layerName },
          visible: false,
          opacity: 1,
          xyz: layer.type == 'tiles',
          attribution: layer.attribution
        });
      if (layer.type === 'wms' && !layer.legendUrl) {
          let url = mapLayer.getSource().getLegendUrl(1, { layer: layer.layerName });
          if (url) url += '&SLD_VERSION=1.1.0';
          layer.legendUrl = url;
        }
    }
    this.layerMap[layer.id] = layer;
  }

  setBackground(id: number | undefined): void {
    this.mapService.backgroundLayers.forEach(layer => this.map?.setVisible(
      this.mapId(layer), layer.id === id));
  }

  private mapId(layer: Layer): string {
    return `${layer.name}-${layer.id}`;
  }

  init(): void {
    this.map = new OlMap(this.target, {projection: `EPSG:${this.srid}`});
    for (let layer of this.mapService.backgroundLayers) {
      this.addLayer(layer, true);
    }
    this.mapService.getLayers().subscribe(layerGroups => {
      layerGroups.forEach(group => {
        if (!group.children) return;
        for (let layer of group.children!.slice().reverse()) {
          this.addLayer(layer, false);
        }
      })
    })
  }

  setLayerAttr(id: number, options: { opacity?: number, visible?: boolean }): void {
    let layer = this.layerMap[id];
    if (!layer) return;
    if (options.opacity != undefined) this.map?.setOpacity(this.mapId(layer), options.opacity);
    if (options.visible != undefined) this.map?.setVisible(this.mapId(layer), options.visible);
  }

  toggleLayer(id: number, active: boolean): void {
    let layer = this.layerMap[id];
    if (!layer) return;
    this.map?.setVisible(this.mapId(layer), active);
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

  destroy(): void {
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }

}
