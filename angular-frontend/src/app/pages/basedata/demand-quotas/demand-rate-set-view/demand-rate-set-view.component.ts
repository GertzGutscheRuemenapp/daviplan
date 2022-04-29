import { Component, Input, OnInit } from '@angular/core';
import { environment } from "../../../../../environments/environment";
import { DemandRateSet } from "../../../../rest-interfaces";

@Component({
  selector: 'app-demand-rate-set-view',
  templateUrl: './demand-rate-set-view.component.html',
  styleUrls: ['./demand-rate-set-view.component.scss']
})
export class DemandRateSetViewComponent implements OnInit {
  backend: string = environment.backend;
  _years: number[] = [];
  _demandRateSet?: DemandRateSet;

  @Input() set years(years: number[]) {
    console.log(years)
    this._years = years;
}
  @Input() set demandRateSet(set: DemandRateSet) {
    console.log(set.name)
    this._demandRateSet = set;
  }

  constructor() { }

  ngOnInit(): void {
  }

}
