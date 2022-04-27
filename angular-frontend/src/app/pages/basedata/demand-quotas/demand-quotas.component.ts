import { AfterViewInit, Component } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { Infrastructure, Service } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";

export const mockQuotas = ['aktuelle Quoten', 'erhöhte Nachfrage ab 2030', 'Name mit langem Text, um Umbruch zu erzwingen']

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements AfterViewInit {
  quotas = mockQuotas;
  backend: string = environment.backend;
  infrastructures: Infrastructure[] = [];
  selectedService?: Service;
  activeService?: Service;
  selectedQuota = this.quotas[0];
  statusQuoQuota: string | undefined = this.quotas[1];

  constructor(private restService: RestCacheService) { }

  ngAfterViewInit(): void {
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures || [];
      if (infrastructures.length === 0) return;
      const services = infrastructures[0].services || [];
      if (services.length > 0) {
        this.activeService = services[0];
        this.onServiceChange();
      }
    })
  }

  onServiceChange(): void {

  }

}
