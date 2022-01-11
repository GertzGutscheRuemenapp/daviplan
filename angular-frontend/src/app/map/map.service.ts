import { Injectable, EventEmitter } from '@angular/core';
import { Layer, LayerGroup } from '../pages/basedata/external-layers/external-layers.component';
import { OlMap } from './map'
import { BehaviorSubject, Observable } from "rxjs";
import { User } from "../pages/login/users";
import { HttpClient } from "@angular/common/http";
import { mergeMap } from "rxjs/operators";
import { RestAPI } from "../rest-api";
import { sortBy } from "../helpers/utils";
import { subscribe } from "graphql";

interface LayerSettings {
  id: number;
  name: string;
  url: string;
  params?: any;
  xyz?: boolean;
}

const mockBackgroundLayers: LayerSettings[] = [
  {
    id: -1,
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    xyz: true
  },
  {
    id: -2,
    name: 'TopPlus',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    params: { layers: 'web' },
  },
]

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};
  backgroundLayers: LayerSettings[] = mockBackgroundLayers;
  layerGroups?: BehaviorSubject<Array<LayerGroup>>;

  constructor(private http: HttpClient, private rest: RestAPI) {}

  // ToDo: return Observable?
  get(target: string): MapControl {
    let control = this.controls[target];
    if(!control){
      control = new MapControl(target, this);
      control.destroyed.subscribe(target => delete this.controls[target]);
      control.create();
      this.controls[target] = control;
    }
    return control;
  }

  getLayers(): BehaviorSubject<Array<LayerGroup>>{
    if (!this.layerGroups) {
      this.layerGroups = new BehaviorSubject<LayerGroup[]>([]);
      this.fetchLayers();
    }
    return this.layerGroups;
  }

  fetchLayers() {
    this.http.get<LayerGroup[]>(this.rest.URLS.layerGroups).subscribe( groups => {
      groups = sortBy(groups, 'order');
      this.http.get<Layer[]>(this.rest.URLS.layers).subscribe(layers => {
        layers.forEach(layer => {
          layer.checked = false;
          const group = groups.find(group => { return group.id === layer.group });
          if (group) {
            if (!group.children) group.children = [];
            group.children.push(layer);
          }
        })
        // remove empty groups
        groups = groups.filter(group => { return !!group.children });
        this.layerGroups!.next(groups);
      })
    })
  }
}

export class MapControl {
  srid = 3857;
  target = '';
  destroyed = new EventEmitter<string>();
  map?: OlMap;
  mapDescription = '';
  private layers: Record<number, Layer> = [];

  constructor(target: string, private mapService: MapService) {
    this.target = target;
    this.mapService.backgroundLayers.forEach(layer => {
      this.layers[layer.id] = <Layer>layer;
    });
  }

  getBackgroundLayers(): Layer[] {
    // ToDo: replace with fetched ones or redefine background-layers
    let layers: Layer[] = this.mapService.backgroundLayers.map(layer => {
      return { id: layer.id, name: layer.name, order: 0,
        layerName:'', url: layer.url, group: 0, description:''} })
    return layers;
  }

  setBackground(id: number): void {
    this.mapService.backgroundLayers.forEach(layer => this.map?.setVisible(this.mapId(layer), layer.id === id));
  }

  private mapId(layer: LayerSettings | Layer): string {
    return `${layer.name}-${layer.id}`;
  }

  create(): void {
    this.map = new OlMap(this.target, {projection: `EPSG:${this.srid}`});
    for (let layer of this.mapService.backgroundLayers) {
      this.map.addTileServer({
        name: this.mapId(layer),
        url: layer.url,
        params: layer.params,
        visible: false,
        opacity: 1,
        xyz: layer.xyz
      });
    }
    this.mapService.getLayers().subscribe(layerGroups => {
      layerGroups.forEach(group => {
        for (let layer of group.children!) {
          this.map!.addTileServer({
            name: this.mapId(layer),
            url: layer.url,
            params: { layers: layer.layerName},
            visible: false,
            opacity: 1
          });
          this.layers[layer.id] = layer;
        }
      })
    })
  }

  setLayerAttr(id: number, options: {opacity?: number, visible?: boolean}): void {
    let layer = this.layers[id];
    if (!layer) return;
    if (options.opacity != undefined) this.map?.setOpacity(this.mapId(layer), options.opacity);
    if (options.visible != undefined) this.map?.setVisible(this.mapId(layer), options.visible);
  }

  toggleLayer(id: number, active: boolean): void {
    let layer = this.layers[id];
    if (!layer) return;
    this.map?.setVisible(this.mapId(layer), active);
  }

  destroy(): void {
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }
}
