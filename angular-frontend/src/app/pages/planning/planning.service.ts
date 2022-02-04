import { Injectable } from "@angular/core";
import { LegendComponent } from "../../map/legend/legend.component";
import { BehaviorSubject } from "rxjs";
import { Infrastructure, Service, Place, AreaLevel, Area } from "../../rest-interfaces";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { area } from "d3";

@Injectable({
  providedIn: 'root'
})
export class PlanningService {
  legend?: LegendComponent;
  infrastructures$ = new BehaviorSubject<Infrastructure[]>([]);
  areaLevels$ = new BehaviorSubject<AreaLevel[]>([]);
  private places: Record<number, Place> = {};

  constructor(private http: HttpClient, private rest: RestAPI) {
    this.fetchAreaLevels();
    this.fetchInfrastructures();
  }

  private fetchAreaLevels(): void {
    this.http.get<AreaLevel[]>(`${this.rest.URLS.arealevels}?active=true`).subscribe(areaLevels => {
      this.areaLevels$.next(areaLevels);
    });
  }

  private fetchInfrastructures(): void {
    this.http.get<Infrastructure[]>(this.rest.URLS.infrastructures).subscribe(infrastructures => {
      this.http.get<Service[]>(this.rest.URLS.services).subscribe(services => {
        infrastructures.forEach( infrastructure => {
          infrastructure.services = services.filter(service => service.infrastructure === infrastructure.id);
        })
        this.infrastructures$.next(infrastructures);
      })
    })
  }

  getPlaces(infrastructureId: number): Place[]{
    return [];
  }

  getAreas(areaLevelId: number): Area[]{
    return [];
  }
}
