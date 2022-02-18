import { Component, ElementRef, AfterViewInit, Renderer2, OnDestroy, ViewChild, TemplateRef } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { FormControl } from "@angular/forms";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { Observable } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";
import { ConfirmDialogComponent } from "../../dialogs/confirm-dialog/confirm-dialog.component";
import { User } from "../login/users";
import { MatDialog } from "@angular/material/dialog";
import { mockUsers } from "../login/users";
import { MatSelect } from "@angular/material/select";
import { RemoveDialogComponent } from "../../dialogs/remove-dialog/remove-dialog.component";
import { PlanningService } from "./planning.service";
import { LegendComponent } from "../../map/legend/legend.component";
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { Infrastructure } from "../../rest-interfaces";

interface Project {
  user?: string;
  shared?: boolean;
  editable?: boolean;
  description?: string;
  name: string;
  id: number
}

const mockMyProjects: Project[] = [
  { name: 'Beispielprojekt 1', id: 1, description: 'Beschreibungstext', shared: true },
  { name: 'Beispielprojekt 2', id: 2, shared: true },
  { name: 'Beispielprojekt 3', description: 'Beschreibungstext', id: 3 }
]

const mockSharedProjects: Project[] = [
  { name: 'Beispielprojekt 4', description: 'Beschreibungstext', user: 'Sascha Schmidt', id: 4, editable: true, shared: true },
  { name: 'Beispielprojekt 5', description: 'Beschreibungstext', user: 'Magdalena Martin', id: 5, editable: false, shared: true }
]

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
  myProjects: Project[] = mockMyProjects;
  sharedProjects: Project[] = mockSharedProjects;
  activeProject?: Project;
  // activeProject: Project = this.myProjects[0];
  users = mockUsers;
  showScenarioMenu: boolean = false;
  mapControl?: MapControl;
  realYears?: number[];
  prognosisYears?: number[];
  infrastructures: Infrastructure[] = [];

  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 39.9375em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private renderer: Renderer2,
              private elRef: ElementRef, private mapService: MapService, private dialog: MatDialog,
              private planningService: PlanningService) {  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    // a bit hacky
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'hidden');
    this.mapControl = this.mapService.get('planning-map');
    this.planningService.legend = this.legend;
    this.mapControl.mapDescription = 'Planungsprozess: xyz > Status Quo Fortschreibung <br> usw.';
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
    this.planningService.setReady(true);
  }

  ngOnDestroy(): void {
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'auto');
    this.mapControl?.destroy();
  }

  onProcessChange(id: number): void {
    if (id === undefined) return;
    let project = this.getProject(id);
    this.activeProject = project;
  }

  setSlider(): void {
    if (!(this.realYears && this.prognosisYears)) return;
    this.timeSlider!.prognosisStart = this.prognosisYears[0] || 0;
    this.timeSlider!.years = this.realYears.concat(this.prognosisYears);
    this.timeSlider!.value = this.realYears[0];
    this.timeSlider!.draw();
  }

  getProject(id: number): Project {
    return this.myProjects.concat(this.sharedProjects).filter(project => project.id === id)[0];
  }

  toggleScenarioMenu(): void{
    this.showScenarioMenu = !this.showScenarioMenu;
  }

  onEditProject(project: Project | undefined = undefined): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '600px',
      disableClose: false,
      data: {
        title: project? 'Planungsprozess editieren': 'Planungsprozess erstellen',
        template: this.processTemplate,
        closeOnConfirm: true,
        context: { project: project },
        confirmButtonText: project? 'Speichern': 'Bestätigen',
        infoText: 'Platzhalter'
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

  onDeleteProject(project: Project) {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '460px',
      data: {
        title: $localize`Den Planungsprozess wirklich entfernen?`,
        confirmButtonText: $localize`Planungsprozess entfernen`,
        value: project.name,
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }
}
