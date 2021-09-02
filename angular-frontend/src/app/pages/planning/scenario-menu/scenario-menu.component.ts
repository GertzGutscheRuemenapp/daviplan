import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {

  scenarios: string[] = ['Szenario 1', 'Szenario 2']

  constructor() { }

  ngOnInit(): void {
  }

}
