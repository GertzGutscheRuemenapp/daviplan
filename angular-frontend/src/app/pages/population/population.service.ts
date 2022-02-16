import { EventEmitter, Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { BehaviorSubject, Observable } from "rxjs";
import { Place, AreaLevel, Area, Gender } from "../../rest-interfaces";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { AgeGroup } from "../administration/project-definition/project-definition.component";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";

@Injectable({
  providedIn: 'root'
})
export class PopulationService {
  legend?: LegendComponent;
  timeSlider?: TimeSliderComponent;
  realYears$ = new BehaviorSubject<number[]>([]);
  prognosisYears$ = new BehaviorSubject<number[]>([]);
  ageGroups$ = new BehaviorSubject<AgeGroup[]>([]);
  genders$ = new BehaviorSubject<Gender[]>([]);
  areaLevels$ = new BehaviorSubject<AreaLevel[]>([]);
  areaMap: Record<number, Area[]> = {};
  private places: Record<number, Place> = {};
  isReady: boolean = false;
  ready: EventEmitter<any> = new EventEmitter();

  constructor(private http: HttpClient, private rest: RestAPI) {
    this.fetchAreaLevels();
    this.fetchAgeGroups();
    this.fetchYears();
    this.fetchGenders();
  }

  private fetchYears(): void {
    this.http.get<any[]>(`${this.rest.URLS.years}?with_population=true`).subscribe(years => {
      const ys = years.map( year => { return year.year })
      this.realYears$.next(ys);
    });
    this.http.get<any[]>(`${this.rest.URLS.years}?with_prognosis=true`).subscribe(years => {
      const ys = years.map( year => { return year.year })
      this.prognosisYears$.next(ys);
    });
  }

  private fetchGenders(): void {
    this.http.get<Gender[]>(this.rest.URLS.genders).subscribe(genders => {
      this.genders$.next(genders);
    });
  }

  private fetchAgeGroups(): void {
    this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups).subscribe(ageGroups => {
      this.ageGroups$.next(ageGroups);
    });
  }

  private fetchAreaLevels(): void {
    this.http.get<AreaLevel[]>(`${this.rest.URLS.arealevels}?active=true`).subscribe(areaLevels => {
      this.areaLevels$.next(areaLevels);
    });
  }

  getAreas(areaLevelId: number): Observable<Area[]>{
    const observable = new Observable<Area[]>(subscriber => {
      const cached = this.areaMap[areaLevelId];
      if (!cached) {
        const query = this.http.get<any>(`${this.rest.URLS.areas}?area_level=${areaLevelId}`);
        query.subscribe( areas => {
          this.areaMap[areaLevelId] = areas.features;
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

  setReady(ready: boolean): void {
    this.isReady = ready;
    this.ready.emit(ready);
  }
}
