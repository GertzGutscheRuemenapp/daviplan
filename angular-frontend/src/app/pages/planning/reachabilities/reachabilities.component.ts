import { AfterViewInit, Component, TemplateRef, ViewChild } from '@angular/core';
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { CookieService } from "../../../helpers/cookies.service";
import { PlanningService } from "../planning.service";
import { Infrastructure, Layer, LayerGroup, PlanningProcess, RasterCell } from "../../../rest-interfaces";
import { MapControl, MapService } from "../../../map/map.service";

@Component({
  selector: 'app-reachabilities',
  templateUrl: './reachabilities.component.html',
  styleUrls: ['./reachabilities.component.scss']
})
export class ReachabilitiesComponent implements AfterViewInit {
  @ViewChild('filterTemplate') filterTemplate!: TemplateRef<any>;
  selectMode = false;
  rasterCells: RasterCell[] = [];
  transportMode = 1;
  indicator = 'option 1';
  selectFacMode = false;
  selectLivMode = false;
  infrastructures?: Infrastructure[];
  selectedInfrastructure?: Infrastructure;
  activeProcess?: PlanningProcess;
  mapControl?: MapControl;
  legendGroup?: LayerGroup;
  rasterLayer?: Layer;

  constructor(private mapService: MapService, private dialog: MatDialog, public cookies: CookieService,
              public planningService: PlanningService) {
    this.planningService.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.selectedInfrastructure = infrastructures[0];
    });
    this.planningService.activeProcess$.subscribe(process => {
      this.activeProcess = process;
    })
  }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('planning-map');
    this.legendGroup = this.mapControl.addGroup({
      name: 'Erreichbarkeiten',
      order: -1
    }, false)
    this.planningService.getRasterCells().subscribe(rasterCells => {
      this.rasterCells = rasterCells;
      this.drawRaster();
    })
  }

  drawRaster(): void {
    this.rasterLayer = this.mapControl?.addLayer({
        order: 0,
        type: 'vector',
        group: this.legendGroup?.id,
        name: 'Rasterzellen',
        description: 'Zensus-Raster (LAEA)',
        opacity: 1,
        symbol: {
          fillColor: 'rgba(0, 0, 0, 0)',
          strokeColor: 'black',
          symbol: 'line'
        },
        labelField: 'label',
        showLabel: false
      },
      {
        visible: true
      });
    this.mapControl?.clearFeatures(this.rasterLayer!.id!);
    this.mapControl?.addFeatures(this.rasterLayer!.id!, this.rasterCells,
      { properties: 'properties', geometry: 'geometry' });
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
