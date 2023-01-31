import { Injectable } from "@angular/core";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
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
  TransportMode,
  CellResult,
  PlaceResult,
  ExtLayerGroup,
  ExtLayer,
  ModeVariant,
  Network,
  Scenario,
  LogEntry,
  IndicatorLegendClass,
  TransitStop,
  TransitMatrixEntry, PlanningProcess, ModeStatistics
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

  getLogs(options?: { room?: string, reset?: boolean }): Observable<LogEntry[]> {
    const url = this.rest.URLS.logs;
    const params = options?.room? { room: options?.room }: {};
    return this.getCachedData<LogEntry[]>(url, { params, reset: options?.reset});
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

  getInfrastructures(options?: { process?: PlanningProcess }): Observable<Infrastructure[]> {
    const observable = new Observable<Infrastructure[]>(subscriber => {
      const infraUrl = this.rest.URLS.infrastructures;
      this.getCachedData<Infrastructure[]>(infraUrl).subscribe(infrastructures => {
        const serviceUrl = this.rest.URLS.services;
        if (options?.process)
          infrastructures = infrastructures.filter(i => options.process!.infrastructures.indexOf(i.id) > -1);
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

  getCapacities(options?: { year?: number, service?: Service, scenario?: Scenario, reset?: boolean }): Observable<Capacity[]>{
    let url = this.rest.URLS.capacities;
    let params: any = {};
    if (options?.year !== undefined)
      params['year'] = options.year;
    if (options?.service)
      params['service'] = options.service.id;
    if (options?.scenario && !options.scenario.isBase)
      params['scenario'] = options.scenario.id;
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
            if (geometry)
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

  getAreaLevelPopulation(areaLevelId: number, year: number, options?: {
    genders?: number[], prognosis?: number, ageGroups?: number[], comparedYear?: number, comparedPrognosis?: number
  }): Observable<{ values: AreaIndicatorResult[], legend: IndicatorLegendClass[] }> {
    const params: any = { area_level: areaLevelId, year: year };
    if (options?.prognosis != undefined)
      params.prognosis = options.prognosis;
    if (options?.genders)
      params.genders = options.genders;
    if (options?.ageGroups)
      params.age_groups = options.ageGroups;

    // no year to compare => return plain year data call
    const yearData = this.getCachedData<{ values: AreaIndicatorResult[], legend: IndicatorLegendClass[] }>(
      this.rest.URLS.areaPopulation, { params: params, method: "POST" });
    if (options?.comparedYear == undefined) return yearData;

    let compParams = Object.assign({}, params);
    if (options?.comparedPrognosis != undefined)
      compParams.prognosis = options.prognosis;
    else
      delete compParams.prognosis
    compParams.year = options?.comparedYear;
    // year to compare -> join calls and change data to return difference of results of year and results of compared year
    const compData = this.getCachedData<{ values: AreaIndicatorResult[], legend: IndicatorLegendClass[] }>(
      this.rest.URLS.areaPopulation, { params: compParams, method: "POST" });
    return forkJoin([yearData, compData]).pipe(map(results => {
      const diffValues = results[0].values.map(areaResult => {
        const compResult = results[1].values.find(r => r.areaId === areaResult.areaId);
        return {
          value: areaResult.value - (compResult?.value || 0),
          areaId: areaResult.areaId };
      });
      return { values: diffValues, legend: [] };
    }));
  }

  getPopulationData(areaId: number, options?: {
    year?: number, prognosis?: number, genders?: number[], ageGroups?: number[]
  }): Observable<{ values: PopulationData[], legend: IndicatorLegendClass[] }> {
    let params: any = { areas: [areaId] };
    if (options?.year != undefined)
      params.year = options?.year;
    if (options?.prognosis != undefined)
      params.prognosis = options?.prognosis;
    if (options?.genders)
      params.genders = options.genders;
    if (options?.ageGroups)
      params.age_groups = options.ageGroups;
    return this.getCachedData<{ values: PopulationData[], legend: IndicatorLegendClass[] }>(
      this.rest.URLS.populationData, { params: params, method: "POST" });
  }

  computeIndicator<Type>(indicatorName: string, serviceId: number, options?: {
    year?: number, prognosis?: number, scenario?: number, areaLevelId?: number, additionalParams?: any }): Observable<{ values: Type[], legend: IndicatorLegendClass[] }> {
    const url = `${this.rest.URLS.services}${serviceId}/compute_indicator/`;
    let params: any = Object.assign({indicator: indicatorName}, options?.additionalParams || {});
    if (options?.year != undefined)
      params.year = options.year;
    if (options?.prognosis != undefined)
      params.prognosis = options.prognosis;
    if (options?.scenario != undefined)
      params.scenario = options.scenario;
    if (options?.areaLevelId != undefined)
      params.area_level = options.areaLevelId;
    return this.getCachedData<{ values: Type[], legend: IndicatorLegendClass[] }>(url, { params: params, method: 'POST', key: options?.scenario?.toString() });
  }

  getDemand(areaLevelId: number, options?: { year?: number, prognosis?: number, service?: number, scenario?: number }): Observable<{ values: AreaIndicatorResult[], legend: IndicatorLegendClass[] }> {
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
    return this.getCachedData<{ values: AreaIndicatorResult[], legend: IndicatorLegendClass[] }>(url, {method: 'POST', params: data, key: options?.scenario?.toString()});
  }

  getDemandRateSets(service: number, options?: { reset?: boolean }): Observable<DemandRateSet[]> {
    const url = `${this.rest.URLS.demandRateSets}?service=${service}`;
    return this.getCachedData<DemandRateSet[]>(url, options);
  }

  getModeVariants(options?: { reset?: boolean }): Observable<ModeVariant[]> {
    const variants = this.getCachedData<ModeVariant[]>(this.rest.URLS.modevariants, options);
    const statistics = this.getModeStatistics(options);

    return forkJoin([variants, statistics]).pipe(map(results => {
      return results[0].map(v => {
        v.statistics = {
          nStops: results[1].nStops[v.id] || 0,
          nRelsPlaceCellModevariant: results[1].nRelsPlaceCellModevariant[v.id] || 0,
          nRelsPlaceStopModevariant: results[1].nRelsPlaceStopModevariant[v.id] || 0,
          nRelsStopCellModevariant: results[1].nRelsStopCellModevariant[v.id] || 0,
          nRelsStopStopModevariant: results[1].nRelsStopStopModevariant[v.id] || 0
        }
        return v;
      })
    }));
  }

  getTransitStops(options?: { reset?: boolean, variant?: number, targetProjection?: string }): Observable<TransitStop[]> {
    const url = this.rest.URLS.transitStops;
    let params: any = {};
    if (options?.variant !== undefined)
      params.variant = options.variant;
    const query = this.getCachedData<TransitStop[]>(url, { reset: options?.reset, params: params });
    const targetProjection = (options?.targetProjection !== undefined) ? options?.targetProjection : 'EPSG:4326';
    return query.pipe(map(stops => {
      stops.forEach( stop => {
        if (!(stop.geom instanceof Geometry)) {
          const geometry = wktToGeom(stop.geom as string,
            { targetProjection: targetProjection, ewkt: true });
          if (geometry)
            stop.geom = geometry;
        }
      })
      return stops;
    }));
  }

  getTransitMatrix(options?: { reset?: boolean, variant?: number }): Observable<TransitMatrixEntry[]> {
    const url = this.rest.URLS.transitMatrix;
    let params: any = {};
    if (options?.variant !== undefined)
      params.variant = options.variant;
    return this.getCachedData<TransitMatrixEntry[]>(url, { reset: options?.reset, params: params });
  }

  getNetworks(options?: { reset: boolean }): Observable<Network[]> {
    const url = this.rest.URLS.networks;
    return this.getCachedData<Network[]>(url, options);
  }

  getModeStatistics(options?: { reset?: boolean }): Observable<ModeStatistics> {
    const url = this.rest.URLS.modeStatistics;
    return this.getCachedData<ModeStatistics>(url, options);
  }

  getStatistics(options?: { reset?: boolean }): Observable<Statistic[]>{
    const url = this.rest.URLS.statistics;
    return this.getCachedData<Statistic[]>(url, options);
  }

  getStatisticsData(options?: { year?: number, areaId?: number, reset?: boolean }): Observable<StatisticsData[]> {
    let params: any = {};
    if (options?.year !== undefined)
      params['year'] = options.year;
    if (options?.areaId !== undefined)
      params['area'] = options.areaId;
    const url = this.rest.URLS.statisticsData;
    return this.getCachedData<StatisticsData[]>(url, {params: params, reset: options?.reset});
  }

  getPlaceReachability(placeId: number, mode: TransportMode, options?: { scenario?: Scenario, reset?: boolean }): Observable<{ values: CellResult[], legend: IndicatorLegendClass[] }>{
    let params: any = { mode: mode, place: placeId };
    if (options?.scenario && !options.scenario.isBase) params.scenario = options.scenario.id;
    return this.getCachedData<{ values: CellResult[], legend: IndicatorLegendClass[] }>(this.rest.URLS.reachabilityPlace, { params: params, method: 'POST', reset: options?.reset, key: options?.scenario?.id?.toString() });
  }

  getCellReachability(cellCode: string, mode: TransportMode, options?: { scenario?: Scenario, reset?: boolean }): Observable<{ values: PlaceResult[], legend: IndicatorLegendClass[] }>{
    let params: any = { mode: mode, cell_code: cellCode };
    if (options?.scenario && !options.scenario.isBase) params.scenario = options.scenario.id;
    return this.getCachedData<{ values: PlaceResult[], legend: IndicatorLegendClass[] }>(this.rest.URLS.reachabilityCell, { params: params, method: 'POST', reset: options?.reset, key: options?.scenario?.id?.toString() });
  }

  getNextPlaceReachability(services: Service[], mode: TransportMode, options?: { year?: number, scenario?: Scenario, places?: Place[], reset?: boolean }): Observable<{ values: CellResult[], legend: IndicatorLegendClass[] }> {
    let params: any = { mode: mode, services: services.map(s => s.id) };
    if (options?.year) params.year = options.year;
    if (options?.scenario && !options.scenario.isBase) params.scenario = options.scenario.id;
    if (options?.places) params.places = options.places.map(p => p.id);
    return this.getCachedData<{ values: CellResult[], legend: IndicatorLegendClass[] }>(this.rest.URLS.reachabilityNextPlace, { params: params, method: 'POST', reset: options?.reset, key: options?.scenario?.id?.toString() });
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
