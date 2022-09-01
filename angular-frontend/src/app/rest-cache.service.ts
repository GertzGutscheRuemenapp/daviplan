import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import {
  Place,
  AreaLevel,
  Area,
  Gender,
  AreaIndicatorResult,
  PopulationData,
  AgeGroup,
  Infrastructure,
  Service,
  Capacity,
  Prognosis,
  StatisticsData,
  DemandRateSet,
  Statistic,
  FieldType,
  RasterCell,
  TransportMode, CellResult, PlaceResult, ExtLayerGroup, ExtLayer, ModeVariant, Network, Scenario
} from "./rest-interfaces";
import { HttpClient, HttpHeaders } from "@angular/common/http";
import { RestAPI } from "./rest-api";
import { sortBy, wktToGeom } from "./helpers/utils";
import * as turf from "@turf/helpers";
import centroid from '@turf/centroid';
import { Geometry, MultiPolygon, Polygon } from "ol/geom";
import { GeoJSON } from "ol/format";
import { map, tap } from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class RestCacheService {
  // ToDo: get functions with cached values instead of BehaviorSubjects

  private genericCache: Record<string, Record<string, any>> = {};
  private areaCache: Record<number, Area[]> = {};
  private demandAreaCache: Record<string, AreaIndicatorResult[]> = {};
  private popDataCache: Record<string, PopulationData[]> = {};
  private popAreaCache: Record<string, AreaIndicatorResult[]> = {};
  private capacitiesCache: Record<string, Capacity[]> = {};
  private statisticsCache: Record<string, StatisticsData[]> = {};
  isLoading$ = new BehaviorSubject<boolean>(false);
  private _isLoading = false;
  private loadCount = 0;

  constructor(protected http: HttpClient, protected rest: RestAPI) { }

  // options.key: special key to cache data for, can be cleared separately
  protected getCachedData<Type>(url: string, options?: {
    params?: Record<string, any>,
    reset?: boolean,
    method?: 'GET' | 'POST',
    key?: string
  }): Observable<Type> {
    const method = options?.method || 'GET';
    if (options?.params) {
      if (method === 'GET') {
        let queryParams = '';
        Object.keys(options?.params).forEach((key, i) => {
          if (i > 0) queryParams += '&';
          queryParams += `${key}=${options!.params![key]}`;
        })
        if (queryParams.length > 0)
          url += `?${queryParams}`;
      }
    }
    const cacheKey = options?.key || 'generic';
    if (!this.genericCache[cacheKey]) this.genericCache[cacheKey] = {};
    const cache = this.genericCache[cacheKey];
    const requestKey = (method === 'GET' || !options?.params)? url: url + JSON.stringify(options.params);
    const _this = this;
    const observable = new Observable<Type>(subscriber => {
      if (options?.reset || !cache[requestKey]){
        const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
        this.setLoading(true);
        function done(data: any) {
          cache[requestKey] = data;
          subscriber.next(data);
          subscriber.complete();
          _this.setLoading(false);
        }
        if (method === 'GET')
          this.http.get<Type>(url, {headers: headers}).subscribe(data => {
            done(data);
          }, error => {
            this.setLoading(false);
          });
        else
          this.http.post<Type>(url, options?.params, {headers: headers}).subscribe(data => {
            done(data);
          }, error => {
            this.setLoading(false);
          });
      }
      else {
        subscriber.next(cache[requestKey]);
        subscriber.complete();
      }
    })
    return observable;
  }

  getPrognoses(): Observable<Prognosis[]> {
    const url = this.rest.URLS.prognoses;
    return this.getCachedData<Prognosis[]>(url);
  }

  getLayerGroups(options?: { reset?: boolean, external?: true }): Observable<ExtLayerGroup[]> {
    let url = this.rest.URLS.layerGroups;
    if (options?.external)
      url += '?external=true';
    return this.getCachedData<ExtLayerGroup[]>(url, options);
  }

  getLayers(options?: { active?: boolean, reset?: boolean }): Observable<ExtLayer[]> {
    let url = this.rest.URLS.layers;
    if (options?.active)
      url += '?active=true';
    return this.getCachedData<ExtLayer[]>(url, options);
  }

  getYears(options?: { params?: string, reset?: boolean }): Observable<number[]> {
    let url = this.rest.URLS.years;
    // ToDo: pass params as list of dicts
    if (options?.params)
      url += `?${options.params}`;
    const query = this.getCachedData<any[]>(url, { reset: options?.reset });
    return query.pipe(map(years => {
      const ys = years.map( year => { return year.year });
      return ys.sort();
    }));
  }

  getRealYears(): Observable<number[]> {
    return this.getYears({ params: 'has_real_data=true&is_real=true' });
  }

  getPrognosisYears(): Observable<number[]> {
    return this.getYears({ params: 'has_prognosis_data=true&is_prognosis=true' });
  }

  getGenders(): Observable<Gender[]> {
    const url = this.rest.URLS.genders;
    return this.getCachedData<Gender[]>(url);
  }

  getAgeGroups(): Observable<AgeGroup[]> {
    const url = this.rest.URLS.ageGroups;
    const query = this.getCachedData<AgeGroup[]>(url);
    return query.pipe(map(ageGroups => {
      ageGroups.forEach( ageGroup => {
        ageGroup.label = String(ageGroup.fromAge);
        ageGroup.label += (ageGroup.toAge >= 999)? ' Jahre und älter': ` bis unter ${ageGroup.toAge + 1} Jahre`;
      });
      return ageGroups;
    }));
  }

  getAreaLevels(options?: { reset?: boolean, active?: boolean }): Observable<AreaLevel[]> {
    let url = this.rest.URLS.arealevels;
    if (options?.active)
      url += '?active=true';
    const query = this.getCachedData<AreaLevel[]>(url, options);
    return query.pipe(map(areaLevels => {
      return sortBy(areaLevels, 'order');
    }));
  }

  getInfrastructures(): Observable<Infrastructure[]> {
    const observable = new Observable<Infrastructure[]>(subscriber => {
      const infraUrl = this.rest.URLS.infrastructures;
      this.getCachedData<Infrastructure[]>(infraUrl).subscribe(infrastructures => {
        const serviceUrl = this.rest.URLS.services;
        this.getCachedData<Service[]>(serviceUrl).subscribe(services => {
          infrastructures.forEach( infrastructure => {
            infrastructure.services = services.filter(service => service.infrastructure === infrastructure.id);
          })
          subscriber.next(infrastructures);
          subscriber.complete();
        });
      });
    });
    return observable;
  }

  getFieldTypes(): Observable<FieldType[]> {
    const url = this.rest.URLS.fieldTypes;
    return this.getCachedData<FieldType[]>(url);
  }

  getCapacities(options?: { year?: number, service?: number, scenario?: number, reset?: boolean }): Observable<Capacity[]>{
    let url = this.rest.URLS.capacities;
    let params: any = {};
    if (options?.year !== undefined)
      params['year'] = options.year;
    if (options?.service !== undefined)
      params['service'] = options.service;
    if (options?.scenario !== undefined && options?.scenario !== -1)
      params['scenario'] = options.scenario;
    return this.getCachedData<Capacity[]>(url, { params: params, reset: options?.reset })
  }

  getAreas(areaLevelId: number, options?: { targetProjection?: string, reset?: boolean }): Observable<Area[]>{
    // ToDo: return clones of areas to avoid side-effects
    const observable = new Observable<Area[]>(subscriber => {
      const cached = this.areaCache[areaLevelId];
      if (options?.reset || !cached) {
        const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
        this.setLoading(true);
        const query = this.http.get<any>(`${this.rest.URLS.areas}?area_level=${areaLevelId}`);
        query.subscribe( areas => {
          areas.features.forEach((f: any) => f.label = f.properties.label);
          const features = sortBy(areas.features, 'label')
          this.areaCache[areaLevelId] = features;
          const format = new GeoJSON();
          features.forEach((area: Area) => {
            const geometry = wktToGeom(area.geometry as string,
              {targetProjection: targetProjection, ewkt: true});
            area.geometry = geometry;
            // if (geometry.getCoordinates().length === 0) return;
            try {
              const poly = turf.multiPolygon((geometry as MultiPolygon).getCoordinates());
              const centroidGeom = format.readFeature(centroid(poly).geometry).getGeometry();
              area.centroid = centroidGeom;
            }
            catch (e) {
              console.log(e);
            }
          })
          this.setLoading(false);
          subscriber.next(features);
          subscriber.complete();
        }, error => {
          this.setLoading(false);
        });
      }
      else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  getRasterCells(options?: { targetProjection?: string, reset?: boolean }): Observable<RasterCell[]>{
    const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
    const observable = new Observable<RasterCell[]>(subscriber => {
      this.getCachedData<RasterCell[]>(this.rest.URLS.rasterCells, { reset: options?.reset }).subscribe(res => {
        res.forEach((rasterCell: RasterCell) => {
          if (!(rasterCell.geom instanceof Geometry)){
            const g = JSON.parse(rasterCell.geom);
            // ToDo: transform
            rasterCell.geom = new Polygon(g.coordinates);
          }
        })
        subscriber.next(res);
        subscriber.complete();
      }, error => {
        this.setLoading(false);
      });
    })
    return observable;
  }

  getClosestCell(lat: number, lon: number, options?: { targetProjection?: string }): Observable<RasterCell> {
    const query = this.getCachedData<RasterCell> (this.rest.URLS.closestCell,
      { params: { lat: lat, lon: lon }, method: 'GET' });
    const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
    return query.pipe(map(cell => {
      if (!(cell.geom instanceof Geometry)){
        const g = JSON.parse(cell.geom);
        // ToDo: transform
        cell.geom = new Polygon(g.coordinates);
      }
      return cell;
    }))
  }

  getAreaLevelPopulation(areaLevelId: number, year: number, options?: { genders?: number[], prognosis?: number, ageGroups?: number[] }): Observable<AreaIndicatorResult[]> {
    const key = `${areaLevelId}-${year}-${options?.prognosis}-${options?.genders}-${options?.ageGroups}`;
    const data: any = { area_level: areaLevelId, year: year };
    if (options?.prognosis != undefined)
      data.prognosis = options.prognosis;
    if (options?.genders)
      data.genders = options.genders;
    if (options?.ageGroups)
      data.age_group = options.ageGroups;
    const observable = new Observable<AreaIndicatorResult[]>(subscriber => {
      const cached = this.popAreaCache[key];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.post<AreaIndicatorResult[]>(this.rest.URLS.areaPopulation, data);
        query.subscribe(data => {
          this.popAreaCache[key] = data;
          this.setLoading(false);
          subscriber.next(data);
          subscriber.complete();
        },error => {
          this.setLoading(false);
        });
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  getPopulationData(areaId: number, options?: { year?: number, prognosis?: number, genders?: number[], ageGroups?: number[]}): Observable<PopulationData[]> {
    const key = `${areaId}-${options?.year}-${options?.prognosis}-${options?.genders}-${options?.ageGroups}`;
    const observable = new Observable<PopulationData[]>(subscriber => {
      const cached = this.popDataCache[key];
      if (!cached) {
        let data: any = { areas: [areaId] };
        if (options?.year != undefined)
          data.year = options?.year;
        if (options?.prognosis != undefined)
          data.prognosis = options?.prognosis;
        if (options?.genders)
          data.genders = options.genders;
        if (options?.ageGroups)
          data.age_groups = options.ageGroups;
        this.setLoading(true);
        const query = this.http.post<PopulationData[]>(this.rest.URLS.populationData, data);
        query.subscribe(data => {
          this.popDataCache[key] = data;
          this.setLoading(false);
          subscriber.next(data);
          subscriber.complete();
        },error => {
          this.setLoading(false);
        });
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  computeIndicator<Type>(indicatorName: string, serviceId: number, options?: {
    year?: number, prognosis?: number, scenario?: number, areaLevelId?: number, mode?: number  }): Observable<Type[]> {
    const url = `${this.rest.URLS.services}${serviceId}/compute_indicator/`;
    let params: any = {
      indicator: indicatorName
    };
    if (options?.year != undefined)
      params.year = options.year;
    if (options?.prognosis != undefined)
      params.prognosis = options.prognosis;
    if (options?.scenario != undefined)
      params.scenario = options.scenario;
    if (options?.areaLevelId != undefined)
      params.area_level = options.areaLevelId;
    if (options?.mode != undefined)
      params.mode = options.mode;
    return this.getCachedData<Type[]>(url, { params: params, method: 'POST', key: options?.scenario?.toString() });
  }

  getDemand(areaLevelId: number, options?: { year?: number, prognosis?: number, service?: number, scenario?: number }): Observable<AreaIndicatorResult[]> {
    let data: any = { area_level: areaLevelId };
    if (options?.year != undefined)
      data.year = options?.year;
    if (options?.prognosis != undefined)
      data.prognosis = options?.prognosis;
    if (options?.service != undefined)
      data.service = options?.service;
    if (options?.scenario != undefined)
      data.scenario = options?.scenario;
    const url = this.rest.URLS.areaDemand;
    return this.getCachedData(url, {method: 'POST', params: data, key: options?.scenario?.toString()});
  }

  getDemandRateSets(service: number, options?: { reset: boolean }): Observable<DemandRateSet[]> {
    const url = `${this.rest.URLS.demandRateSets}?service=${service}`;
    return this.getCachedData<DemandRateSet[]>(url, options);
  }

  getModeVariants(options?: { reset: boolean }): Observable<ModeVariant[]> {
    const url = this.rest.URLS.modevariants;
    return this.getCachedData<ModeVariant[]>(url, options);
  }

  getNetworks(options?: { reset: boolean }): Observable<Network[]> {
    const url = this.rest.URLS.networks;
    return this.getCachedData<Network[]>(url, options);
  }

  getStatistics(options?: { reset?: boolean }): Observable<Statistic[]>{
    const url = this.rest.URLS.statistics;
    return this.getCachedData<Statistic[]>(url, options);
  }

  getStatisticsData(options?: { year?: number, areaId?: number }): Observable<StatisticsData[]> {
    const key = `${options?.areaId}-${options?.year}`;
    const observable = new Observable<StatisticsData[]>(subscriber => {
      const cached = this.statisticsCache[key];
      if (!cached) {
        this.setLoading(true);
        let url = this.rest.URLS.statisticsData;
        let params: any = {};
        if (options?.year !== undefined)
          params['year'] = options.year;
        if (options?.areaId !== undefined)
          params['area'] = options.areaId;
        this.http.get<StatisticsData[]>(this.rest.URLS.statisticsData, { params: params }).subscribe(data => {
          this.statisticsCache[key] = data;
          this.setLoading(false);
          subscriber.next(data);
          subscriber.complete();
        }, error => {
          this.setLoading(false);
        })
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    })
    return observable;
  }

  getPlaceReachability(placeId: number, mode: TransportMode, options?: { scenario?: Scenario }): Observable<CellResult[]>{
    let params: any = { mode: mode, place: placeId };
    if (options?.scenario) params.scenario = options.scenario.id;
    return this.getCachedData<CellResult[]>(this.rest.URLS.reachabilityPlace, { params: params, method: 'POST' });
  }

  getCellReachability(cellCode: string, mode: TransportMode, options?: { scenario?: Scenario }): Observable<PlaceResult[]>{
    let params: any = { mode: mode, cell_code: cellCode };
    if (options?.scenario) params.scenario = options.scenario.id;
    return this.getCachedData<PlaceResult[]>(this.rest.URLS.reachabilityCell, { params: params, method: 'POST' });
  }

  getNextPlaceReachability(services: Service[], mode: TransportMode, options?: { year?: number, scenario?: Scenario }): Observable<CellResult[]> {
    let params: any = { mode: mode, services: services.map(s => s.id) };
    if (options?.year) params.year = options.year;
    if (options?.scenario) params.scenario = options.scenario.id;
    return this.getCachedData<CellResult[]>(this.rest.URLS.reachabilityNextPlace, { params: params, method: 'POST' });
  }

  clearCache(key?: string) {
    if (key)
      this.genericCache[key] = {};
    else
      this.reset()
  }

  reset(): void {
    this.genericCache = {};
    this.areaCache = {};
    this.demandAreaCache = {};
    this.popDataCache = {};
    this.popAreaCache = {};
    this.capacitiesCache = {};
    this.statisticsCache = {};
  }

  setLoading(isLoading: boolean) {
    this.loadCount += isLoading? 1: -1;
    const iL = this.loadCount > 0;
    if (iL != this._isLoading){
      this._isLoading = iL;
      this.isLoading$.next(this._isLoading);
    }
  }
}
