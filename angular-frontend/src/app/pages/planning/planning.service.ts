import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import {
  Capacity,
  Indicator,
  Infrastructure,
  Place,
  PlanningProcess,
  Scenario,
  Service,
  User
} from "../../rest-interfaces";
import { SettingsService } from "../../settings.service";
import { CookieService } from "../../helpers/cookies.service";
import { FilterColumn } from "../../elements/filter-table/filter-table.component";
import { map } from "rxjs/operators";
import { sortBy, wktToGeom } from "../../helpers/utils";
import { Geometry } from "ol/geom";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  isReady: boolean = false;
  placeFilterColumns: FilterColumn[] = [];
  private placesCache: Record<number, Place[]> = {};
  private capacitiesPerScenarioService: Record<number, Record<string, Capacity[]>> = {};
  year$ = new BehaviorSubject<number>(0);
  activeProcess$ = new BehaviorSubject<PlanningProcess | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
  activeInfrastructure$ = new BehaviorSubject<Infrastructure | undefined>(undefined);
  activeService$ = new BehaviorSubject<Service | undefined>(undefined);
  activeInfrastructure?: Infrastructure;
  activeYear?: number;
  activeService?: Service;
  activeScenario?: Scenario;
  showScenarioMenu = false;

  constructor(protected http: HttpClient, protected rest: RestAPI, private settings: SettingsService,
              private cookies: CookieService) {
    super(http, rest);
/*    this.year$.next(this.cookies.get('planning-year', 'number') || 0);
    this.activeProcess$.next(this.cookies.get('planning-year', 'number') || 0);
    this.activeScenario$.next(this.cookies.get('planning-year', 'number') || 0);

    this.year$.subscribe(year => {
      this.cookies.set('planning-year', year);
    });
    this.activeProcess$.subscribe(process => {
      this.cookies.set('planning-process', process?.id);
    })
    this.activeScenario$.subscribe(scenario => {
      this.cookies.set('planning-scenario', scenario?.id);
    })*/
    // could also be done later with [...].pipe(take(1)).subscribe(...), easier by remembering in separate variable
    this.activeInfrastructure$.subscribe(infrastructure => this.activeInfrastructure = infrastructure);
    this.activeService$.subscribe(service => this.activeService = service);
    this.year$.subscribe(year => this.activeYear = year);
    this.activeScenario$.subscribe(scenario => this.activeScenario = scenario);
  }

  getIndicators(serviceId: number): Observable<Indicator[]>{
    const url = `${this.rest.URLS.services}${serviceId}/get_indicators/`;
    return this.getCachedData<Indicator[]>(url);
  }

  getUsers(): Observable<User[]>{
    const url = this.rest.URLS.users;
    return this.getCachedData<User[]>(url);
  }

  getProcesses(): Observable<PlanningProcess[]>{
    const observable = new Observable<PlanningProcess[]>(subscriber => {
      const processUrl = this.rest.URLS.processes;
      this.getCachedData<PlanningProcess[]>(processUrl).subscribe(processes => {
        const scenarioUrl = this.rest.URLS.scenarios;
        this.getCachedData<Scenario[]>(scenarioUrl).subscribe(scenarios => {
          processes.forEach(process => process.scenarios = []);
          scenarios.forEach(scenario => {
            const process = processes.find(p => p.id === scenario.planningProcess);
            if (!process) return;
            process.scenarios!.push(scenario);
          })
          subscriber.next(processes);
          subscriber.complete();
        })
      })
    });
    return observable;
  };

  getBaseScenario(): Observable<Scenario> {
    const observable = new Observable<Scenario>(subscriber => {
      // ToDo: what happens if baseDataSettings$ is refreshed or not ready?
      this.settings.baseDataSettings$.subscribe(baseSettings => {
        const baseScenario: Scenario = {
          id: -1,
          planningProcess: -1,
          isBase: true,
          name: 'Status Quo Fortschreibung',
          prognosis: baseSettings.defaultPrognosis,
          modeVariants: baseSettings.defaultModeVariants,
          demandrateSets: baseSettings.defaultDemandRateSets
        }
        subscriber.next(baseScenario);
        subscriber.complete();
      })
    })
    return observable;
  }

  getPlaces(infrastructureId: number, options?: {
    scenario?: number,
    targetProjection?: string,
    reset?: boolean,
    addCapacities?: boolean,
    filter?: {
      columnFilter?: boolean,
      year?: number,
      hasCapacity?: boolean
    }
  }): Observable<Place[]>{
    /*this.getCachedData<Place[]>('this.rest.URLS.places', {
      params: { infrastructure: infrastructureId }, reset: options?.reset })*/
    const _this = this;
    const observable = new Observable<Place[]>(subscriber => {
      function next(places: Place[]){
        subscriber.next(places);
        subscriber.complete();
      };
      function filter(places: Place[]){
        if (options?.filter?.columnFilter || options?.addCapacities || options?.filter?.hasCapacity) {
          _this.updateCapacities({ infrastructureId: infrastructureId, year: options?.filter?.year, scenarioId: options?.scenario }).subscribe(() => {
            let placesTmp: Place[] = [];
            places.forEach(place => {
              const cap = _this.getPlaceCapacity(place);
              if (options.filter?.hasCapacity && cap === 0) return;
              // ToDo: pass year
              if (options.filter?.columnFilter && !_this._filterPlace(place)) return;
              if (options?.addCapacities)
                place.capacity = cap;
              placesTmp.push(place);
            });
            places = placesTmp;
            next(places);
          })
        }
        else
          next(places);
      }
      let params: any = {infrastructure: infrastructureId};
      if (options?.scenario) params.scenario = options.scenario;
      this.getCachedData<Place[]>(this.rest.URLS.places, { reset: options?.reset, params: params }).subscribe(places => {
        const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
        places.forEach((place: Place )=> {
          if (!(place.geom instanceof Geometry)) {
            const geometry = wktToGeom(place.geom as string,
              { targetProjection: targetProjection, ewkt: true });
            place.geom = geometry;
          }
        })
        filter(places);
      })
    });
    return observable;
  }

  updateCapacities(options?: { infrastructureId?: number, year?: number, scenarioId?: number }): Observable<any> {
    const year = (options?.year !== undefined)? options?.year: this.activeYear;
    const _this = this;
    const scenarioId = options?.scenarioId || -1;
    const observable = new Observable<any>(subscriber => {
      let scenarioCapacities = this.capacitiesPerScenarioService[scenarioId];
      if (!scenarioCapacities)
        scenarioCapacities = this.capacitiesPerScenarioService[scenarioId] = {};
      function update(infrastructure: Infrastructure | undefined) {
        let observables: Observable<any>[] = [];
        infrastructure?.services?.forEach(service => {
          let key = `${service.id}-${year}`;
          if (!scenarioCapacities[key]) {
            observables.push(_this.getCapacities({
              year: year,
              service: service.id!,
              scenario: options?.scenarioId,
              reset: true
            }).pipe(map(capacities => {
              scenarioCapacities[key] = capacities;
            })));
          }
        });
        if (observables.length > 0) {
          forkJoin(...observables).subscribe(() => {
            subscriber.next();
            subscriber.complete();
          })
        }
        else {
          subscriber.next();
          subscriber.complete();
        }
      }
      if (options?.infrastructureId !== undefined) {
        this.getInfrastructures().subscribe(infrastructures => {
          let infrastructure = infrastructures.find(i => i.id === options.infrastructureId);
          update(infrastructure);
        })
      }
      else update(this.activeInfrastructure);
    })
    return observable;
  }

  resetCapacities(serviceId: number, scenarioId: number){
    const capacities = this.capacitiesPerScenarioService[scenarioId];
    if (capacities)
      delete capacities[serviceId];
  }

  getPlaceCapacity(place: Place, options?: { service?: Service, scenario?: Scenario, year?: number}): number{
    const service = options?.service || this.activeService;
    const scenario = options?.scenario || this.activeScenario;
    const year = (options?.year !== undefined)? options?.year: this.activeYear;
    if (!service || !scenario) return 0;
    let key = `${service.id}-${year}`;
    const scenarioCapacities = this.capacitiesPerScenarioService[scenario.id] || {};
    const cap = scenarioCapacities[key]?.find(c => c.place === place.id);
    return cap?.capacity || 0;
  }

/*  getPlaceCapacities(place: Place, service?: Service, scenario?: Scenario): Capacity[] {
    service = service || this.activeService;
    scenario = scenario || this.activeScenario;
    if (!service || !scenario) return [];
    const capacities = this.capacitiesPerScenarioService[scenario.id] || {};
    return sortBy((capacities[service.id] || []).filter(c => c.place === place.id), 'fromYear')
  }*/

  private _filterPlace(place: Place): boolean {
    if (this.placeFilterColumns.length === 0) return true;
    let match = false;
    this.placeFilterColumns.forEach((filterColumn, i) => {
      const filter = filterColumn.filter!;
      if (filterColumn.service) {
        const cap = this.getPlaceCapacity(place, { service: filterColumn.service });
        if (!filter.filter(cap)) return;
      }
      else if (filterColumn.attribute) {
        const value = place.attributes[filterColumn.attribute];
        if (!filter.filter(value)) return;
      }
      if (i === this.placeFilterColumns.length - 1) match = true;
    })
    return match;
  }
}
