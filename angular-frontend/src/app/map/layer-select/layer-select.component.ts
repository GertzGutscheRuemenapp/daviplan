import { Component, Input, OnInit } from '@angular/core';
import { MapComponent } from '../map.component';

@Component({
  selector: 'app-layer-select',
  templateUrl: './layer-select.component.html',
  styleUrls: ['./layer-select.component.scss']
})
export class LayerSelectComponent implements OnInit {
  @Input() map!: MapComponent;
  overlayLayers: string[] = [];
  backgroundLayers: string[] = [];

  constructor() { }

  ngOnInit(): void {
    this.backgroundLayers = Object.keys(this.map.baseLayers);
  }
}
