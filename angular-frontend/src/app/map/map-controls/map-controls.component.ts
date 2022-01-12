import { Component, Input, OnInit, ViewChild } from '@angular/core';
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
  @Input() showOnHover?: boolean = false;

  expanded: boolean = false;

  constructor() { }

  ngOnInit(): void {
  }

  action(a: string): void {

  }

  toggle(): void {
    this.leftDial?.toggle();
    this.rightDial?.toggle();
    this.expanded = !this.expanded;
  }

}
