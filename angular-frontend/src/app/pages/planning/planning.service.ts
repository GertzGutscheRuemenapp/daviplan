import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject, Observable } from "rxjs";
import { Indicator, PlanningProcess, Scenario } from "../../rest-interfaces";
import { SettingsService } from "../../settings.service";
import { CookieService } from "../../helpers/cookies.service";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();
  year$ = new BehaviorSubject<number>(0);
  activeProcess$ = new BehaviorSubject<PlanningProcess | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
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
  }

  getIndicators(serviceId: number): Observable<Indicator[]>{
    const url = `${this.rest.URLS.services}${serviceId}/get_indicators/`;
    return this.getCachedData<Indicator[]>(url);
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
          name: 'Status Quo Fortschreibung',
          prognosis: baseSettings.defaultPrognosis,
          modevariants: baseSettings.defaultModeVariants,
          demandratesets: baseSettings.defaultDemandRateSets
        }
        subscriber.next(baseScenario);
        subscriber.complete();
      })
    })
    return observable
  }

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }
}
