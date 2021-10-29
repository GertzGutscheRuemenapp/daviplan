import { Component, OnInit, ViewChildren, QueryList, ElementRef, ViewChild, TemplateRef } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  scenarios: string[] = ['Szenario 1', 'Szenario 2']
  activeScenario: string = 'Status Quo';
  @ViewChild('removeScenario') removeScenarioTemplate?: TemplateRef<any>;
  @ViewChild('editScenario') editScenarioTemplate?: TemplateRef<any>;
  @ViewChild('createScenario') createScenarioTemplate?: TemplateRef<any>;

  constructor(private dialog: MatDialog) { }

  ngOnInit(): void {
  }

  toggleScenario(event: Event) {
    if (event.target !== event.currentTarget) return;
    let a = (event.target as Element).attributes;
    this.activeScenario = ((event.target as Element).attributes as any)['data-value'].value;
    this.scenarioCards?.forEach((card: ElementRef) => {
      let el = card.nativeElement;
      if (el.attributes['data-value'].nodeValue === this.activeScenario)
        el.classList.add('active');
      else
        el.classList.remove('active');
    });
  }

  onDeleteScenario() {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Das Szenario wirklich entfernen?`,
        confirmButtonText: $localize`Szenario entfernen`,
        template: this.removeScenarioTemplate,
        closeOnConfirm: true
      },
      panelClass: 'warning'
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

  onCreateScenario() {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Szenario erstellen`,
        // confirmButtonText: $localize`erstellen`,
        template: this.createScenarioTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

  onEditScenario() {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: $localize`Szenario umbenennen`,
        // confirmButtonText: $localize`umbenennen`,
        template: this.editScenarioTemplate,
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
    });
  }

}
