import { ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { OlMap } from "../map";
import { MapService } from "../map.service";
import { FormControl } from "@angular/forms";

const mockLayerGroups: Record<string, any[]> = {
/*  Leistungen: [
    { name: 'Kita', checked: true },
    { name: 'Krippe', checked: true },
  ],*/
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
  map?: OlMap;
  activeBackground = '';
  backgroundLayers: string[] = [''];
  layerGroups: Record<string, any[]> = mockLayerGroups;
  activeGroups: string[] = [];

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) {
  }

  ngOnInit (): void {
    this.map = this.mapService.getMap(this.target);
    if (this.map)
      this.initSelect();
    // map not ready yet
    else
      this.mapService.mapCreated.subscribe( map => {
        if (map.target = this.target) {
          this.map = map;
          this.initSelect();
        }
      })
  }

  initSelect(): void {
    if (!this.map) return;
    this.backgroundLayers = this.mapService.backgroundLayers.map(layer => layer.name);
    this.activeBackground = this.backgroundLayers[0];
    this.activeGroups = Object.keys(this.layerGroups).filter(g => this.layerGroups[g].filter(l => l.checked).length > 0);
    this.selectBackground(this.activeBackground);
    this.cdRef.detectChanges();
  }

  selectBackground(selected: string) {
    this.backgroundLayers.forEach(layer => (this.map?.setVisible(layer, layer === selected)));
  }
}
