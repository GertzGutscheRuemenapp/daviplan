import { AfterViewInit, ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { MapControl, MapService } from "../map.service";
import { LayerGroup, Layer } from "../../pages/basedata/external-layers/external-layers.component";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: 'app-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.scss']
})
export class LegendComponent implements AfterViewInit {

  @Input() target!: string;
  layers: any;
  mapControl!: MapControl;
  activeBackground?: number;
  backgroundOpacity = 1;
  backgroundLayers: Layer[] = [];
  layerGroups: LayerGroup[] = [];
  activeGroups: LayerGroup[] = [];
  editMode: boolean = true;
  Object = Object;

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) {
  }

  ngAfterViewInit (): void {
    this.mapControl = this.mapService.get(this.target);
    this.initSelect();
  }

  initSelect(): void {
    this.backgroundLayers = this.mapControl.getBackgroundLayers();
    this.mapService.getLayers().subscribe(groups => {
      this.layerGroups = groups;
    })
    this.activeBackground = this.backgroundLayers[0].id;
    this.mapControl.setBackground(this.activeBackground);
    this.filterActiveGroups();
    this.cdRef.detectChanges();
  }

  onLayerToggle(layer: Layer): void {
    layer.checked = !layer.checked;
    this.mapControl.toggleLayer(layer.id, layer.checked);
  }

  // ToDo: use template filter
  filterActiveGroups(): void {
    // this.activeGroups = Object.keys(this.layerGroups).filter(g => this.layerGroups[g].layers.filter(l => l.checked).length > 0);
  }

  opacityChanged(id: number, value: number | null): void {
    if(value === null) return;
    this.mapControl?.setLayerAttr(id, { opacity: value });
  }
}
