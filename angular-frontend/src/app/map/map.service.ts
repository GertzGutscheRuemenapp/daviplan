import { Injectable, EventEmitter } from '@angular/core';
import { OlMap } from './map'
import {User} from "../pages/login/users";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})

export class MapService {
  private maps: Record<string, OlMap> = {};
  mapCreated = new EventEmitter<OlMap>();

  baseLayers: Record<string, string> = {
    // 'OSM': new TileLayer({ source: new OSM({}), visible: true }),
    'Ahocevar': 'https://ahocevar.com/geoserver/wfs'
  }

  constructor() { }

  create(target: string): OlMap {
    let map = new OlMap(target);
    this.maps[target] = map;
    for (let k in this.baseLayers) {
      map.addWFSLayer(k, this.baseLayers[k]);
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
