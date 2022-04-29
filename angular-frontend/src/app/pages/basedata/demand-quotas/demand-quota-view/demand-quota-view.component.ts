import { Component, OnInit } from '@angular/core';
import { environment } from "../../../../../environments/environment";

@Component({
  selector: 'app-demand-quota-view',
  templateUrl: './demand-quota-view.component.html',
  styleUrls: ['./demand-quota-view.component.scss']
})
export class DemandQuotaViewComponent implements OnInit {
  backend: string = environment.backend;

  constructor() { }

  ngOnInit(): void {
  }

}
