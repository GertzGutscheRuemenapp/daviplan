import { AfterViewInit, ChangeDetectorRef, Component, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { AreaLevel, BasedataSettings, Layer } from "../../../rest-interfaces";
import { Observable } from "rxjs";
import { sortBy } from "../../../helpers/utils";
import { HttpClient } from "@angular/common/http";
import { MatDialog } from "@angular/material/dialog";
import { RestAPI } from "../../../rest-api";
import { InputCardComponent } from "../../../dash/input-card.component";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { MatCheckbox } from "@angular/material/checkbox";


@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['../../../map/legend/legend.component.scss','./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  @ViewChild('editArealevelCard') editArealevelCard!: InputCardComponent;
  @ViewChild('enableLayerCheck') enableLayerCheck?: MatCheckbox;
  mapControl?: MapControl;
  selectedAreaLevel?: AreaLevel;
  basedataSettings?: BasedataSettings;
  presetLevels: AreaLevel[] = [];
  customAreaLevels: AreaLevel[] = [];
  colorSelection: string = 'black';
  editArealevelErrors: string[] = [];
  Object = Object;

  constructor(private mapService: MapService,private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private formBuilder: FormBuilder) {
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('base-areas-map');

    this.fetchBasedataSettings().subscribe(res => {
      this.fetchAreas().subscribe(res => {
        this.selectedAreaLevel = this.presetLevels[0];
        this.colorSelection = this.selectedAreaLevel.symbol?.fillColor || 'black';
      })
    })
    this.setupLayerCard();
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

  setupLayerCard(): void {
    this.editArealevelCard.dialogOpened.subscribe(ok => {
      this.colorSelection = this.selectedAreaLevel?.symbol?.strokeColor || 'black';
      this.editArealevelErrors = [];
    })
    this.editArealevelCard.dialogConfirmed.subscribe((ok)=>{
      const attributes: any = this.enableLayerCheck!.checked? {
        symbol: {
          strokeColor: this.colorSelection
        }
      }: {
        symbol: null
      }
      this.editArealevelCard.setLoading(true);
      this.http.patch<AreaLevel>(`${this.rest.URLS.arealevels}${this.selectedAreaLevel?.id}/`, attributes
      ).subscribe(arealevel => {
        this.selectedAreaLevel!.symbol = arealevel.symbol;
        this.editArealevelCard.closeDialog(true);
      },(error) => {
        this.editArealevelErrors = [error.error.detail];
        this.editArealevelCard.setLoading(false);
      });
    })
  }

  selectAreaLevel(areaLevel: AreaLevel): void {
    this.selectedAreaLevel = areaLevel;
    // this.mapControl?.addLayer()
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

  onCreateArea(): void {
  }

  onDeleteArea(): void {
  }

}
