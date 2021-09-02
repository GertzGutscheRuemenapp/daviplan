import { Component, OnInit } from '@angular/core';
import { FormControl } from "@angular/forms";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements OnInit{
  activeInfrastructure: string = '';
  constructor() {}
  showScenarioMenu: boolean = false;

  ngOnInit(): void {
  }

  toggleScenarioMenu(): void{
    this.showScenarioMenu = !this.showScenarioMenu;
    console.log(this.showScenarioMenu)
  }
}
