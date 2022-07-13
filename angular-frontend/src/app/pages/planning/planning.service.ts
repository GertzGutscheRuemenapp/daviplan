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
import { wktToGeom } from "../../helpers/utils";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  isReady: boolean = false;
  placeFilterColumns: FilterColumn[] = [];
  private placesCache: Record<number, Place[]> = {};
  private capacitiesPerService: Record<number, Capacity[]> = {};
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
    return observable
  }

  getPlaces(infrastructureId: number, options?: {
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
          _this.updateCapacities({ infrastructureId: infrastructureId, year: options?.filter?.year }).subscribe(() => {
            let placesTmp: Place[] = [];
            places.forEach(place => {
              const cap = _this.getCapacity(place);
              if (options.filter?.hasCapacity && cap === 0) return;
              // ToDo: pass year
              if (options.filter?.columnFilter && !_this._filterPlace(place)) return;
              if (options?.addCapacities)
                place.properties.capacity = cap;
              placesTmp.push(place);
            });
            places = placesTmp;
            next(places);
          })
        }
        else
          next(places);
      }
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
          filter(places.features);
        }, error => {
          this.setLoading(false);
        });
      }
      else {
        filter(cached);
      }
    });
    return observable;
  }

  updateCapacities(options?: { infrastructureId?: number, year?: number }): Observable<any> {
    const year = (options?.year !== undefined)? options?.year: this.activeYear;
    const _this = this;
    const observable = new Observable<any>(subscriber => {
      function update(infrastructure: Infrastructure | undefined) {
        let observables: Observable<any>[] = [];
        infrastructure?.services?.forEach(service => {
          observables.push(_this.getCapacities({
            year: year,
            service: service.id!
          }).pipe(map(capacities => {
            _this.capacitiesPerService[service.id] = capacities;
          })));
        });
        forkJoin(...observables).subscribe(() => {
          subscriber.next();
          subscriber.complete();
        })
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

  getCapacity(place: Place, service?: Service): number{
    service = service || this.activeService;
    if (!service) return 0;
    const cap = this.capacitiesPerService[service.id]?.find(c => c.place === place.id);
    return cap?.capacity || 0;
  }

  private _filterPlace(place: Place): boolean {
    if (this.placeFilterColumns.length === 0) return true;
    let match = false;
    this.placeFilterColumns.forEach((filterColumn, i) => {
      const filter = filterColumn.filter!;
      if (filterColumn.service) {
        const cap = this.getCapacity(place, filterColumn.service);
        if (!filter.filter(cap)) return;
      }
      else if (filterColumn.attribute) {
        const value = place.properties.attributes[filterColumn.attribute];
        if (!filter.filter(value)) return;
      }
      if (i === this.placeFilterColumns.length - 1) match = true;
    })
    return match;
  }
}
