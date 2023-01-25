import {
  Component,
  ElementRef,
  AfterViewInit,
  Renderer2,
  OnDestroy,
  ViewChild,
  TemplateRef,
  ChangeDetectorRef
} from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { Observable, Subscription } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { MatSelect } from "@angular/material/select";
import { RemoveDialogComponent } from "../../dialogs/remove-dialog/remove-dialog.component";
import { PlanningService } from "./planning.service";
import { LegendComponent } from "../../map/legend/legend.component";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { Infrastructure, PlanningProcess, Scenario, User } from "../../rest-interfaces";
import { SettingsService } from "../../settings.service";
import { AuthService } from "../../auth.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { CookieService } from "../../helpers/cookies.service";
import { showAPIError } from "../../helpers/utils";

interface SharedUser extends User {
  shared?: boolean;
}
interface IncludedInfrastructure extends Infrastructure {
  included?: boolean;
}

const processInfoText = "<p>Geben Sie Ihrem Planungsprozess einen – möglichst kurzen – Namen (z.B. „Kitabedarfsplanung“) und eine kurze Beschreibung (z.B. „Bedarfsplanung für den Zeitraum 2024-2026“).</p>" +
  "<p>Wählen Sie anschließend aus, welche Infrastrukturbereiche Sie in diesem Planungsprozess bearbeiten wollen. Nur diese Infrastrukturbereiche sind innerhalb des Planungsprozesses sichtbar und können mit Hilfe von Auswertungen und Szenarien bearbeitet werden.</p>" +
  "<p>Legen Sie abschließend noch fest, welche anderen daviplan-Nutzer:innen Zugriff auf den Planungsprozess haben sollen. Mit dem Häkchen unten rechts können Sie festlegen, ob die ausgewählten Nutzer:innen die Szenarien des Planungsprozesses verändern können sollen. Wenn Sie diese Option deaktivieren, können die anderen Nutzer:innen nur Auswertungen vornehmen, aber keine Veränderungen (mehr) in den Szenarien (andere Einwohnerentwicklung, andere Nachfragequoten, andere Standort- und Kapazitätsstruktur, andere ÖPNV-Netze) vornehmen.</p>" +
  "<p>Sie können alle Eintragungen auch nachträglich noch verändern.</p>"

@Component({
  selector: 'app-planning',
  templateUrl: './planning.component.html',
  styleUrls: ['./planning.component.scss']
})
export class PlanningComponent implements AfterViewInit, OnDestroy {
  @ViewChild('processTemplate') processTemplate?: TemplateRef<any>;
  @ViewChild('processSelect') processSelect!: MatSelect;
  @ViewChild('planningLegend') legend?: LegendComponent;
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  faArrows = faArrowsAlt;
  myProcesses: PlanningProcess[] = [];
  sharedProcesses: PlanningProcess[] = [];
  activeProcess?: PlanningProcess;
  otherUsers: SharedUser[] = [];
  user?: User;
  mapControl?: MapControl;
  realYears?: number[];
  prognosisYears?: number[];
  allInfrastructures: IncludedInfrastructure[] = [];
  infrastructures: Infrastructure[] = [];
  baseScenario?: Scenario;
  editProcessForm: FormGroup;
  isLoading = true;
  mapDescription = '';
  subscriptions: Subscription[] = [];

  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 39.9375em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private renderer: Renderer2,
              private elRef: ElementRef, private mapService: MapService, private dialog: MatDialog,
              public planningService: PlanningService, private settings: SettingsService,
              private auth: AuthService, private formBuilder: FormBuilder, private cdref: ChangeDetectorRef,
              private http: HttpClient, private rest: RestAPI, private cookies: CookieService) {
    this.planningService.reset();
    this.editProcessForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl(''),
      allowSharedChange: new FormControl(false)
    });
    this.planningService.getInfrastructures().subscribe( infrastructures => this.allInfrastructures = infrastructures);
  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    // a bit hacky
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'hidden');
    this.mapControl = this.mapService.get('planning-map');
    this.planningService.legend = this.legend;
    // using "isLoading$ | async" in template causes NG0100, because service doesn't know about life cycle of this page
    // workaround: force change detection
    this.subscriptions.push(this.planningService.isLoading$.subscribe(isLoading => {
      this.isLoading = isLoading;
      this.cdref.detectChanges();
    }));
    // same as above
    this.mapControl.mapDescription$.subscribe(desc => {
      this.mapDescription = desc;
      this.cdref.detectChanges();
    });
    this.timeSlider?.onChange.subscribe(value => {
      this.planningService.year$.next(value);
      this.cookies.set('planning-year', value);
    })
    this.planningService.getRealYears().subscribe( years => {
      this.realYears = years;
      this.setSlider();
    })
    this.planningService.getPrognosisYears().subscribe( years => {
      this.prognosisYears = years;
      this.setSlider();
    })
    this.subscriptions.push(this.planningService.activeInfrastructure$.subscribe(infrastructure => {
      if (infrastructure) this.cookies.set(`planning-infrastructure-${this.activeProcess?.id}`, infrastructure?.id);
    }))
    this.subscriptions.push(this.planningService.activeService$.subscribe(service => {
      if (service) this.cookies.set(`planning-service-${this.activeProcess?.id}`, service?.id);
    }))
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      if (scenario && this.planningService.activeProcess)
        this.cookies.set(`planning-scenario-${this.planningService.activeProcess.id}`, scenario.id);
    }))

    this.planningService.getProcesses().subscribe(processes => {
      this.planningService.getBaseScenario().subscribe(scenario => {
        this.baseScenario = scenario;
        this.auth.getCurrentUser().subscribe(user => {
          this.user = user;
          if (!user) return;
          this.planningService.getUsers().subscribe(users => {
            this.otherUsers = users.filter(u => u.id != user.id);
          })
          processes.forEach(process => {
            if (process.owner === user.id)
              this.myProcesses.push(process);
            else
              this.sharedProcesses.push(process);
          })
          const processId = this.cookies.get('planning-process', 'number');
          if (processId) {
            this.setProcess(Number(processId));
          }
        })
      })
    })
  }

  setProcess(id: number | undefined, options?: { persist: boolean }): void {
    this.planningService.activeService$.next(undefined);
    this.mapControl?.setDescription('');
    let process = this.getProcess(id);
    this.activeProcess = process;
    const scenarioId = this.cookies.get(`planning-scenario-${process?.id}`, 'number');
    const scenario = process?.scenarios?.find(s => s.id === scenarioId) || this.baseScenario;
    if (options?.persist)
      this.cookies.set('planning-process', process?.id);
    this.planningService.activeProcess$.next(process);
    this.planningService.activeScenario$.next(scenario);
    this.planningService.getInfrastructures({ process: process }).subscribe( infrastructures => {
      this.infrastructures = infrastructures.filter(i => i.access === true);
      const infraId = this.cookies.get(`planning-infrastructure-${id}`, 'number');
      // process does not contain last selected infrastructure -> do not select it
      let activeInfrastructure = (infraId !== undefined && this.activeProcess && this.activeProcess.infrastructures.indexOf(infraId) >= 0)? this.infrastructures?.find(i => i.id === infraId): undefined;
      this.planningService.activeInfrastructure$.next(activeInfrastructure);
      const activeService = activeInfrastructure?.services.find(i => i.id === this.cookies.get(`planning-service-${id}`, 'number'));
      this.planningService.activeService$.next(activeService);
    })
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    this.timeSlider!.prognosisStart = this.prognosisYears[0] || 0;
    this.timeSlider!.years = this.realYears.concat(this.prognosisYears);
    const year = this.cookies.get('planning-year', 'number') || this.realYears[0];
    this.timeSlider!.value = year;
    this.planningService.year$.next(year);
    this.timeSlider!.draw();
  }

  getProcess(id: number | undefined): PlanningProcess | undefined {
    if (id === undefined) return;
    return this.myProcesses.concat(this.sharedProcesses).filter(process => process.id === id)[0];
  }

  onCreateProcess(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '600px',
      disableClose: false,
      data: {
        title: 'Planungsprozess erstellen',
        template: this.processTemplate,
        closeOnConfirm: false,
        confirmButtonText: 'Bestätigen',
        infoText: processInfoText
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editProcessForm.reset({
        allowSharedChange: false,
        description: '',
      });
      this.otherUsers.forEach(user => {
        user.shared = false;
      })
      this.allInfrastructures.forEach(infrastructure => {
        infrastructure.included = true;
      })
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.editProcessForm.markAllAsTouched();
      if (this.editProcessForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      const sharedUsers = this.otherUsers.filter(user => user.shared).map(user => user.id);
      const includedInfrastructures = this.allInfrastructures.filter(i => i.included).map(i => i.id);
      let attributes = {
        name: this.editProcessForm.value.name,
        description: this.editProcessForm.value.description,
        infrastructures: includedInfrastructures,
        allowSharedChange: this.editProcessForm.value.allowSharedChange,
        users: sharedUsers
      };
      this.http.post<PlanningProcess>(this.rest.URLS.processes, attributes
      ).subscribe(process => {
        process.scenarios = [];
        this.myProcesses.push(process);
        this.setProcess(process.id);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  editProcess(process: PlanningProcess): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '600px',
      disableClose: false,
      data: {
        title: 'Planungsprozess editieren',
        template: this.processTemplate,
        closeOnConfirm: false,
        confirmButtonText: 'Speichern',
        infoText: processInfoText
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editProcessForm.reset({
        name: process.name,
        description: process.description,
        allowSharedChange: process.allowSharedChange
      });
      this.otherUsers.forEach(user => {
        user.shared = (process.users.indexOf(user.id) > -1);
      })
      this.allInfrastructures.forEach(infrastructure => {
        infrastructure.included = (process.infrastructures && process.infrastructures.indexOf(infrastructure.id) > -1);
      })
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.editProcessForm.markAllAsTouched();
      if (this.editProcessForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      const sharedUsers = this.otherUsers.filter(user => user.shared).map(user => user.id);
      const includedInfrastructures = this.allInfrastructures.filter(i => i.included).map(i => i.id);
      let attributes = {
        name: this.editProcessForm.value.name,
        description: this.editProcessForm.value.description,
        allowSharedChange: this.editProcessForm.value.allowSharedChange,
        infrastructures: includedInfrastructures,
        users: sharedUsers
      };
      this.http.patch<PlanningProcess>(`${this.rest.URLS.processes}${process.id}/`, attributes
      ).subscribe(resProcess => {
        // window.location.reload();
        Object.assign(process, resProcess);
        this.setProcess(process.id);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  deleteProcess(process: PlanningProcess) {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '460px',
      data: {
        title: $localize`Den Planungsprozess wirklich entfernen?`,
        confirmButtonText: $localize`Planungsprozess entfernen`,
        value: process.name,
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.processes}${process.id}/?force=true`
        ).subscribe(res => {
          const idx = this.myProcesses.indexOf(process);
          if (idx > -1) {
            this.myProcesses.splice(idx, 1);
          }
          if (this.activeProcess === process) {
            this.activeProcess = undefined;
            this.setProcess(undefined, {persist: true});
          }
        },(error) => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  getProcessPopoverHTML(process?: PlanningProcess): string {
    if (!process) return '';
    let description = process.description? `<p><i>${process.description}</i></p>`: '';
    const infraNames = process.infrastructures.map(iId => this.allInfrastructures.find(i => i.id === iId)?.name);
    const access = process.infrastructures.map(iId => this.allInfrastructures.find(i => i.id === iId)?.access);
    description += `<p>Infrastrukturbereiche:
                      <ul>
                        ${(infraNames.length > 0)? infraNames.map((s, i) =>
                          (s === undefined)? '<li class="red">unbekannter Bereich (keine Zugriffsberechtigung!)</li>':
                            (!access[i])? `<li class="red"> ${s} (keine Zugriffsberechtigung!)</li>`:
                            `<li>${s}</li>`).join('')
                          : '-' }
                      </ul>
                    </p>`;
    if (process.owner === this.user?.id && process.users.length > 0) {
      const userNames = process.users.map(uId => this.getPrettyUserName(this.otherUsers.find(u => u.id === uId)));
      description += `<p>geteilt mit:
                        <ul>
                            ${userNames.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                      </p>`;
    }
    if (process.owner !== this.user?.id) {
      description += `<p>geteilt durch ${this.getPrettyUserName(this.otherUsers.find(u => u.id === process.owner))}</p>`;
      description += `<p><b>Änderungen an Szenarien ${process.allowSharedChange? 'erlaubt': 'nicht erlaubt'}</p></b>`;
    }
    return description;
  }

  getPrettyUserName(user?: User): string {
    if (!user) return '';
    let pretty = user.username;
    if (user.firstName.length > 0 || user.lastName.length > 0) {
      pretty += ` (${user.firstName}${(user.firstName.length > 0 && user.lastName.length > 0)? ' ': ''}${user.lastName})`;
    }
    return pretty;
  }

  ngOnDestroy() {
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'auto');
    this.mapControl?.destroy();
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
