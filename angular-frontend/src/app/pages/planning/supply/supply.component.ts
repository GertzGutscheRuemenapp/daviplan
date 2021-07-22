import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

  public onMapReady(event:any) {
    console.log("Map Ready")
  }
}
