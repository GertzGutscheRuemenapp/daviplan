import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'
import OSM from 'ol/source/OSM';
import {User} from "../pages/login/users";
import {Observable} from "rxjs";


interface Layer {
  id: number;
  name: string;
  url: string;
  params?: any;
  visible: boolean;
  xyz?: boolean;
}

const mockBackgroundLayers: Layer[] = [
  {
    id: 1,
    name: 'OSM',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    visible: false,
    xyz: true
  },
  {
    id: 2,
    name: 'TopPlus',
    url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
    params: { layers: 'web' },
    visible: false
  },
]

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private maps: Record<string, OlMap> = {};
  mapCreated = new EventEmitter<OlMap>();

  backgroundLayers: Layer[] = mockBackgroundLayers;

  constructor() { }

  create(target: string): OlMap {
    let map = new OlMap(target);
    this.maps[target] = map;
    for (let layer of this.backgroundLayers) {
      map.addTileServer(layer);
    }
    this.mapCreated.emit(map);
    return map;
  }

  getMap(target: string): OlMap {
    return this.maps[target];
  }

  remove(target: string): void {
    let map = this.maps[target];
    if (!map) return;
    map.unset();
    delete this.maps[target];
  }
}
