import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { RestCacheService } from "../../rest-cache.service";

@Injectable({
  providedIn: 'root'
})
export class PlanningService extends RestCacheService {
  legend?: LegendComponent;
  timeSlider?: TimeSliderComponent;
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();

  constructor(protected http: HttpClient, protected rest: RestAPI) {
    super(http, rest);
    this.fetchAreaLevels();
    this.fetchInfrastructures();
    this.fetchYears();
  }

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }
}
