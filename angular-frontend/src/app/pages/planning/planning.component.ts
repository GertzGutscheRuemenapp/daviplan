import { Component, ElementRef, AfterViewInit, Renderer2, OnDestroy, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { FormControl } from "@angular/forms";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';

interface Project {
  user?: string;
  shared?: boolean;
  editable?: boolean;
  name: string;
  id: number
}

const mockMyProjects: Project[] = [
  { name: 'Beispielprojekt 1', id: 1 },
  { name: 'Beispielprojekt 2', id: 2, shared: true },
  { name: 'Beispielprojekt 3', id: 3 }
]

const mockSharedProjects: Project[] = [
  { name: 'Beispielprojekt 4', user: 'Sascha Schmidt', id: 4, editable: true, shared: true },
  { name: 'Beispielprojekt 5', user: 'Magdalena Martin', id: 5, editable: false, shared: true }
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
  processForm = new FormControl();
  showScenarioMenu: boolean = false;
  mapControl?: MapControl;

  constructor(private renderer: Renderer2, private elRef: ElementRef, private mapService: MapService) {  }

  ngAfterViewInit(): void {
    // there is no parent css selector yet but we only want to hide the overflow in the planning pages
    // a bit hacky
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'hidden');
    this.mapControl = this.mapService.get('planning-map');
    this.mapControl.mapDescription = 'Planungsprozess: xyz > Status Quo Fortschreibung <br> usw.'
  }

  ngOnDestroy(): void {
    let wrapper = this.elRef.nativeElement.closest('mat-sidenav-content');
    this.renderer.setStyle(wrapper, 'overflow-y', 'auto');
    this.mapControl?.destroy();
  }

  onProcessChange(id: number): void {
    let project = this.getProject(id);
    this.activeProject = project;
  }

  getProject(id: number): Project {
    return this.myProjects.concat(this.sharedProjects).filter(project => project.id === id)[0];
  }

  toggleScenarioMenu(): void{
    this.showScenarioMenu = !this.showScenarioMenu;
  }
}
