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
import { mockInfrastructures } from "../administration/infrastructure/infrastructure.component";
import { mockUsers } from "../login/users";
import { MatSelect } from "@angular/material/select";

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

  faArrows = faArrowsAlt;
  myProjects: Project[] = mockMyProjects;
  sharedProjects: Project[] = mockSharedProjects;
  activeProject?: Project;
  // activeProject: Project = this.myProjects[0];
  infrastructures = mockInfrastructures;
  users = mockUsers;
  @ViewChild('processTemplate') processTemplate?: TemplateRef<any>;
  @ViewChild('removeProject') removeProjectTemplate?: TemplateRef<any>;
  @ViewChild('processSelect') processSelect!: MatSelect;
  showScenarioMenu: boolean = false;
  mapControl?: MapControl;
  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 39.9375em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  constructor(private breakpointObserver: BreakpointObserver, private renderer: Renderer2,
              private elRef: ElementRef, private mapService: MapService, private dialog: MatDialog) {  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    // a bit hacky
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'hidden');
    this.mapControl = this.mapService.get('planning-map');
    this.mapControl.mapDescription = 'Planungsprozess: xyz > Status Quo Fortschreibung <br> usw.';
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
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '460px',
      data: {
        title: $localize`Den Planungsprozess wirklich entfernen?`,
        confirmButtonText: $localize`Planungsprozess entfernen`,
        context: { project: project },
        template: this.removeProjectTemplate,
        closeOnConfirm: true
      },
      panelClass: 'warning'
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }
}
