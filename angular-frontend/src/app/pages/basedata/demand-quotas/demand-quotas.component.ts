import { AfterViewInit, Component, ViewChild } from '@angular/core';
import { environment } from "../../../../environments/environment";
import { Infrastructure, Service, DemandRateSet } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";

const demandTypes = {
  1: ['Nachfragequote', '(z.B. 30% der Kinder einer Altersklasse)'],
  2: ['Nutzungshäufigkeit pro Einwohner', '(z.B. 15 Arztbesuche pro Jahr.)'],
  3: ['Einwohnerzahl insgesamt', '(z.B. Brandschutz oder Einzelhandelsversorgung, keine weitere Angaben erforderlich)']
}

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements AfterViewInit {
  @ViewChild('demandTypeCard') demandTypeCard?: InputCardComponent;
  backend: string = environment.backend;
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  activeDemandRateSet?: DemandRateSet;
  demandTypes = demandTypes;
  demandTypeForm: FormGroup;
  demandRateSets: DemandRateSet[] = [];
  demandRateSetCache: Record<number, DemandRateSet[]> = {};

  constructor(private restService: RestCacheService, private formBuilder: FormBuilder,
              private http: HttpClient, private rest: RestAPI) {
    this.demandTypeForm = this.formBuilder.group({
      demandType: new FormControl('1')
    });
  }

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
    this.setupDemandTypeCard();
  }

  setupDemandTypeCard(): void {
    this.demandTypeCard?.dialogOpened.subscribe(ok => {
      this.demandTypeForm.reset({
        demandType: String(this.activeService?.demandType)
      });
    })
    this.demandTypeCard?.dialogConfirmed.subscribe((ok)=>{
      this.demandTypeForm.setErrors(null);
      this.demandTypeForm.markAllAsTouched();
      if (this.demandTypeForm.invalid) return;
      let attributes: any = {
        demandType: this.demandTypeForm.value.demandType,
      }
      this.demandTypeCard?.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService?.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.demandTypeCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.demandTypeForm.setErrors(error.error);
        this.demandTypeCard?.setLoading(false);
      });
    })
  }

  onServiceChange(): void {
    if (!this.activeService) return;
    const demandRateSets = this.demandRateSetCache[this.activeService!.id];
    if (demandRateSets) {
      this.demandRateSets = demandRateSets;
      this.activeDemandRateSet = demandRateSets[0];
      this.onDemandRateSetChange();
    }
    else
      this.restService.getDemandRateSets(this.activeService.id).subscribe(sets => {
        this.demandRateSetCache[this.activeService!.id] = sets;
        this.demandRateSets = sets;
        this.activeDemandRateSet = sets[0];
        this.onDemandRateSetChange();
      });
  }

  onDemandRateSetChange(): void {

  }

  setDefaultDemandRateSet(): void {

  }
}
