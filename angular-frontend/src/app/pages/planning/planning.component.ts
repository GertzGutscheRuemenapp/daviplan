import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-planning',
  templateUrl: './planning.component.html',
  styleUrls: ['./planning.component.scss']
})
export class PlanningComponent implements OnInit {
  selectedItem: String = '';

  constructor() { }

  ngOnInit(): void {
  }

  public onMapReady(event:any) {
    console.log("Map Ready")
  }
}
