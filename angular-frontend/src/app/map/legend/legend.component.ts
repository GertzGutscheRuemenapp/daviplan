import { ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { OlMap } from "../map";
import { MapControl, MapService, Layer } from "../map.service";
import { FormControl } from "@angular/forms";

const mockLayerGroups: Record<string, any[]> = {
  // Leistungen: [
  //   { name: 'Kita', checked: true },
  //   { name: 'Krippe', checked: true },
  // ],
  Standorte: [
    { name: 'Schulen', checked: false },
    { name: 'Feuerwehr', checked: true },
    { name: 'Kinderbeutreuung', checked: false },
    { name: 'Ärzte', checked: true },
  ],
  Gebietsgrenzen: [
    { name: 'Gemeinden', checked: false },
    { name: 'Kreise', checked: true },
    { name: 'Verwaltungsgemeinschaften', checked: false },
    { name: 'Gemeinden', checked: false },
  ],
  Ökologie: [
    { name: 'Wälder', checked: false },
    { name: 'Gewässer', checked: false }
  ]
}

@Component({
  selector: 'app-legend',
  templateUrl: './legend.component.html',
  styleUrls: ['./legend.component.scss']
})
export class LegendComponent implements OnInit {

  @Input() target!: string;
  layers: any;
  mapControl!: MapControl;
  activeBackground?: number;
  backgroundOpacity = 1;
  backgroundLayers: Layer[] = [];
  layerGroups: Record<string, any[]> = mockLayerGroups;
  activeGroups: string[] = [];
  editMode: boolean = true;
  Object = Object;

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) {
  }

  ngOnInit (): void {
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
    this.activeGroups = Object.keys(this.layerGroups).filter(g => this.layerGroups[g].filter(l => l.checked).length > 0);
  }

  opacityChanged(id: number, value: number | null): void {
    if(value === null) return;
    this.mapControl?.setLayerAttr(id, { opacity: value });
  }
}
