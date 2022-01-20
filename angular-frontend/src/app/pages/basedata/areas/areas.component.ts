import { AfterViewInit, ChangeDetectorRef, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { AreaLevel, BasedataSettings } from "../../../rest-interfaces";
import { Observable } from "rxjs";
import { sortBy } from "../../../helpers/utils";
import { HttpClient } from "@angular/common/http";
import { MatDialog } from "@angular/material/dialog";
import { RestAPI } from "../../../rest-api";


@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['../../../map/legend/legend.component.scss','./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  selectedAreaLevel?: AreaLevel;
  basedataSettings?: BasedataSettings;
  presetLevels: AreaLevel[] = [];
  customAreaLevels: AreaLevel[] = [];
  colorSelection: string = 'black';

  constructor(private mapService: MapService,private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-areas-map');
    this.mapControl.setBackground(this.mapControl.getBackgroundLayers()[0].id);

    this.fetchBasedataSettings().subscribe(res => {
      this.fetchAreas().subscribe(res => {
        this.selectedAreaLevel = this.presetLevels[0];
        this.colorSelection = this.selectedAreaLevel.symbol?.fillColor || 'black';
      })
    })
  }

  /**
   * fetch basedata-settings
   */
  fetchBasedataSettings(): Observable<BasedataSettings> {
    const query = this.http.get<BasedataSettings>(this.rest.URLS.basedataSettings);
    query.subscribe((basedataSettings) => {
      this.basedataSettings = basedataSettings;
    });
    return query;
  }

  /**
   * fetch areas
   */
  fetchAreas(): Observable<AreaLevel[]> {
    const query = this.http.get<AreaLevel[]>(this.rest.URLS.arealevels);
    query.subscribe((areaLevels) => {
      this.presetLevels = [];
      this.customAreaLevels = [];
      areaLevels.forEach(level => {
        if (level.isPreset)
          this.presetLevels.push(level);
        else
          this.customAreaLevels.push(level);
      })
      this.presetLevels = sortBy(this.presetLevels, 'order');
      this.customAreaLevels = sortBy(this.customAreaLevels, 'order');
    });
    return query;
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

  onSelect(areaLevel: AreaLevel): void {
    this.selectedAreaLevel = areaLevel;
    this.colorSelection = this.selectedAreaLevel.symbol?.fillColor || 'black';
  }

  onCreateArea(): void {
  }

  onDeleteArea(): void {
  }

}
