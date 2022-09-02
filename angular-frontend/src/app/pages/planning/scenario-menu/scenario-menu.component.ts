import { Component, OnInit, ViewChildren, QueryList, ElementRef, ViewChild, TemplateRef, Input } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { environment } from "../../../../environments/environment";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { PlanningService } from "../planning.service";
import {
  DemandRateSet, ModeVariant,
  Network,
  PlanningProcess,
  Prognosis,
  Scenario,
  Service,
  TransportMode
} from "../../../rest-interfaces";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { CookieService } from "../../../helpers/cookies.service";

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {
  @Input() domain!: 'demand' | 'reachabilities' | 'rating' | 'supply';
  @Input() helpText = '';
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  @ViewChild('editScenario') editScenarioTemplate?: TemplateRef<any>;
  @ViewChild('supplyScenarioTable') supplyScenarioTableTemplate?: TemplateRef<any>;
  @ViewChild('demandPlaceholderTable') demandPlaceholderTemplate?: TemplateRef<any>;
  @ViewChild('demandQuotaDialog') demandQuotaTemplate?: TemplateRef<any>;
  baseScenario?: Scenario;
  scenarios: Scenario[] = [];
  activeScenario?: Scenario;
  backend: string = environment.backend;
  editScenarioForm: FormGroup;
  process?: PlanningProcess;
  demandRateSets: DemandRateSet[] = [];
  transitVariants: ModeVariant[] = [];
  prognoses: Prognosis[] = [];

  constructor(private dialog: MatDialog, public planningService: PlanningService, private cookies: CookieService,
              private formBuilder: FormBuilder, private http: HttpClient, private rest: RestAPI) {
    this.planningService.activeProcess$.subscribe(process => {
      this.planningService.getBaseScenario().subscribe(scenario => {
        this.baseScenario = scenario;
        this.onProcessChange(process);
      });
    })
    this.planningService.activeScenario$.subscribe(scenario => {
       if (scenario)
         this.setScenario(scenario, {silent: true});
    })
    this.editScenarioForm = this.formBuilder.group({
      scenarioName: new FormControl('')
    });
    this.planningService.activeService$.subscribe(service => this.onServiceChange(service));
    this.planningService.getPrognoses().subscribe(pr => this.prognoses = pr)
  }

  ngOnInit(): void {
    this.onServiceChange(this.planningService.activeService);
  }

  onServiceChange(service: Service | undefined): void {
    if (!service) return;
    switch (this.domain) {
      case 'supply':
        break;
      case 'demand':
        this.planningService.getDemandRateSets(service.id).subscribe(dr => { this.demandRateSets = dr; });
        break;
      case 'reachabilities':
        this.planningService.getModeVariants().subscribe(modeVariants => this.transitVariants = modeVariants.filter(v => v.mode === TransportMode.TRANSIT));
        break;
      case 'rating':
        this.planningService.getDemandRateSets(service.id).subscribe(dr => { this.demandRateSets = dr; });
        this.planningService.getModeVariants().subscribe(modeVariants => this.transitVariants = modeVariants.filter(v => v.mode === TransportMode.TRANSIT));
        break;
      default:
        break;
    }
  }

  getDemandRateSet(scenario: Scenario): DemandRateSet | undefined {
    const id = scenario.demandrateSets.find(dr => dr.service === this.planningService.activeService?.id)?.demandrateset;
    return this.demandRateSets.find(dr => dr.id === id);
  }

  setScenario(scenario: Scenario, options?: { silent?: boolean }): void {
    if (this.activeScenario === scenario) return;
    this.activeScenario = scenario;
    if (!options?.silent)
      this.planningService.activeScenario$.next(scenario);
  }

  onProcessChange(process: PlanningProcess | undefined): void {
    this.process = process;
    this.scenarios = (process)? [this.baseScenario!].concat(process.scenarios || []): [];
  }

  onDeleteScenario(): void {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Das Szenario wirklich entfernen?`,
        confirmButtonText: $localize`Szenario entfernen`,
        value: this.activeScenario!.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.scenarios}${this.activeScenario!.id}/?force=true/`
        ).subscribe(res => {
          const idx = this.process!.scenarios!.indexOf(this.activeScenario!);
          if (idx >= 0) {
            this.process!.scenarios!.splice(idx, 1);
            this.scenarios = [this.baseScenario!].concat(this.process!.scenarios!);
          }
          this.activeScenario = this.baseScenario;
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
      dialogRef.componentInstance.isLoading$.next(true);
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
        dialogRef.componentInstance.isLoading$.next(false);
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
        scenarioName: this.activeScenario!.name
      });
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.editScenarioForm.markAllAsTouched();
      if (this.editScenarioForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        name: this.editScenarioForm.value.scenarioName
      };
      this.http.patch<Scenario>(`${this.rest.URLS.scenarios}${this.activeScenario!.id}/`, attributes
      ).subscribe(scenario => {
        this.activeScenario!.name = scenario.name;
      },(error) => {
        dialogRef.componentInstance.isLoading$.next(false);
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
    const scenario = this.planningService.activeScenario;
    const demandRateSet = this.getDemandRateSet(scenario!);
    if (!demandRateSet) return;
    this.planningService.getRealYears().subscribe(realYears => {
      this.planningService.getPrognosisYears().subscribe(prognosisYears => {
        this.planningService.getGenders().subscribe(genders => {
          this.planningService.getAgeGroups().subscribe(ageGroups => {
            const service = this.planningService.activeService;
            const dialogRef = this.dialog.open(ConfirmDialogComponent, {
              width: '900px',
              data: {
                title: 'Nachfragequoten',
                subtitle: `Leistung "${service?.name}" / Set "${demandRateSet?.name}"`,
                // confirmButtonText: $localize`umbenennen`,
                template: this.demandQuotaTemplate,
                context: {
                  years: realYears.concat(prognosisYears),
                  scenario: scenario,
                  demandRateSet: demandRateSet,
                  genders: genders,
                  ageGroups: ageGroups,
                  service: service
                },
                hideConfirmButton: true
              }
            });
            dialogRef.afterClosed().subscribe((confirmed: boolean) => {
            });
          })
        })
      })
    })
  }

  onDemandRateChange(scenario: Scenario, demandRateSet: DemandRateSet): void {
    if (!this.planningService.activeService) return;
    const serviceId = this.planningService.activeService.id;
    const body: any = { demandrateSets: [{ service: serviceId, demandrateset: demandRateSet.id }] };
    this.patchScenarioSetting(scenario, body);
  }

  onPrognosisChange(scenario: Scenario, prognosisId: number): void {
    const body: any = { prognosis: prognosisId };
    this.patchScenarioSetting(scenario, body);
  }

  onTransitChange(scenario: Scenario, variant: ModeVariant): void {
    const body: any = { modeVariants: [{ mode: TransportMode.TRANSIT, variant: variant.id }] };
    this.patchScenarioSetting(scenario, body);
  }

  getTransitVariant(scenario: Scenario): ModeVariant | undefined{
    const mv = scenario.modeVariants.find(v => v.mode === TransportMode.TRANSIT);
    if (!mv) return;
    return this.transitVariants.find(tv => tv.id === mv.variant);
  }

  private patchScenarioSetting(scenario: Scenario, body: any): void { //: Observable<Scenario> {
    const url = `${this.rest.URLS.scenarios}${scenario.id}/`;
    this.http.patch<Scenario>(url, body).subscribe(scen => {
      Object.assign(scenario, scen);
      this.planningService.clearCache(scenario.id.toString());
      this.planningService.activeScenario$.next(scenario);
    });
  }
}
