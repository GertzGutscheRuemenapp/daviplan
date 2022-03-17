import { Component, Input, OnInit } from '@angular/core';
import { Place, Scenario, Service } from "../../../rest-interfaces";

@Component({
  selector: 'app-service-filter',
  templateUrl: './service-filter.component.html',
  styleUrls: ['./service-filter.component.scss']
})
export class ServiceFilterComponent implements OnInit {
  @Input() services!: Service[];
  @Input() places!: Place[];
  @Input() scenario!: Scenario;
  @Input() year?: number;

  constructor() { }

  ngOnInit(): void {
  }

}
