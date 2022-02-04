import { Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { BehaviorSubject } from "rxjs";
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
  years$ = new BehaviorSubject<number[]>([]);
  ageGroups$ = new BehaviorSubject<AgeGroup[]>([]);
  genders$ = new BehaviorSubject<Gender[]>([]);
  areaLevels$ = new BehaviorSubject<AreaLevel[]>([]);
  private places: Record<number, Place> = {};

  constructor(private http: HttpClient, private rest: RestAPI) {
    this.fetchAreaLevels();
    this.fetchAgeGroups();
    this.fetchYears();
    this.fetchGenders();
  }

  private fetchYears(): void {
    this.http.get<any[]>(this.rest.URLS.years).subscribe(years => {
      const ys = years.map( year => { return year.year })
      this.years$.next(ys);
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

  getAreas(areaLevelId: number): Area[]{
    return [];
  }
}
