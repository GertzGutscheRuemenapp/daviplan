import { Component, ElementRef, AfterViewInit, Renderer2, OnDestroy, ViewChild, TemplateRef } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { Observable } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { mockUsers, User } from "../login/users";
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
  showScenarioMenu: boolean = false;
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
              private http: HttpClient, private rest: RestAPI) {
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
    this.timeSlider?.valueChanged.subscribe(value => {
      this.planningService.year$.next(value);
    })
    this.planningService.realYears$.subscribe( years => {
      this.realYears = years;
      this.setSlider();
    })
    this.planningService.prognosisYears$.subscribe( years => {
      this.prognosisYears = years;
      this.setSlider();
    })
    this.planningService.infrastructures$.subscribe( infrastructures => {
      this.infrastructures = infrastructures;
    })
    this.planningService.processes$.subscribe(processes => {
      this.auth.getCurrentUser().subscribe(user => {
        if (!user) return;
        processes.forEach(process => {
          if (process.owner === user.id)
            this.myProcesses.push(process);
          else
            this.sharedProcesses.push(process);
        })
      })
    })
    this.planningService.setReady(true);
  }

  ngOnDestroy(): void {
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'auto');
    this.mapControl?.destroy();
  }

  onProcessChange(id: number): void {
    if (id === undefined) return;
    let process = this.getProcess(id);
    this.activeProcess = process;
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    this.timeSlider!.prognosisStart = this.prognosisYears[0] || 0;
    this.timeSlider!.years = this.realYears.concat(this.prognosisYears);
    this.timeSlider!.value = this.realYears[0];
    this.planningService.year$.next(this.realYears[0]);
    this.timeSlider!.draw();
  }

  getProcess(id: number): PlanningProcess {
    return this.myProcesses.concat(this.sharedProcesses).filter(process => process.id === id)[0];
  }

  toggleScenarioMenu(): void{
    this.showScenarioMenu = !this.showScenarioMenu;
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
      dialogRef.componentInstance.isLoading = true;
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
        dialogRef.componentInstance.isLoading = false;
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
      dialogRef.componentInstance.isLoading = true;
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
        dialogRef.componentInstance.isLoading = false;
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
          if (this.activeProcess === process)
            this.activeProcess = undefined;
        },(error) => {
          console.log('there was an error sending the query', error);
        });
      }
    });
  }
}
