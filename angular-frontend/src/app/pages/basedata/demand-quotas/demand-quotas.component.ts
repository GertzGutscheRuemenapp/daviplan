import { Component, OnInit } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { environment } from "../../../../environments/environment";

export const mockQuotas = ['aktuelle Quoten', 'erhöhte Nachfrage ab 2030', 'Name mit langem Text, um Umbruch zu erzwingen']

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements OnInit {
  quotas = mockQuotas;
  backend: string = environment.backend;
  infrastructures = mockInfrastructures;
  selectedService = mockInfrastructures[0].services[1];
  selectedQuota = this.quotas[0];
  statusQuoQuota: string | undefined = this.quotas[1];

  constructor() { }

  ngOnInit(): void {
  }

}
