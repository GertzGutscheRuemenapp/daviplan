import { Component, OnInit } from '@angular/core';

export const mockRouters = ['Deutschland 2020', 'SHK mit ÖPNV 2021', 'Dtl 2020 mit A13 Ausbau'];

@Component({
  selector: 'app-router-settings',
  templateUrl: './router-settings.component.html',
  styleUrls: ['./router-settings.component.scss']
})
export class RouterSettingsComponent implements OnInit {
  routers = mockRouters;
  selectedRouter = this.routers[0];

  constructor() { }

  ngOnInit(): void {
  }

}
