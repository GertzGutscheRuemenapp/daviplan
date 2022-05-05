import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { RestCacheService } from "../../rest-cache.service";
import { BehaviorSubject, Observable } from "rxjs";
import { PopEntry, Population, Prognosis } from "../../rest-interfaces";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";

@Injectable({
  providedIn: 'root'
})
export class PopulationService extends RestCacheService {
  legend?: LegendComponent;
  timeSlider?: TimeSliderComponent;
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();

  constructor(protected http: HttpClient, protected rest: RestAPI) {
    super(http, rest);
  }

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }

  getPopEntries(population: number): Observable<PopEntry[]> {
    return this.getCachedData<PopEntry[]>(`${this.rest.URLS.popEntries}?population=${population}`);
  }

  fetchPopulations(isPrognosis: boolean = false): Observable<Population[]>{
    const query = this.http.get<Population[]>(this.rest.URLS.populations,
      { params: { is_prognosis: isPrognosis }});
    return query;
  }

  fetchPrognoses(): Observable<Prognosis[]>{
    const query = this.http.get<Prognosis[]>(this.rest.URLS.prognoses);
    return query;
  }
}
