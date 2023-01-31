import { AfterViewInit, Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { Infrastructure, Service, DemandRateSet, Gender, AgeGroup } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { DemandRateSetViewComponent } from "./demand-rate-set-view/demand-rate-set-view.component";
import { DemandTypes } from "../../../rest-interfaces";
import { BehaviorSubject } from "rxjs";
import { MatSelectionList } from "@angular/material/list";
import { showAPIError } from "../../../helpers/utils";

@Component({
  selector: 'app-demand-quotas',
  templateUrl: './demand-quotas.component.html',
  styleUrls: ['./demand-quotas.component.scss']
})
export class DemandQuotasComponent implements OnInit, AfterViewInit {
  @ViewChild('demandTypeCard') demandTypeCard?: InputCardComponent;
  @ViewChild('propertiesCard') propertiesCard?: InputCardComponent;
  @ViewChild('demandRateSetCard') demandRateSetCard?: InputCardComponent;
  @ViewChild('demandRateSetPreview') demandRateSetPreview?: DemandRateSetViewComponent;
  @ViewChild('propertiesEdit') propertiesEdit?: TemplateRef<any>;
  @ViewChild('demandSetSelection') demandSetSelection?: MatSelectionList;
  isLoading$ = new BehaviorSubject<boolean>(false);
  year?: number;
  years: number[] = [];
  genders: Gender[] = [];
  ageGroups: AgeGroup[] = [];
  infrastructures: Infrastructure[] = [];
  activeService?: Service;
  activeDemandRateSet?: DemandRateSet;
  editDemandRateSet?: DemandRateSet;
  demandTypes = DemandTypes;
  demandTypeForm: FormGroup;
  propertiesForm: FormGroup;
  demandRateSets: DemandRateSet[] = [];

  constructor(private restService: RestCacheService, private formBuilder: FormBuilder,
              private dialog: MatDialog, private http: HttpClient, private rest: RestAPI) {
    // make sure data requested herer is up-to-date
    this.restService.reset();
    this.demandTypeForm = this.formBuilder.group({
      demandType: new FormControl('1')
    });
    this.propertiesForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl('')
    });
  }

  ngOnInit() {
    this.isLoading$.next(true);
    this.restService.getYears().subscribe(years => {
      this.years = years;
      this.year = years[0];
    });
    this.restService.getGenders().subscribe(genders => this.genders = genders);
    this.restService.getAgeGroups().subscribe(ageGroups => this.ageGroups = ageGroups);
    this.restService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures || [];
      this.isLoading$.next(false);
      if (infrastructures.length === 0) return;
      const services = infrastructures[0].services || [];
      if (services.length > 0) {
        this.activeService = services[0];
        this.onServiceChange();
      }
    })
  }

  ngAfterViewInit(): void {
    this.demandRateSetPreview?.timeSlider?.valueChange.subscribe(year => this.year = year || undefined);
    this.setupDemandTypeCard();
    this.setupPropertiesCard();
    this.setupDemandRateSetCard();
  }

  setupDemandTypeCard(): void {
    this.demandTypeCard?.dialogOpened.subscribe(ok => {
      this.demandTypeForm.reset({
        demandType: String(this.activeService?.demandType)
      });
    })
    this.demandTypeCard?.dialogConfirmed.subscribe((ok)=>{
      this.demandTypeForm.markAllAsTouched();
      this.demandTypeForm.markAllAsTouched();
      if (this.demandTypeForm.invalid) return;
      let attributes: any = {
        demandType: this.demandTypeForm.value.demandType,
      }
      this.demandTypeCard?.setLoading(true);
      this.http.patch<Service>(`${this.rest.URLS.services}${this.activeService?.id}/`, attributes
      ).subscribe(service => {
        Object.assign(this.activeService!, service);
        this.demandRateSetPreview!.service = this.activeService;
        this.demandTypeCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.demandTypeCard?.setLoading(false);
      });
    })
  }

  setupPropertiesCard(): void {
    this.propertiesCard?.dialogOpened.subscribe(ok => {
      this.propertiesForm.reset({
        name: this.activeDemandRateSet?.name,
        description: this.activeDemandRateSet?.description,
      });
    })
    this.propertiesCard?.dialogConfirmed.subscribe((ok)=>{
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description
      }
      this.propertiesCard?.setLoading(true);
      this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/`, attributes
      ).subscribe(set => {
        Object.assign(this.activeDemandRateSet!, set);
        // trigger reload of demand rate card
        const activeDemandRateSet = this.activeDemandRateSet;
        this.activeDemandRateSet = undefined;
        setTimeout(() => {  this.activeDemandRateSet = activeDemandRateSet; }, 1);
        this.propertiesCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.propertiesCard?.setLoading(false);
      });
    })
  }

  setupDemandRateSetCard(): void {
    this.demandRateSetCard?.dialogConfirmed.subscribe((ok)=>{
      const attributes = { demandRates: this.editDemandRateSet?.demandRates.filter(dr => dr.value) }
      this.demandRateSetCard?.setLoading(true);
      this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/`, attributes
      ).subscribe(set => {
        Object.assign(this.activeDemandRateSet!, set);
        this.demandRateSetPreview!.demandRateSet = set;
        this.demandRateSetCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.demandRateSetCard?.setLoading(false);
      });
    })
    this.demandRateSetCard?.dialogClosed.subscribe(() => {
      this.editDemandRateSet = JSON.parse(JSON.stringify(this.activeDemandRateSet));
    })
  }

  createDemandRateSet(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Nachfragevariante',
        template: this.propertiesEdit,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(ok => {
      this.propertiesForm.reset();
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || '',
        service: this.activeService?.id
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<DemandRateSet>(this.rest.URLS.demandRateSets, attributes
      ).subscribe(set => {
        this.demandRateSets.push(set);
        this.activeDemandRateSet = set;
        this.onDemandRateSetChange();
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  cloneDemandRateSet(): void {
    if (!this.activeDemandRateSet) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Nachfragevariante klonen',
        template: this.propertiesEdit,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(ok => {
      let i = 2;
      let name = '';
      const existingNames = this.demandRateSets.map(drs => drs.name);
      while (true) {
        const newName = `${this.activeDemandRateSet!.name} (${i})`;
        if (existingNames.indexOf(newName) === -1){
          name = newName;
          break;
        }
        i += 1;
      }
      this.propertiesForm.reset({
        name: name,
        description: this.activeDemandRateSet!.description,
      });
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.propertiesForm.markAllAsTouched();
      if (this.propertiesForm.invalid) return;
      let attributes: any = {
        name: this.propertiesForm.value.name,
        description: this.propertiesForm.value.description || '',
        service: this.activeService?.id,
        demandRates: this.activeDemandRateSet?.demandRates
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<DemandRateSet>(this.rest.URLS.demandRateSets, attributes
      ).subscribe(set => {
        this.demandRateSets.push(set);
        this.activeDemandRateSet = set;
        this.onDemandRateSetChange();
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  deleteDemandRateSet(): void {
    if (!this.activeDemandRateSet)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Die Nachfragevariante wirklich entfernen?`,
        confirmButtonText: $localize`Variante entfernen`,
        message: `Es werden auch alle bereits definierten Nachfragewerte der Variante entfernt. <br><br> ${this.activeService?.name}`,
        value: this.activeDemandRateSet.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.demandRateSets}${this.activeDemandRateSet?.id}/?force=true`
        ).subscribe(() => {
          this.activeDemandRateSet = undefined;
          // other set might change on deletion of the default one
          this.onServiceChange({reset: true});
        },(error) => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  onServiceChange(options?: {reset?: boolean}): void {
    if (!this.activeService) return;
    this.activeDemandRateSet = undefined;
    this.isLoading$.next(true);
    this.restService.getDemandRateSets(this.activeService.id, {reset: options?.reset}).subscribe(sets => {
      this.demandRateSets = sets;
      // this.activeDemandRateSet = sets[0];
      // this.onDemandRateSetChange();
      this.isLoading$.next(false);
      // workaround: mat-selection always seems to select sth when adding options, even if nothing is defined
      // as selected
      this.demandSetSelection?.deselectAll();
    });
  }

  onDemandRateSetChange(): void {
    if(!this.activeDemandRateSet) return;
    // deep clone
    this.editDemandRateSet = JSON.parse(JSON.stringify(this.activeDemandRateSet));
  }

  setDefaultDemandRateSet(set: DemandRateSet): void {
    if (!set || set.isDefault) return;
    const attributes = { isDefault: true };
    this.http.patch<DemandRateSet>(`${this.rest.URLS.demandRateSets}${set.id}/`, attributes
    ).subscribe(ds => {
      this.demandRateSets.forEach(s => s.isDefault = false);
      set.isDefault = ds.isDefault;
    })
  }

  getTitle(demandType: number | undefined): string {
    switch(demandType) {
      case 1:
        return 'Nachfragequoten der ausgewählten Variante';
      case 2:
        return 'Nutzungshäufigkeiten der ausgewählten Variante';
      default:
    }
    return '';
  }
}
