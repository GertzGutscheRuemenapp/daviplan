import { Component, OnInit, ViewChild } from '@angular/core';
import { EcoFabSpeedDialComponent } from "@ecodev/fab-speed-dial";

@Component({
  selector: 'app-map-controls',
  templateUrl: './map-controls.component.html',
  styleUrls: ['./map-controls.component.scss']
})
export class MapControlsComponent implements OnInit {

  @ViewChild('leftDial') leftDial?: EcoFabSpeedDialComponent;
  @ViewChild('rightDial') rightDial?: EcoFabSpeedDialComponent;
  @ViewChild('leftDialBack') leftDialBack?: HTMLElement;

  dialBackVis: boolean = false;

  constructor() { }

  ngOnInit(): void {
  }

  action(a: string): void {

  }

  trigger(): void{
    this.leftDial?.toggle();
    this.rightDial?.toggle();
    this.dialBackVis = !this.dialBackVis;
  }

}
