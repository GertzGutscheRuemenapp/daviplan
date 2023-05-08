import {
  Component,
  OnInit,
  ViewChildren,
  QueryList,
  ElementRef,
  ViewChild,
  TemplateRef,
  Input,
  OnDestroy
} from '@angular/core';
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
  Service, TotalCapacityInScenario,
  TransportMode, User
} from "../../../rest-interfaces";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { CookieService } from "../../../helpers/cookies.service";
import { showAPIError } from "../../../helpers/utils";
import { AuthService } from "../../../auth.service";
import { Subscription } from "rxjs";
import { map } from "rxjs/operators";

interface DiffCapacity extends TotalCapacityInScenario{
  diffCapacity: number,
  diffPlaces: number
}

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']//, '../../../elements/side-toggle/side-toggle.component.scss']
})
export class ScenarioMenuComponent implements OnInit, OnDestroy {
  @Input() domain!: 'demand' | 'reachabilities' | 'rating' | 'supply';
  @Input() helpText = '';
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  @ViewChild('editScenarioTemplate') editScenarioTemplate?: TemplateRef<any>;
  @ViewChild('supplyScenarioTable') supplyScenarioTableTemplate?: TemplateRef<any>;
  @ViewChild('demandPlaceholderTable') demandPlaceholderTemplate?: TemplateRef<any>;
  @ViewChild('demandQuotaDialog') demandQuotaTemplate?: TemplateRef<any>;
  baseScenario?: Scenario;
  scenarios: Scenario[] = [];
  activeScenario?: Scenario;
  backend: string = environment.backend;
  editScenarioForm: FormGroup;
  process?: PlanningProcess;
  user?: User;
  processEditable = false;
  demandRateSets: DemandRateSet[] = [];
  transitVariants: ModeVariant[] = [];
  prognoses: Prognosis[] = [];
  year?: number;
  totalCapacities: Record<number, DiffCapacity> = {};
  service?: Service;
  subscriptions: Subscription[] = [];
  inputErrors: string[] = [];
  realYears: number[] = [];

  constructor(private dialog: MatDialog, public planningService: PlanningService, private cookies: CookieService,
              private formBuilder: FormBuilder, private http: HttpClient, private rest: RestAPI, private auth: AuthService) {
    this.auth.getCurrentUser().subscribe(user => {
      this.user = user;
      this.subscriptions.push(this.planningService.activeProcess$.subscribe(process => {
        this.processEditable = (process?.owner === this.user?.id) || !!process?.allowSharedChange;
        this.planningService.getBaseScenario().subscribe(scenario => {
          this.baseScenario = scenario;
          this.onProcessChange(process);
        });
      }))
    })
    this.planningService.getRealYears().subscribe(years => {
      this.realYears = years;
    });
    this.planningService.getPrognoses().subscribe(pr => this.prognoses = pr);
    this.subscriptions.push(this.planningService.scenarioChanged.subscribe(scenario => {
      this.verifyScenarioInputs();
    }));
    this.subscriptions.push(this.planningService.capacitiesChanged.subscribe(() => {
      this.updateTotalCapacities({ reset: true });
    }));
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      if (scenario)
        this.setScenario(scenario, { silent: true });
      this.verifyScenarioInputs();
    }));
    this.editScenarioForm = this.formBuilder.group({
      scenarioName: new FormControl('')
    });
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      this.service= service;
      this.onServiceChange(service);
    }));
    this.subscriptions.push(this.planningService.year$.subscribe(year => {
      this.year = year;
      this.verifyScenarioInputs();
      if (this.domain==="supply"){
        this.updateTotalCapacities();
      }
    }));
  }

  ngOnInit(): void {
    this.onServiceChange(this.planningService.activeService);
  }

  onServiceChange(service: Service | undefined): void {
    switch (this.domain) {
      case 'supply':
        this.updateTotalCapacities();
        this.verifyScenarioInputs();
        break;
      case 'demand':
        if (!service) return;
        this.planningService.getDemandRateSets(service.id).subscribe(dr => {
          this.demandRateSets = dr;
          this.verifyScenarioInputs();
        });
        break;
      case 'reachabilities':
        this.planningService.getModeVariants().subscribe(modeVariants => {
          this.transitVariants = modeVariants.filter(v => v.mode === TransportMode.TRANSIT);
          this.verifyScenarioInputs();
        });
        break;
      case 'rating':
        this.planningService.getModeVariants().subscribe(modeVariants => this.transitVariants = modeVariants.filter(v => v.mode === TransportMode.TRANSIT));
        if (!service) return;
        this.planningService.getDemandRateSets(service.id).subscribe(dr => {
          this.demandRateSets = dr;
          this.verifyScenarioInputs();
        });
        break;
      default:
        break;
    }
  }

  updateTotalCapacities(options?:{scenario?: Scenario, reset?: boolean} ): void{
    if (!options?.scenario)
      this.totalCapacities = {};
    if (!this.service || !this.year) return;
    this.planningService.getTotalCapactities(this.year, this.service,{scenario:options?.scenario, planningProcess: this.planningService.activeProcess, reset:options?.reset}).subscribe(cap => {
      const baseCap = cap.find(scen => scen.scenarioId === 0) || this.totalCapacities[0];
      if (!baseCap) return;
      cap.forEach(scen => {
        this.totalCapacities[scen.scenarioId] = {
          scenarioId: scen.scenarioId,
          totalCapacity: scen.totalCapacity,
          nPlaces: scen.nPlaces,
          diffCapacity: (scen.totalCapacity || 0) - (baseCap.totalCapacity || 0),
          diffPlaces: (scen.nPlaces || 0) - (baseCap.nPlaces || 0)
        }
      });
    });
  }

  getActiveDemandRateSet(scenario: Scenario): DemandRateSet | undefined {
    const id = scenario.demandrateSets.find(dr => dr.service === this.planningService.activeService?.id)?.demandrateset;
    return this.demandRateSets.find(dr => dr.id === id);
  }

  setScenario(scenario: Scenario, options?: { silent?: boolean }): void {
    if (this.activeScenario?.id === scenario.id) return;
    this.activeScenario = scenario;
    if (!options?.silent)
      this.planningService.activeScenario$.next(scenario);
    else
      this.verifyScenarioInputs();
  }

  onProcessChange(process: PlanningProcess | undefined): void {
    this.process = process;
    this.scenarios = (process)? [this.baseScenario!].concat(process.scenarios || []): [];
  }

  deleteScenario(scenario: Scenario): void {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Das Szenario wirklich entfernen?`,
        confirmButtonText: $localize`Szenario entfernen`,
        value: scenario.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.scenarios}${scenario.id}/?force=true`
        ).subscribe(res => {
          const idx = this.process!.scenarios!.indexOf(scenario);
          if (idx >= 0) {
            this.process!.scenarios!.splice(idx, 1);
            this.scenarios = [this.baseScenario!].concat(this.process!.scenarios!);
          }
          if (scenario.id === this.activeScenario?.id)
            this.activeScenario = this.baseScenario;
        }, error => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  onCreateScenario(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      panelClass: 'absolute',
      data: {
        title: $localize`Szenario erstellen`,
        // confirmButtonText: $localize`erstellen`,
        template: this.editScenarioTemplate,
        closeOnConfirm: false
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
        this.planningService.scenarioChanged.emit(scenario);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  editScenario(scenario: Scenario): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      panelClass: 'absolute',
      data: {
        title: $localize`Szenario umbenennen`,
        // confirmButtonText: $localize`umbenennen`,
        template: this.editScenarioTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editScenarioForm.reset({
        scenarioName: scenario.name
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
      ).subscribe(scen => {
        scenario.name = scen.name;
        this.planningService.activeScenario$.next(scenario);
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  onShowSupplyTable(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      panelClass: 'absolute',
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
      panelClass: 'absolute',
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
    const demandRateSet = this.getActiveDemandRateSet(scenario!);
    if (!demandRateSet) return;
    this.planningService.getRealYears().subscribe(realYears => {
      this.planningService.getPrognosisYears().subscribe(prognosisYears => {
        this.planningService.getGenders().subscribe(genders => {
          this.planningService.getAgeGroups().subscribe(ageGroups => {
            const service = this.planningService.activeService;
            const dialogRef = this.dialog.open(ConfirmDialogComponent, {
              width: '100%',
              panelClass: 'absolute',
              data: {
                title: 'Nachfragequoten',
                subtitle: `Leistung "${service?.name}" / Variante "${demandRateSet?.name}"`,
                // confirmButtonText: $localize`umbenennen`,
                template: this.demandQuotaTemplate,
                context: {
                  years: realYears.concat(prognosisYears),
                  year: this.year,
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

  getActiveTransitVariant(scenario: Scenario): ModeVariant | undefined{
    const mv = scenario.modeVariants.find(v => v.mode === TransportMode.TRANSIT);
    if (!mv) return;
    return this.transitVariants.find(tv => tv.id === mv.variant);
  }

  getActivePrognosis(scenario: Scenario): Prognosis | undefined{
    return this.prognoses.find(p => p.id === scenario.prognosis);
  }

  private patchScenarioSetting(scenario: Scenario, body: any): void { //: Observable<Scenario> {
    const url = `${this.rest.URLS.scenarios}${scenario.id}/`;
    this.http.patch<Scenario>(url, body).subscribe(scen => {
      Object.assign(scenario, scen);
      this.planningService.clearCache(scenario.id.toString());
      this.planningService.activeScenario$.next(scenario);
      this.verifyScenarioInputs();
    });
  }

  /**
   * verify inputs of active scenario and append occuring missing or faulty inputs to inputErrors
   */
  verifyScenarioInputs(): void {
    this.inputErrors = [];
    if (!this.activeScenario) {
      this.inputErrors.push('Kein Szenario ausgewählt');
      return;
    }
    // supply domain has no inputs
    if (this.domain === 'supply') return;
    if (this.domain === 'demand' || this.domain === 'rating') {
      // service has demand and no demand rate set selected
      if (this.planningService.activeService && this.planningService.activeService?.demandType !== 3 && !this.getActiveDemandRateSet(this.activeScenario)) {
        this.inputErrors.push('Keine Nachfragequote ausgewählt');
      }
      // prognosis year and no prognosis selected
      if (this.year && this.realYears.indexOf(this.year) < 0 && !this.activeScenario.prognosis) {
        this.inputErrors.push('Keine Einwohnerentwicklung ausgewählt');
      }
    }
  };

  ngOnDestroy() {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
