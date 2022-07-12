import { Component, OnDestroy, OnInit } from '@angular/core';
import { Infrastructure, Service } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { Subscription } from "rxjs";

@Component({
  selector: 'app-service-select',
  templateUrl: './service-select.component.html',
  styleUrls: ['./service-select.component.scss']
})
export class ServiceSelectComponent implements OnInit, OnDestroy {
  infrastructures: Infrastructure[] = [];
  services: Service[] = [];
  subscriptions: Subscription[] = [];
  selectedService?: Service;
  selectedInfrastructure?: Infrastructure;

  constructor(public planningService: PlanningService) {
    this.planningService.getInfrastructures().subscribe( infrastructures => {
      this.infrastructures = infrastructures;
      this.services = [];
      this.infrastructures?.forEach(i => this.services = this.services.concat(i.services));
      this.planningService.activeInfrastructure$.subscribe(
        infrastructure => this.selectedInfrastructure = this.infrastructures?.find(i => i.id === infrastructure?.id));
      this.planningService.activeService$.subscribe(service => this.selectedService = service);
    })
  }

  ngOnInit(): void {
  }

  onInfrastructureChange() {
    this.planningService.activeInfrastructure$.next(this.selectedInfrastructure);
    this.planningService.activeService$.next(this.selectedInfrastructure?.services[0]);
  }

  onServiceChange() {
    this.planningService.activeService$.next(this.selectedService);
  }

  ngOnDestroy() {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
