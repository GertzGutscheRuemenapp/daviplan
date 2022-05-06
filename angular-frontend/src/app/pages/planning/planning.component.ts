import { Component, ElementRef, AfterViewInit, Renderer2, OnDestroy, ViewChild, TemplateRef } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { Observable } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { mockUsers } from "../login/users";
import { MatSelect } from "@angular/material/select";
import { RemoveDialogComponent } from "../../dialogs/remove-dialog/remove-dialog.component";
import { PlanningService } from "./planning.service";
import { LegendComponent } from "../../map/legend/legend.component";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { Infrastructure, PlanningProcess } from "../../rest-interfaces";
import { SettingsService } from "../../settings.service";
import { AuthService } from "../../auth.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../rest-api";
import { CookieService } from "../../helpers/cookies.service";

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
  users = mockUsers;
  mapControl?: MapControl;
  realYears?: number[];
  prognosisYears?: number[];
  infrastructures: Infrastructure[] = [];
  editProcessForm: FormGroup;
  Object = Object;

  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 39.9375em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private renderer: Renderer2,
              private elRef: ElementRef, private mapService: MapService, private dialog: MatDialog,
              public planningService: PlanningService, private settings: SettingsService,
              private auth: AuthService, private formBuilder: FormBuilder,
              private http: HttpClient, private rest: RestAPI, private cookies: CookieService) {
    this.editProcessForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl(''),
      allowSharedChange: new FormControl(false)
    });
  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    // a bit hacky
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'hidden');
    this.mapControl = this.mapService.get('planning-map');
    this.planningService.legend = this.legend;
    this.mapControl.mapDescription = 'Planungsprozess: xyz > Status Quo Fortschreibung <br> usw.';
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
    this.planningService.getInfrastructures().subscribe( infrastructures => {
      this.infrastructures = infrastructures;
    })

    this.planningService.getProcesses().subscribe(processes => {
      this.auth.getCurrentUser().subscribe(user => {
        if (!user) return;
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
    this.planningService.setReady(true);
  }

  ngOnDestroy(): void {
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'auto');
    this.mapControl?.destroy();
  }

  setProcess(id: number | undefined, options?: { persist: boolean }): void {
    let process = this.getProcess(id);
    this.activeProcess = process;
    if (options?.persist)
      this.cookies.set('planning-process', process?.id);
    this.planningService.activeProcess$.next(process);
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
        infoText: 'Platzhalter'
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editProcessForm.reset({
        allowSharedChange: false,
        description: '',
      });
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.editProcessForm.setErrors(null);
      // display errors for all fields even if not touched
      this.editProcessForm.markAllAsTouched();
      if (this.editProcessForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        name: this.editProcessForm.value.name,
        description: this.editProcessForm.value.description,
        allowSharedChange: this.editProcessForm.value.allowSharedChange
      };
      this.http.post<PlanningProcess>(this.rest.URLS.processes, attributes
      ).subscribe(process => {
        process.scenarios = [];
        this.myProcesses.push(process);
        dialogRef.close();
      },(error) => {
        this.editProcessForm.setErrors(error.error);
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
        infoText: 'Platzhalter'
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.editProcessForm.reset({
        name: process.name,
        description: process.description,
        allowSharedChange: process.allowSharedChange
      });
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.editProcessForm.setErrors(null);
      // display errors for all fields even if not touched
      this.editProcessForm.markAllAsTouched();
      if (this.editProcessForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        name: this.editProcessForm.value.name,
        description: this.editProcessForm.value.description,
        allowSharedChange: this.editProcessForm.value.allowSharedChange
      };
      this.http.patch<PlanningProcess>(`${this.rest.URLS.processes}${process.id}/`, attributes
      ).subscribe(resProcess => {
        process.name = resProcess.name;
        process.description = resProcess.description;
        process.allowSharedChange = resProcess.allowSharedChange;
        dialogRef.close();
      },(error) => {
        this.editProcessForm.setErrors(error.error);
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
        this.http.delete(`${this.rest.URLS.processes}${process.id}/`
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
          console.log('there was an error sending the query', error);
        });
      }
    });
  }
}
