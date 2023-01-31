import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import {
  Capacity, FieldType,
  Indicator,
  Infrastructure,
  Place,
  PlanningProcess,
  Scenario,
  Service,
  TotalCapacityInScenario,
  User
} from "../../rest-interfaces";
import { SettingsService } from "../../settings.service";
import { CookieService } from "../../helpers/cookies.service";
import { ColumnFilter, deSerializeFilter, serializeFilter } from "../../elements/filter-table/filter-table.component";
import { map } from "rxjs/operators";
import { wktToGeom } from "../../helpers/utils";
import { Geometry } from "ol/geom";

export type PlaceFilter = { name: string, property?: string, service?: number, field?: string, filter: ColumnFilter };

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  private placeFilters: Record<number, PlaceFilter[]> = {};
  // private placeFilters: Record<number, { attribute: string, service: Service, filter: ColumnFilter }[]> = {};
  // cache already requested capacities: {scenario_id: {service_id: {year: capacity}}}
  private capacitiesPerScenarioService: Record<number, Record<string, Record<number, Capacity[]>>> = {};
  private fieldTypes: FieldType[] = [];
  year$ = new BehaviorSubject<number>(0);
  activeProcess$ = new BehaviorSubject<PlanningProcess | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
  activeInfrastructure$ = new BehaviorSubject<Infrastructure | undefined>(undefined);
  activeService$ = new BehaviorSubject<Service | undefined>(undefined);
  activeInfrastructure?: Infrastructure;
  activeYear?: number;
  activeService?: Service;
  activeScenario?: Scenario;
  activeProcess?: PlanningProcess;
  showScenarioMenu = false;
  scenarioChanged = new EventEmitter<Scenario>();

  constructor(protected http: HttpClient, protected rest: RestAPI, private settings: SettingsService,
              private cookies: CookieService) {
    super(http, rest);
    // store the current states in variables, easier to access than subscribing to observables
    // could also be done later with [...].pipe(take(1)).subscribe(...), easier by remembering in separate variable
    this.getFieldTypes().pipe(map(fieldTypes => {
      this.fieldTypes = fieldTypes;
    }))
    this.activeInfrastructure$.subscribe(infrastructure => {
      this.activeInfrastructure = infrastructure;
      if (infrastructure)
        this.placeFilters[infrastructure.id] = this.restoreFilters(infrastructure);
    });
    this.activeService$.subscribe(service => this.activeService = service);
    this.year$.subscribe(year => this.activeYear = year);
    this.activeProcess$.subscribe(process => this.activeProcess = process);
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

  getPlaces(options?: {
    infrastructure?: Infrastructure,
    scenario?: Scenario,
    service?: Service,
    targetProjection?: string,
    reset?: boolean,
    addCapacities?: boolean,
    filter?: {
      columnFilter?: boolean,
      year?: number,
      hasCapacity?: boolean
    }
  }): Observable<Place[]>{
    const _this = this;
    const infrastructure = options?.infrastructure || this.activeInfrastructure;
    const observable = new Observable<Place[]>(subscriber => {
      function next(places: Place[]){
        subscriber.next(places);
        subscriber.complete();
      };
      // no infrastructure -> no places
      if (!infrastructure) {
        next([]);
        return;
      };
      function postprocess(places: Place[]){
        if (options?.filter?.columnFilter || options?.addCapacities || options?.filter?.hasCapacity) {
          let observables: Observable<any>[] = [];
          // scenario capacity is required in any case (filter and adding cap.)
          observables.push(_this.updateCapacities({ infrastructure: infrastructure, year: options?.filter?.year, scenario: options?.scenario, reset: options?.reset }).pipe(map(() => {
            places.forEach(place => {
              const cap = _this.getPlaceCapacity(place, { service: options?.service, scenario: options?.scenario });
              place.capacity = cap;
            });
          })))
          // if capacities shall be added to the places add those of the base scenario too
          if (options?.addCapacities && !options?.scenario?.isBase)
            observables.push(_this.updateCapacities({ infrastructure: infrastructure, year: options?.filter?.year }).pipe(map(() => {
              places.forEach(place => {
                const cap = _this.getPlaceCapacity(place, { service: options?.service });
                place.baseCapacity = cap;
              })
            })));
          forkJoin(...observables).subscribe(() => {
            if (options.filter) {
              let placesTmp: Place[] = [];
              // could take the normal array filter function instead but got messy
              places.forEach(place => {
                if (options.filter?.hasCapacity && place.capacity === 0) return;
                // ToDo: pass year
                if (options.filter?.columnFilter && !_this._filterPlace(place)) return;
                placesTmp.push(place);
              });
              places = placesTmp;
            }
            next(places);
          });
        }
        // nothing to do -> emit
        else
          next(places);
      }
      let params: any = {infrastructure: infrastructure.id};
      if (options?.scenario && !options.scenario.isBase) params.scenario = options.scenario.id;
      this.getCachedData<Place[]>(this.rest.URLS.places, { reset: options?.reset, params: params }).subscribe(places => {
        const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
        places.forEach((place: Place) => {
          if (!(place.geom instanceof Geometry)) {
            const geometry = wktToGeom(place.geom as string,
              { targetProjection: targetProjection, ewkt: true });
            if (geometry)
              place.geom = geometry;
          }
        })
        postprocess(places);
      })
    });
    return observable;
  }

  getTotalCapactities(year: number, service: Service, options?: {scenario?:Scenario, planningProcess?: PlanningProcess, reset?: boolean}): Observable<TotalCapacityInScenario[]> {
    const url = `${this.rest.URLS.services}${service.id}/total_capacity_in_year/`;
    let params: {year:number, scenario?:number, planningProcess?:number} = {year: year};
    if (options?.scenario){
      params.scenario = options.scenario.id
    }
    if (options?.planningProcess){
      params.planningProcess = options.planningProcess.id
    };
    return this.getCachedData<TotalCapacityInScenario[]>(url, {params: params, reset: options?.reset});
  }

  updateCapacities(options?: { infrastructure?: Infrastructure, year?: number, scenario?: Scenario, reset?: boolean }): Observable<any> {
    const year = (options?.year !== undefined)? options?.year: this.activeYear;
    const _this = this;
    const scenarioId = (options?.scenario?.id !== undefined)? options.scenario.id: -1;
    const observable = new Observable<any>(subscriber => {
      let scenarioCapacities = this.capacitiesPerScenarioService[scenarioId];
      if (!scenarioCapacities)
        scenarioCapacities = this.capacitiesPerScenarioService[scenarioId] = {};
      // check for data missing in cache and collect requests for those
      function update(infrastructure: Infrastructure | undefined) {
        let observables: Observable<any>[] = [];
        infrastructure?.services?.forEach(service => {
          let serviceCapacities = scenarioCapacities[service.id];
          if (!serviceCapacities)
            serviceCapacities = scenarioCapacities[service.id] = {};
          if (!serviceCapacities[year!] || options?.reset) {
            observables.push(_this.getCapacities({
              year: year,
              service: service,
              scenario: options?.scenario,
              reset: true
            }).pipe(map(capacities => {
              serviceCapacities[year!] = capacities;
            })));
          }
        });
        // do all the missing requests
        if (observables.length) {
          forkJoin(...observables).subscribe(() => {
            subscriber.next();
            subscriber.complete();
          })
        }
        // if all is cached already -> just emit it is that ready
        else {
          subscriber.next();
          subscriber.complete();
        }
      }
      if (options?.infrastructure) {
        this.getInfrastructures().subscribe(infrastructures => {
          let infrastructure = infrastructures.find(i => i.id === options?.infrastructure?.id);
          update(infrastructure);
        })
      }
      else
        update(this.activeInfrastructure);
    })
    return observable;
  }

  resetCapacities(scenarioId: number, serviceId?: number, year?: number){
    const scenarioCapacities = this.capacitiesPerScenarioService[scenarioId];
    if (scenarioCapacities && serviceId !== undefined) {
      if (scenarioCapacities[serviceId] && year !== undefined)
        delete scenarioCapacities[serviceId][year];
      else
        delete scenarioCapacities[serviceId];
    }
    else
      delete this.capacitiesPerScenarioService[scenarioId];
  }

  getPlaceCapacity(place: Place, options?: { service?: Service, scenario?: Scenario, year?: number}): number{
    const service = options?.service || this.activeService;
    const year = (options?.year !== undefined)? options?.year: this.activeYear;
    if (!service || !year) return 0;
    const scenarioId = options?.scenario? options.scenario.id: -1;
    const scenarioCapacities = this.capacitiesPerScenarioService[scenarioId] || {};
    const serviceCapacities = scenarioCapacities[service.id] || {};
    const cap = serviceCapacities[year]?.find(c => c.place === place.id);
    return cap?.capacity || 0;
  }

  /**
   * restore filters for given infrastructure from cookies
   */
  restoreFilters(infrastructure: Infrastructure): PlaceFilter[] {
    const serialized = this.cookies.get(`planning-filter-${infrastructure.id}`, 'json') || [];
    const filters: PlaceFilter[] = [];
    serialized.forEach((obj: any) => {
      if (!obj || !obj.filter) return;
      const columnFilter = deSerializeFilter(obj.filter);
      if (!columnFilter) return;
      filters.push({
        name: obj.name,
        service: obj.service,
        property: obj.property,
        field: obj.field,
        filter: columnFilter
      })
    })
    return filters;
  }

  setPlaceFilters(infrastructure: Infrastructure, placeFilters: PlaceFilter[]): void{
    this.placeFilters[infrastructure.id] = placeFilters;
    let filtersSerialized = placeFilters.map(pf => {
      let clone: any = Object.assign({}, pf);
      // serialize the filter object
      clone.filter = serializeFilter(pf.filter);
      return clone;
    })
    this.cookies.set(`planning-filter-${infrastructure.id}`, filtersSerialized, {type: 'json'});
  }

  getPlaceFilters(infrastructure: Infrastructure | undefined): PlaceFilter[] {
    if (!infrastructure) return [];
    return (this.placeFilters[infrastructure.id] || []).filter(pf => pf.filter.active);
  }

  private _filterPlace(place: Place): boolean {
    if (!this.activeInfrastructure) return false;
    const filterColumns = this.getPlaceFilters(this.activeInfrastructure);
    // all filters have to match (AND-linked in loop)
    let match = true;
    // cloned place with current capacity
    filterColumns.forEach((filterColumn, i) => {
      // service capacity filter
      if (filterColumn.service) {
        const service = this.activeInfrastructure!.services.find(s => s.id === filterColumn.service);
        const cap = this.getPlaceCapacity(place, { service: service });
        match = match && filterColumn.filter.filter(cap);
      }
      // field filter
      else if (filterColumn.field) {
        const value = place.attributes[filterColumn.field];
        match = match && filterColumn.filter.filter(value);
      }
      // property filter
      else if (filterColumn.property){
        // if no property was given take the given name as a last resort
        if (place.hasOwnProperty(filterColumn.property)) {
          const value = place[filterColumn.property as keyof Place];
          match = match && filterColumn.filter.filter(value);
        }
      }
    })
    return match;
  }
}
