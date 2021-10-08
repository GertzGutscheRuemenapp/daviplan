import { AfterViewInit, ChangeDetectorRef, Component, OnDestroy } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { AreaLevel, mockAreaLevels, mockPresetLevels } from "./areas";

@Component({
  selector: 'app-areas',
  templateUrl: './areas.component.html',
  styleUrls: ['../../../map/legend/legend.component.scss','./areas.component.scss']
})
export class AreasComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  selectedAreaLevel?: AreaLevel;
  presetLevels!: AreaLevel[];
  areaLevels?: AreaLevel[];
  colorSelection: string = 'black';

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('level-map');
    this.areaLevels = mockAreaLevels;
    this.presetLevels = mockPresetLevels;
    this.selectedAreaLevel = this.presetLevels[0];
    this.colorSelection = this.selectedAreaLevel.layer?.symbol?.fillColor || 'black';
    this.cdRef.detectChanges();
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

  onSelect(areaLevel: AreaLevel): void {
    this.selectedAreaLevel = areaLevel;
    this.colorSelection = this.selectedAreaLevel.layer?.symbol?.fillColor || 'black';
  }

  onCreateArea(): void {
  }

  onDeleteArea(): void {
  }

}
