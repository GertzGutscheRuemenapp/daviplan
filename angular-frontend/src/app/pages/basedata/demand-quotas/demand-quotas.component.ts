import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { environment } from "../../../../environments/environment";

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements OnInit {
  backend: string = environment.backend;
  infrastructures = mockInfrastructures;
  services = mockInfrastructures[1].services;
  selectedService = mockInfrastructures[1].services[1];
  quotas = ['aktuelle Quoten', 'erhöhte Nachfrage ab 2030', 'Name mit langem Text, um Umbruch zu erzwingen']
  selectedQuota = this.quotas[0];
  statusQuoQuota: string | undefined = this.quotas[1];

  constructor() { }

  ngOnInit(): void {
  }

}
