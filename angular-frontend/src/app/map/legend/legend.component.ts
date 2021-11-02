import { AfterViewInit, ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { MapControl, MapService, Layer } from "../map.service";

const mockLayerGroups: Record<string, { info?: string, layers: any[] }> = {
  // Leistungen: [
  //   { name: 'Kita', checked: true },
  //   { name: 'Krippe', checked: true },
  // ],
  Standorte: {
    info: '',
    layers: [
      { name: 'Schulen', checked: false, color: 'grey', symbol: 'dot' },
      { name: 'Feuerwehr', checked: true, color: 'red', symbol: 'dot' },
      { name: 'Kinderbeutreuung', checked: false, color: 'lightblue', symbol: 'dot' },
      { name: 'Ärzte', checked: true, color: 'lightgreen', symbol: 'dot' },
    ]
  },
  Gebietsgrenzen: {
    info: '',
    layers: [
      { name: 'Gemeinden', checked: false, color: 'orange', symbol: 'line' },
      { name: 'Kreise', checked: true, color: 'yellow', symbol: 'line' },
      { name: 'Verwaltungsgemeinschaften', checked: false, color: 'red', symbol: 'line' },
      { name: 'Bundesländer', checked: false, color: 'black', symbol: 'line' },
    ]
  },
  Ökologie: {
    info: '',
    layers: [
      { name: 'Wälder', checked: false },
      { name: 'Gewässer', checked: false }
    ]
  }
}

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
  layerGroups = mockLayerGroups;
  activeGroups: string[] = [];
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
    this.activeBackground = this.backgroundLayers[0].id;
    this.mapControl.setBackground(this.activeBackground);
    this.filterActiveGroups();
    this.cdRef.detectChanges();
  }

  // ToDo: use template filter
  filterActiveGroups(): void {
    this.activeGroups = Object.keys(this.layerGroups).filter(g => this.layerGroups[g].layers.filter(l => l.checked).length > 0);
  }

  opacityChanged(id: number, value: number | null): void {
    if(value === null) return;
    this.mapControl?.setLayerAttr(id, { opacity: value });
  }
}
