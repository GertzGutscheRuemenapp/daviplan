import { Component, OnInit, ViewChildren, QueryList, ElementRef, ViewChild, TemplateRef, Input } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { mockQuotas } from "../../basedata/demand-quotas/demand-quotas.component";
import { mockPrognoses } from "../../basedata/prognosis-data/prognosis-data.component";
import { environment } from "../../../../environments/environment";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { PlanningService } from "../planning.service";
import { PlanningProcess, Scenario } from "../../../rest-interfaces";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";

const baseScenario: Scenario = {
  id: -1,
  name: 'Status Quo Fortschreibung',
  planningProcess: -1,
  modevariants: [],
  demandratesets: []
}

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {
  @Input() domain: string = '';
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  baseScenario = baseScenario;
  scenarios: Scenario[] = [];
  activeScenario: Scenario = baseScenario;
  @ViewChild('editScenario') editScenarioTemplate?: TemplateRef<any>;
  @ViewChild('supplyScenarioTable') supplyScenarioTableTemplate?: TemplateRef<any>;
  @ViewChild('demandPlaceholderTable') demandPlaceholderTemplate?: TemplateRef<any>;
  @ViewChild('demandQuotaDialog') demandQuotaTemplate?: TemplateRef<any>;
  quotas = mockQuotas;
  prognoses = mockPrognoses;
  backend: string = environment.backend;
  editScenarioForm: FormGroup;
  process?: PlanningProcess;

  constructor(private dialog: MatDialog, private planningService: PlanningService,
              private formBuilder: FormBuilder, private http: HttpClient, private rest: RestAPI) {
    this.planningService.activeProcess$.subscribe(process => {
      this.onProcessChange(process);
    })
    this.editScenarioForm = this.formBuilder.group({
      scenarioName: new FormControl('')
    });
  }

  ngOnInit(): void {
  }

  toggleScenario(scenario: Scenario): void {
    // if (event.target !== event.currentTarget) return;
    // let a = (event.target as Element).attributes;
    // this.activeScenario = ((event.target as Element).attributes as any)['data-value'].value;
    this.activeScenario = scenario;
    this.scenarioCards?.forEach((card: ElementRef) => {
      let el = card.nativeElement;
      if (el.attributes['data-value'].nodeValue === this.activeScenario)
        el.classList.add('active');
      else
        el.classList.remove('active');
    });
  }

  onProcessChange(process: PlanningProcess | undefined): void {
    this.process = process;
    this.scenarios = (process)? [baseScenario].concat(process.scenarios || []): [];
    this.activeScenario = baseScenario;
  }

  onDeleteScenario(): void {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Das Szenario wirklich entfernen?`,
        confirmButtonText: $localize`Szenario entfernen`,
        value: this.activeScenario.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.scenarios}${this.activeScenario.id}/`
        ).subscribe(res => {
          const idx = this.process!.scenarios!.indexOf(this.activeScenario);
          if (idx >= 0) {
            this.process!.scenarios!.splice(idx, 1);
            this.scenarios = [baseScenario].concat(this.process!.scenarios!);
          }
          this.activeScenario = baseScenario;
        }, error => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }

  onCreateScenario(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Szenario erstellen`,
        // confirmButtonText: $localize`erstellen`,
        template: this.editScenarioTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editScenarioForm.reset();
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.editScenarioForm.markAllAsTouched();
      if (this.editScenarioForm.invalid) return;
      dialogRef.componentInstance.isLoading = true;
      let attributes = {
        name: this.editScenarioForm.value.scenarioName,
        planningProcess: this.process!.id
      };
      this.http.post<Scenario>(this.rest.URLS.scenarios, attributes
      ).subscribe(scenario => {
        if(!this.process!.scenarios) this.process!.scenarios = []
        this.process!.scenarios.push(scenario);
        this.scenarios.push(scenario);
      },(error) => {
        dialogRef.componentInstance.isLoading = false;
      });
    });
  }

  onEditScenario(): void {
    if(!this.activeScenario) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Szenario umbenennen`,
        // confirmButtonText: $localize`umbenennen`,
        template: this.editScenarioTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editScenarioForm.reset({
        scenarioName: this.activeScenario.name
      });
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.editScenarioForm.markAllAsTouched();
      if (this.editScenarioForm.invalid) return;
      dialogRef.componentInstance.isLoading = true;
      let attributes = {
        name: this.editScenarioForm.value.scenarioName
      };
      this.http.patch<Scenario>(`${this.rest.URLS.scenarios}${this.activeScenario.id}/`, attributes
      ).subscribe(scenario => {
        this.activeScenario.name = scenario.name;
      },(error) => {
        dialogRef.componentInstance.isLoading = false;
      });
    });
  }

  onShowSupplyTable(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Übersicht der Änderungen`,
        // confirmButtonText: $localize`umbenennen`,
        template: this.supplyScenarioTableTemplate,
        hideConfirmButton: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

  onShowDemandPlaceholder(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        // title: $localize``,
        // confirmButtonText: $localize`umbenennen`,
        template: this.demandPlaceholderTemplate,
        hideConfirmButton: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

  onShowDemandQuotaSet(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '900px',
      data: {
        title: $localize`Nachfragequoten-Set: [Name]`,
        // confirmButtonText: $localize`umbenennen`,
        template: this.demandQuotaTemplate,
        hideConfirmButton: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }
}
