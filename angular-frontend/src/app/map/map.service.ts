import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'
import OSM from 'ol/source/OSM';
import {User} from "../pages/login/users";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})

export class MapService {
  private maps: Record<string, OlMap> = {};
  mapCreated = new EventEmitter<OlMap>();

  baseLayers: Record<string, { params: any, url: string, visible: boolean }> = {
    TopPlus:  {
      url: 'https://sgx.geodatenzentrum.de/wms_topplus_open',
      params: { layers: 'web' },
      visible: false
    }
  }

  constructor() { }

  create(target: string): OlMap {
    let map = new OlMap(target);
    this.maps[target] = map;
    for (let name in this.baseLayers) {
      let layer = this.baseLayers[name];
      map.addWMS(name, layer.url, layer.params, layer.visible);
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
