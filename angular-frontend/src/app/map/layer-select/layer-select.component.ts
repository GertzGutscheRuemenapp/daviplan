import { Component, Input, OnInit } from '@angular/core';
import { MapService } from "../map.service";
import { OlMap } from "../map";
import { ChangeDetectorRef } from '@angular/core';
import {FormControl} from "@angular/forms";
import {pairwise, startWith} from "rxjs/operators";

@Component({
  selector: 'app-layer-select',
  templateUrl: './layer-select.component.html',
  styleUrls: ['./layer-select.component.scss']
})
export class LayerSelectComponent implements OnInit {
  @Input() target!: string;
  overlayLayers: string[] = [];
  backgroundLayers: string[] = [''];
  map?: OlMap;
  backgroundControl: FormControl;

  constructor(private mapService: MapService, private cdRef:ChangeDetectorRef) {
    this.backgroundControl = new FormControl();
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
    this.backgroundControl.valueChanges.pipe(
      startWith(this.backgroundControl.value),
      pairwise()
    ).subscribe(
      ([old,value])=>{
        this.map?.setVisible(old, false);
        this.map?.setVisible(value, true);
      }
    )
  }

  initSelect(): void {
    if (!this.map) return;
    this.backgroundLayers = Object.keys(this.map.layers);
    this.backgroundControl.setValue(this.backgroundLayers[0]);
    this.cdRef.detectChanges();
  }
}
