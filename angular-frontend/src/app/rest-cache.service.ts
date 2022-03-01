import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import { Place, AreaLevel, Area, Gender, AreaPopulationData, PopulationData, AgeGroup,
  Infrastructure, Service, Capacity } from "./rest-interfaces";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "./rest-api";
import { sortBy } from "./helpers/utils";

@Injectable({
  providedIn: 'root'
})
export class RestCacheService {
  // ToDo: get functions with cached values instead of BehaviorSubjects
  realYears$ = new BehaviorSubject<number[]>([]);
  prognosisYears$ = new BehaviorSubject<number[]>([]);
  ageGroups$ = new BehaviorSubject<AgeGroup[]>([]);
  genders$ = new BehaviorSubject<Gender[]>([]);
  areaLevels$ = new BehaviorSubject<AreaLevel[]>([]);
  infrastructures$ = new BehaviorSubject<Infrastructure[]>([]);
  private areaCache: Record<number, Area[]> = {};
  private popDataCache: Record<string, PopulationData[]> = {};
  private popAreaCache: Record<string, AreaPopulationData[]> = {};
  private placesCache: Record<number, Place[]> = {};
  private capacitiesCache: Record<string, Capacity[]> = {};
  isLoading$ = new BehaviorSubject<boolean>(false);

  constructor(protected http: HttpClient, protected rest: RestAPI) { }

  fetchYears(): void {
    this.http.get<any[]>(`${this.rest.URLS.years}?with_population=true`).subscribe(years => {
      const ys = years.map( year => { return year.year })
      this.realYears$.next(ys);
    });
    this.http.get<any[]>(`${this.rest.URLS.years}?with_prognosis=true`).subscribe(years => {
      const ys = years.map( year => { return year.year })
      this.prognosisYears$.next(ys);
    });
  }

  fetchGenders(): void {
    this.http.get<Gender[]>(this.rest.URLS.genders).subscribe(genders => {
      this.genders$.next(genders);
    });
  }

  fetchAgeGroups(): void {
    this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups).subscribe(ageGroups => {
      ageGroups.forEach(ageGroup => {
        ageGroup.label = String(ageGroup.fromAge);
        ageGroup.label += (ageGroup.toAge >= 999)? ' Jahre und älter': ` bis unter ${ageGroup.toAge} Jahre`;
      })
      this.ageGroups$.next(ageGroups);
    });
  }

  fetchAreaLevels(): void {
    this.http.get<AreaLevel[]>(`${this.rest.URLS.arealevels}?active=true`).subscribe(areaLevels => {
      this.areaLevels$.next(sortBy(areaLevels, 'order'));
    });
  }

  getPlaces(infrastructureId: number): Observable<Place[]>{
    const observable = new Observable<Place[]>(subscriber => {
      const cached = this.placesCache[infrastructureId];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.get<any>(`${this.rest.URLS.places}?infrastructure=${infrastructureId}`);
        query.subscribe( places => {
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

  getAreas(areaLevelId: number): Observable<Area[]>{
    // ToDo: return clones of areas to avoid side-effects
    const observable = new Observable<Area[]>(subscriber => {
      const cached = this.areaCache[areaLevelId];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.get<any>(`${this.rest.URLS.areas}?area_level=${areaLevelId}`);
        query.subscribe( areas => {
          this.areaCache[areaLevelId] = areas.features;
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

  getAreaLevelPopulation(areaLevelId: number, year: number): Observable<AreaPopulationData[]> {
    const key = `${areaLevelId}-${year}`;
    const observable = new Observable<AreaPopulationData[]>(subscriber => {
      const cached = this.popAreaCache[key];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.get<AreaPopulationData[]>(`${this.rest.URLS.areaPopulation}?area_level=${areaLevelId}&year=${year}`);
        query.subscribe(data => {
          this.popAreaCache[key] = data;
          this.setLoading(false);
          subscriber.next(data);
          subscriber.complete();
        });
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  getPopulationData(areaId: number, year?: number): Observable<PopulationData[]> {
    const key = `${areaId}-${year}`;
    let url = `${this.rest.URLS.populationData}?area=${areaId}`
    if(year != undefined)
      url += `&year=${year}`;
    const observable = new Observable<PopulationData[]>(subscriber => {
      const cached = this.popDataCache[key];
      if (!cached) {
        this.setLoading(true);
        const query = this.http.get<PopulationData[]>(url);
        query.subscribe(data => {
          this.popDataCache[key] = data;
          this.setLoading(false);
          subscriber.next(data);
          subscriber.complete();
        });
      } else {
        subscriber.next(cached);
        subscriber.complete();
      }
    });
    return observable;
  }

  fetchInfrastructures(): void {
    this.http.get<Infrastructure[]>(this.rest.URLS.infrastructures).subscribe(infrastructures => {
      this.http.get<Service[]>(this.rest.URLS.services).subscribe(services => {
        infrastructures.forEach( infrastructure => {
          infrastructure.services = services.filter(service => service.infrastructure === infrastructure.id);
        })
        this.infrastructures$.next(infrastructures);
      })
    })
  }

  setLoading(isLoading: boolean) {
    this.isLoading$.next(isLoading);
  }
}
