import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import {
  Place, AreaLevel, Area, Gender, AreaIndicatorData, PopulationData, AgeGroup,
  Infrastructure, Service, Capacity, Prognosis, StatisticsData, DemandRateSet, Statistic, FieldType, RasterCell
} from "./rest-interfaces";
import { HttpClient } from "@angular/common/http";
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

  private genericCache: Record<string, any> = {};
  private areaCache: Record<number, Area[]> = {};
  private demandAreaCache: Record<string, AreaIndicatorData[]> = {};
  private popDataCache: Record<string, PopulationData[]> = {};
  private popAreaCache: Record<string, AreaIndicatorData[]> = {};
  private placesCache: Record<number, Place[]> = {};
  private capacitiesCache: Record<string, Capacity[]> = {};
  private statisticsCache: Record<string, StatisticsData[]> = {};
  isLoading$ = new BehaviorSubject<boolean>(false);

  constructor(protected http: HttpClient, protected rest: RestAPI) { }

  protected getCachedData<Type>(url: string, options?: { params?: Record<string, any>, reset?: boolean }): Observable<Type> {
    if (options?.params) {
      let queryParams = '';
      Object.keys(options?.params).forEach((key,i) => {
        if (i > 0) queryParams += '&';
        queryParams += `${key}=${options!.params![key]}`;
      })
      if (queryParams.length > 0)
        url += `?${queryParams}`;
    }
    const observable = new Observable<Type>(subscriber => {
      if (options?.reset || !this.genericCache[url]){
        this.setLoading(true);
        this.http.get<Type>(url).subscribe(data => {
          this.genericCache[url] = data;
          subscriber.next(data);
          subscriber.complete();
          this.setLoading(false);
        });
      }
      else {
        subscriber.next(this.genericCache[url]);
        subscriber.complete();
      }
    })
    return observable;
  }

  getPrognoses(): Observable<Prognosis[]> {
    const url = this.rest.URLS.prognoses;
    return this.getCachedData<Prognosis[]>(url);
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
    return this.getYears({ params: 'has_real_data=true&isReal=true' });
  }

  getPrognosisYears(): Observable<number[]> {
    return this.getYears({ params: 'has_prognosis_data=true&isPrognosis=true' });
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

  getPlaces(infrastructureId: number, options?: { targetProjection?: string, reset?: boolean }): Observable<Place[]>{
    const observable = new Observable<Place[]>(subscriber => {
      const cached = this.placesCache[infrastructureId];
      if (!cached || options?.reset) {
        const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
        this.setLoading(true);
        const query = this.http.get<any>(`${this.rest.URLS.places}?infrastructure=${infrastructureId}`);
        query.subscribe( places => {
          places.features.forEach((place: Place )=> {
            const geometry = wktToGeom(place.geometry as string,
              {targetProjection: targetProjection, ewkt: true});
            place.geometry = geometry;
          })
          this.placesCache[infrastructureId] = places.features;
          this.setLoading(false);
          subscriber.next(places.features);
          subscriber.complete();
        });
      }
      else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  getCapacities(options?: { year?: number, service?: number, scenario?: number }): Observable<Capacity[]>{
    let url = this.rest.URLS.capacities;
    let params: any = {};
    if (options?.year !== undefined)
      params['year'] = options.year;
    if (options?.service !== undefined)
      params['service'] = options.service;
    if (options?.scenario !== undefined)
      params['scenario'] = options.scenario;
    return this.getCachedData<Capacity[]>(url, { params: params })
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
      this.getCachedData<any>(this.rest.URLS.rasterCells, { reset: options?.reset }).subscribe(res => {
        res.features.forEach((rasterCell: RasterCell) => {
          if (!(rasterCell.geometry instanceof Geometry))
            rasterCell.geometry = wktToGeom(rasterCell.geometry as string,
              { targetProjection: targetProjection, ewkt: true});
        })
        subscriber.next(res.features);
        subscriber.complete();
      });
    })
    return observable;
  }

  getAreaLevelPopulation(areaLevelId: number, year: number, options?: { genders?: number[], prognosis?: number, ageGroups?: number[] }): Observable<AreaIndicatorData[]> {
    const key = `${areaLevelId}-${year}-${options?.prognosis}-${options?.genders}-${options?.ageGroups}`;
    const data: any = { area_level: areaLevelId, year: year };
    if (options?.prognosis != undefined)
      data.prognosis = options.prognosis;
    if (options?.genders)
      data.gender = options.genders;
    if (options?.ageGroups)
      data.age_group = options.ageGroups;
    const observable = new Observable<AreaIndicatorData[]>(subscriber => {
      const cached = this.popAreaCache[key];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.post<AreaIndicatorData[]>(this.rest.URLS.areaPopulation, data);
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
        let data: any = { area: [areaId] };
        if (options?.year != undefined)
          data.year = options?.year;
        if (options?.prognosis != undefined)
          data.prognosis = options?.prognosis;
        if (options?.genders)
          data.gender = options.genders;
        if (options?.ageGroups)
          data.age_group = options.ageGroups;
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

  getDemand(areaLevelId: number, options?: { year?: number, prognosis?: number, service?: number }): Observable<AreaIndicatorData[]> {
    const key = `${areaLevelId}-${options?.year}-${options?.prognosis}-${options?.service}`;
    const observable = new Observable<AreaIndicatorData[]>(subscriber => {
      const cached = this.demandAreaCache[key];
      if (!cached) {
        let data: any = { area_level: areaLevelId };
        if (options?.year != undefined)
          data.year = options?.year;
        if (options?.prognosis != undefined)
          data.prognosis = options?.prognosis;
        if (options?.service != undefined)
          data.service = options?.service;
        this.setLoading(true);
        const query = this.http.post<AreaIndicatorData[]>(this.rest.URLS.areaDemand, data);
        query.subscribe(data => {
          this.demandAreaCache[key] = data;
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

  getDemandRateSets(service: number, options?: { reset: boolean }): Observable<DemandRateSet[]> {
    const url = `${this.rest.URLS.demandRateSets}?service=${service}`;
    return this.getCachedData<DemandRateSet[]>(url, options);
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
        })
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    })
    return observable;
  }

  reset(): void {
    this.genericCache = {};
    this.areaCache = {};
    this.demandAreaCache = {};
    this.popDataCache = {};
    this.popAreaCache = {};
    this.placesCache = {};
    this.capacitiesCache = {};
    this.statisticsCache = {};
  }

  setLoading(isLoading: boolean) {
    this.isLoading$.next(isLoading);
  }
}
