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
        infoText: 'Platzhalter: Die Filterung der Tabelle filtert die in der Karte dargestellten Standorte'
      }
    });
    dialogRef.afterClosed().subscribe((ok: boolean) => {  });
    dialogRef.componentInstance.confirmed.subscribe(() => {  });
  }

}
