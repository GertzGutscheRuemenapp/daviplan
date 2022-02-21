import { Component, AfterViewInit, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { Infrastructure, Layer, LayerGroup, Place } from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-supply',
  templateUrl: './supply.component.html',
  styleUrls: ['./supply.component.scss']
})
export class SupplyComponent implements AfterViewInit{
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  addPlaceMode = false;
  years = [2009, 2010, 2012, 2013, 2015, 2017, 2020, 2025];
  compareSupply = true;
  compareStatus = 'option 1';
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  showScenarioMenu: any = false;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  placesLayer?: Layer;
  places?: Place[];

  constructor(private dialog: MatDialog, private cookies: CookieService, private mapService: MapService,
              private planningService: PlanningService) {
    this.planningService.infrastructures$.subscribe(infrastructures => {
      this.infrastructures = infrastructures;
    })
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.showScenarioMenu = this.cookies.get('exp-planning-scenario');

    this.legendGroup = this.mapControl.addGroup({
      name: 'Angebot',
      order: -1
    }, false)
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

  updatePlaces(): void {
    if (!this.selectedInfrastructure) return;
    this.planningService.getPlaces(this.selectedInfrastructure.id).subscribe(places => {
      if (this.placesLayer)
        this.mapControl?.removeLayer(this.placesLayer.id!)
      this.placesLayer = this.mapControl?.addLayer({
          order: 0,
          type: 'vector',
          group: this.legendGroup?.id,
          name: this.selectedInfrastructure!.name,
          description: this.selectedInfrastructure!.name,
          opacity: 1,
          symbol: {
            fillColor: 'blue',
            strokeColor: 'black',
            symbol: 'circle'
          }
        },
        {
          visible: true,
          tooltipField: 'name',
          selectable: true,
          select: {
            fillColor: 'yellow'
          }
        });
      this.places = places;
      this.mapControl?.addWKTFeatures(this.placesLayer!.id!, this.places, true);
    })
  }
}
