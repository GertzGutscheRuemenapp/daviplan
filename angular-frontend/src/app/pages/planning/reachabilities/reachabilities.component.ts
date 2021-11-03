import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { mockInfrastructures } from "../../administration/infrastructure/infrastructure.component";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements OnInit {
  selectMode = false;
  transportMode = 1;
  indicator = 'option 1';
  selectFacMode = false;
  selectLivMode = false;
  infrastructures = mockInfrastructures;
  selectedInfrastructure = this.infrastructures[0];
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  showScenarioMenu: any = false;

  constructor(private dialog: MatDialog, public cookies: CookieService) {}

  ngOnInit(): void {
    this.showScenarioMenu = this.cookies.get('exp-planning-scenario');
  }

  toggleIndicator(): void {
    this.selectFacMode = false;
    this.selectLivMode = false;
  }

  onFilter(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '1400px',
      disableClose: false,
      data: {
        // title: 'Standortfilter',
        template: this.filterTemplate,
        closeOnConfirm: true,
        infoText: '<p>Mit dem Schieberegler rechts oben können Sie das Jahr wählen für das die Standortstruktur in der Tabelle angezeigt werden soll. Die Einstellung wird für die Default-Kartendarstellung übernommen.</p>' +
          '<p>Mit einem Klick auf das Filtersymbol in der Tabelle können Sie Filter auf die in der jeweiligen Spalte Indikatoren definieren. Die Filter werden grundsätzlich auf alle Jahre angewendet. In der Karte werden nur die gefilterten Standorte angezeigt.</p>'+
          '<p>Sie können einmal gesetzte Filter bei Bedarf im Feld „Aktuell verwendete Filter“ unter der Tabelle wieder löschen.</p>'
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

}
