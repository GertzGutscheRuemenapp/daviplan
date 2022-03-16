import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject, Observable } from "rxjs";
import { AgeGroup, PlanningProcess, Scenario } from "../../rest-interfaces";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();
  year$ = new BehaviorSubject<number>(0);
  activeProcess$ = new BehaviorSubject<PlanningProcess | undefined>(undefined);

  constructor(protected http: HttpClient, protected rest: RestAPI) {
    super(http, rest);
  }

  getProcesses(): Observable<PlanningProcess[]>{
    const observable = new Observable<PlanningProcess[]>(subscriber => {
      const processUrl = this.rest.URLS.processes;
      this.getCachedData<PlanningProcess[]>(processUrl).subscribe(processes => {
        const scenarioUrl = this.rest.URLS.scenarios;
        this.getCachedData<Scenario[]>(scenarioUrl).subscribe(scenarios => {
          scenarios.forEach(scenario => {
            const process = processes.find(p => p.id === scenario.planningProcess);
            if (!process) return;
            if (!process.scenarios) process.scenarios = [];
            process.scenarios.push(scenario);
          })
          subscriber.next(processes);
          subscriber.complete();
        })
      });
    });
    return observable;
  };

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }
}
