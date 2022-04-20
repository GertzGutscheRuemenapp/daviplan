import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import {
  Place, AreaLevel, Area, Gender, AreaIndicatorData, PopulationData, AgeGroup,
  Infrastructure, Service, Capacity, Prognosis, StatisticsData
} from "./rest-interfaces";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "./rest-api";
import { sortBy, wktToGeom } from "./helpers/utils";
import * as turf from "@turf/helpers";
import centroid from '@turf/centroid';
import { MultiPolygon, Polygon } from "ol/geom";
import { GeoJSON } from "ol/format";
import { map } from "rxjs/operators";

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

  protected getCachedData<Type>(url: string, options?: { reset?: boolean }): Observable<Type> {
    const observable = new Observable<Type>(subscriber => {
      if (options?.reset || !this.genericCache[url]){
        this.http.get<Type>(url).subscribe(data => {
          this.genericCache[url] = data;
          subscriber.next(data);
          subscriber.complete();
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

  private getYears(url: string): Observable<number[]> {
    const query = this.getCachedData<any[]>(url);
    return query.pipe(map(years => {
      return years.map( year => { return year.year })
    }));
  }

  getRealYears(): Observable<number[]> {
    const url = `${this.rest.URLS.years}?has_real_data=true`;
    return this.getYears(url);
  }

  getPrognosisYears(): Observable<number[]> {
    const url = `${this.rest.URLS.years}?has_prognosis_data=true`;
    return this.getYears(url);
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

  getPlaces(infrastructureId: number, options?: { targetProjection?: string }): Observable<Place[]>{
    const observable = new Observable<Place[]>(subscriber => {
      const cached = this.placesCache[infrastructureId];
      if (!cached) {
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

  getCapacities(year: number, serviceId: number, scenarioId: number | undefined = undefined): Observable<Capacity[]>{
    year = year || 0;
    let key = `${serviceId}-${year}`;
    if (scenarioId !== undefined)
      key += `-${scenarioId}`
    const observable = new Observable<Capacity[]>(subscriber => {
      const cached = this.capacitiesCache[key];
      if (!cached) {
        this.setLoading(true);
        let url = `${this.rest.URLS.capacities}?service=${serviceId}&year=${year}`;
        if (scenarioId !== undefined)
          url += `&scenario=${scenarioId}`;
        const query = this.http.get<Capacity[]>(url);
        query.subscribe( capacities => {
          this.capacitiesCache[key] = capacities;
          this.setLoading(false);
          subscriber.next(capacities);
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

  getAreas(areaLevelId: number, options?: { targetProjection?: string, reset?: boolean }): Observable<Area[]>{
    // ToDo: return clones of areas to avoid side-effects
    const observable = new Observable<Area[]>(subscriber => {
      const cached = this.areaCache[areaLevelId];
      if (options?.reset || !cached) {
        const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
        this.setLoading(true);
        const query = this.http.get<any>(`${this.rest.URLS.areas}?area_level=${areaLevelId}`);
        query.subscribe( areas => {
          this.areaCache[areaLevelId] = areas.features;
          const format = new GeoJSON();
          areas.features.forEach((area: Area )=> {
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
          subscriber.next(areas.features);
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

  getStatistics(options?: { year?: number, areaId?: number }): Observable<StatisticsData[]> {
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

  setLoading(isLoading: boolean) {
    this.isLoading$.next(isLoading);
  }
}
