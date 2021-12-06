import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'

interface LayerSettings {
  id: number;
  name: string;
  url: string;
  params?: any;
  xyz?: boolean;
}

export interface Layer {
  id: number;
  name: string;
  color?: string;
  opacity?: number;
  checked?: boolean;
}

const mockBackgroundLayers: LayerSettings[] = [
  {
    id: 1,
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    xyz: true
  },
  {
    id: 2,
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

  constructor() { }

  // ToDo: return Observable?
  get(target: string): MapControl {
    let control = this.controls[target];
    if(!control){
      control = new MapControl(this.backgroundLayers, target);
      control.destroyed.subscribe(target => delete this.controls[target]);
      control.create();
      this.controls[target] = control;
    }
    return control;
  }
}

export class MapControl {
  target = '';
  destroyed = new EventEmitter<string>();
  map?: OlMap;
  mapDescription = '';
  private layers: Record<number, LayerSettings> = [];
  private readonly backgroundLayers: LayerSettings[] = [];
  private backgroundOpacity: number = 1;

  constructor(backgroundLayers: LayerSettings[], target: string) {
    this.backgroundLayers = backgroundLayers;
    this.target = target;
    this.backgroundLayers.forEach(layer => this.layers[layer.id] = layer);
  }

  getBackgroundLayers(): Layer[] {
    let layers: Layer[] = this.backgroundLayers.map(layer => { return { id: layer.id, name: layer.name } })
    return layers;
  }

  setBackground(id: number): void {
    this.backgroundLayers.forEach(layer => this.map?.setVisible(this.mapId(layer), layer.id === id));
  }

  private mapId(layer: LayerSettings): string {
    return `${layer.name}-${layer.id}`;
  }

  create(): void {
    this.map = new OlMap(this.target);
    for (let layer of this.backgroundLayers) {
      this.map.addTileServer({
        name: this.mapId(layer),
        url: layer.url,
        params: layer.params,
        visible: false,
        opacity: 1,
        xyz: layer.xyz
      });
    }
  }

  setLayerAttr(id: number, options: {opacity?: number, visible?: boolean}): void {
    let layer = this.layers[id];
    if (!layer) return;
    if (options.opacity != undefined) this.map?.setOpacity(this.mapId(layer), options.opacity);
    if (options.visible != undefined) this.map?.setVisible(this.mapId(layer), options.visible);
  }

  destroy(): void {
    if(!this.map) return;
    this.map.unset();
    this.destroyed.emit(this.target);
  }
}
