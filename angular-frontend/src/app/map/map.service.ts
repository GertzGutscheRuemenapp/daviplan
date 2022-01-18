import { Injectable, EventEmitter } from '@angular/core';
import { Layer, LayerGroup } from '../pages/basedata/external-layers/external-layers.component';
import { OlMap } from './map'
import { BehaviorSubject } from "rxjs";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../rest-api";
import { sortBy } from "../helpers/utils";
import { environment } from "../../environments/environment";

interface BackgroundLayer {
  id: number;
  name: string;
  url: string;
  legendUrl?: string;
  description?: string;
  attribution?: string;
  params?: any;
  xyz?: boolean;
}

const backgroundLayers: BackgroundLayer[] = [
  {
    id: -1,
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    description: 'Offizielle Weltkarte von OpenStreetMap',
    attribution: '©<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende<a>',
    xyz: true
  },
  {
    id: -2,
    name: 'TopPlusOpen',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    description: 'Weltweite einheitliche Webkarte vom BKG. Normalausgabe',
    legendUrl: 'https://sgx.geodatenzentrum.de/wms_topplus_open?styles=&sld_version=1.1.0&version=1.1.1&request=GetLegendGraphic&format=image%2Fpng&service=WMS&layer=web',
    params: { layers: 'web' },
  },
  {
    id: -3,
    name: 'TopPlusOpen grau',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    legendUrl: 'https://sgx.geodatenzentrum.de/wms_topplus_open?styles=&sld_version=1.1.0&version=1.1.1&request=GetLegendGraphic&format=image%2Fpng&service=WMS&layer=web_grau',
    description: 'Weltweite einheitliche Webkarte vom BKG. Graustufendarstellung',
    params: { layers: 'web_grau' },
  }
]

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private controls: Record<string, MapControl> = {};
  backgroundLayers: BackgroundLayer[] = backgroundLayers;
  layerGroups?: BehaviorSubject<Array<LayerGroup>>;

  constructor(private http: HttpClient, private rest: RestAPI) {

  }

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
      this.http.get<Layer[]>(`${this.rest.URLS.layers}?active=true`).subscribe(layers => {
        layers = sortBy(layers, 'order');
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
    let layers: Layer[] = this.mapService.backgroundLayers.map(layer => {
      return { id: layer.id, name: layer.name, order: 0, description: layer.description || '', legendUrl: layer.legendUrl || '',
        // ToDo: ugly, info not needed
        layerName:'', url: layer.url, group: 0} })
    return layers;
  }

  setBackground(id: number): void {
    this.mapService.backgroundLayers.forEach(layer => this.map?.setVisible(this.mapId(layer), layer.id === id));
  }

  private mapId(layer: BackgroundLayer | Layer): string {
    return `${layer.name}-${layer.id}`;
  }

  create(): void {
    this.map = new OlMap(this.target, {projection: `EPSG:${this.srid}`});
    for (let layer of this.mapService.backgroundLayers) {
      const mapLayer = this.map.addTileServer({
        name: this.mapId(layer),
        url: layer.url,
        params: layer.params,
        visible: false,
        opacity: 1,
        xyz: layer.xyz,
        attribution: layer.attribution
      });
    }
    const testLayer = this.map.addTileServer({
      name: 'test',
      url: `${environment.backend}/arealevels/1/tile/{z}/{x}/{y}`,
      visible: true,
      opacity: 1,
      xyz: true,
    });
    this.mapService.getLayers().subscribe(layerGroups => {
      layerGroups.forEach(group => {
        for (let layer of group.children!.slice().reverse()) {
          const mapLayer = this.map!.addTileServer({
            name: this.mapId(layer),
            url: layer.url,
            params: { layers: layer.layerName},
            visible: false,
            opacity: 1
          });
          if (!layer.legendUrl) {
            let url = mapLayer.getSource().getLegendUrl(1, { layer: layer.layerName });
            if (url) url += '&SLD_VERSION=1.1.0';
            layer.legendUrl = url;
          }
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
