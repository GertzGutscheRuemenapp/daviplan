import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject } from "rxjs";
import { AgeGroup, PlanningProcess, Scenario } from "../../rest-interfaces";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();
  year$ = new BehaviorSubject<number>(0);
  processes$ = new BehaviorSubject<PlanningProcess[]>([]);

  constructor(protected http: HttpClient, protected rest: RestAPI) {
    super(http, rest);
    this.fetchAreaLevels();
    this.fetchInfrastructures();
    this.fetchYears();
    this.fetchProcesses();
  }

  fetchProcesses(){
    this.http.get<PlanningProcess[]>(this.rest.URLS.processes).subscribe(processes => {
      this.http.get<Scenario[]>(this.rest.URLS.processes).subscribe(scenarios => {
        scenarios.forEach(scenario => {
          const process = processes.find(p => p.id === scenario.planningProcess);
          if (!process) return;
          if (!process.scenarios) process.scenarios = [];
          process.scenarios.push(scenario);
        })
        this.processes$.next(processes);
      })
    });
  };

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }
}
