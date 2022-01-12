import { Component, OnInit, ViewChildren, QueryList, ElementRef, ViewChild, TemplateRef, Input } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { mockQuotas } from "../../basedata/demand-quotas/demand-quotas.component";
import { mockPrognoses } from "../../basedata/prognosis-data/prognosis-data.component";
import { environment } from "../../../../environments/environment";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {
  @Input() domain: string = '';
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  scenarios: string[] = ['Szenario 1', 'Szenario 2']
  activeScenario: string = 'Status Quo';
  @ViewChild('editScenario') editScenarioTemplate?: TemplateRef<any>;
  @ViewChild('createScenario') createScenarioTemplate?: TemplateRef<any>;
  @ViewChild('supplyScenarioTable') supplyScenarioTableTemplate?: TemplateRef<any>;
  @ViewChild('demandPlaceholderTable') demandPlaceholderTemplate?: TemplateRef<any>;
  @ViewChild('demandQuotaDialog') demandQuotaTemplate?: TemplateRef<any>;
  quotas = mockQuotas;
  prognoses = mockPrognoses;
  backend: string = environment.backend;

  constructor(private dialog: MatDialog) { }

  ngOnInit(): void {
  }

  toggleScenario(scenario: string) {
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

  onDeleteScenario() {
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Das Szenario wirklich entfernen?`,
        confirmButtonText: $localize`Szenario entfernen`,
        value: this.activeScenario
      }
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

  onShowSupplyTable() {
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

  onShowDemandPlaceholder() {
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

  onShowDemandQuotaSet() {
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
