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
  activeInfrastructures: Infrastructure[] = [];
  services: Service[] = [];
  subscriptions: Subscription[] = [];
  selectedService?: Service;
  selectedInfrastructure?: Infrastructure;

  constructor(public planningService: PlanningService) {
    this.planningService.getInfrastructures().subscribe( infrastructures => {
      this.activeInfrastructures = this.infrastructures = infrastructures.filter(i => (i.services.length > 0));
      this.services = [];
      this.infrastructures?.forEach(i => this.services = this.services.concat(i.services));
      this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(
        infrastructure => this.selectedInfrastructure = this.activeInfrastructures?.find(i => i.id === infrastructure?.id)));
      this.subscriptions.push(this.planningService.activeService$.subscribe(service => this.selectedService = service));
      this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
          this.activeInfrastructures = process? this.infrastructures.filter(i => process.infrastructures!.indexOf(i.id) > -1): [];
      }))
    })
  }

  ngOnInit(): void { }

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
