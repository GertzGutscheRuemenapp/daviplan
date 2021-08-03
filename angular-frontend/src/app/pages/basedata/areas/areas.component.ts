import { AfterViewInit, ChangeDetectorRef, Component, OnDestroy } from '@angular/core';
import { MapService } from "../../../map/map.service";
import { OlMap } from "../../../map/map";
import { AreaLevel, mockAreaLevels } from "./areas";

@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  map?: OlMap;
  selectedAreaLevel?: AreaLevel;
  areaLevels?: AreaLevel[];

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) { }

  ngAfterViewInit(): void {
    this.map = this.mapService.create('level-map');
    this.areaLevels = mockAreaLevels;
    this.cdRef.detectChanges();
  }

  ngOnDestroy(): void {
    this.mapService.remove('level-map');
  }

  onSelect(areaLevel: AreaLevel): void {
    this.selectedAreaLevel = areaLevel;
  }

  onCreateArea(): void {
  }

  onDeleteArea(): void {
  }

}
