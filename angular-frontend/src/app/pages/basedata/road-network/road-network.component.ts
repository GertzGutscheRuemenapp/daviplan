import { Component, OnDestroy, OnInit } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { MatDialog } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";
import { BasedataSettings, LogEntry, ModeVariant, TransportMode } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { Subscription } from "rxjs";

@Component({
  selector: 'app-road-network',
  templateUrl: './road-network.component.html',
  styleUrls: ['./road-network.component.scss']
})
export class RoadNetworkComponent implements OnInit, OnDestroy {
  baseDataSettings?: BasedataSettings;
  modeVariants: ModeVariant[] = [];
  isProcessing = false;
  subscriptions: Subscription[] = [];

  constructor(private http: HttpClient, private rest: RestAPI, private dialog: MatDialog,
              private settings: SettingsService, private restCache: RestCacheService) { }

  ngOnInit(): void {
    this.settings.baseDataSettings$.subscribe(baseSettings => this.baseDataSettings = baseSettings);
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(bs => {
      this.baseDataSettings = bs;
      this.isProcessing = bs.processes?.routing || false;
    }));
    this.settings.fetchBaseDataSettings();
    this.restCache.getModeVariants().subscribe(modeVariants => {
      this.modeVariants = modeVariants.filter(m => m.mode !== TransportMode.TRANSIT);
    })
  }

  downloadBaseNetwork(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `OpenStreetMap-Straßennetz herunterladen`,
        confirmButtonText: 'Straßennetz herunterladen',
        message: 'Das gesamtdeutsche Straßennetz wird von der Geofabrik heruntergeladen und auf dem Server für die weitere Verarbeitung gespeichert. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      if (ok) {
        if (this.baseDataSettings?.routing) {
          this.baseDataSettings.routing.projectAreaNet = false;
          this.baseDataSettings.routing.baseNet = false;
        }
        this.http.post<any>(`${this.rest.URLS.networks}pull_base_network/`, {}).subscribe(() => {
          this.isProcessing = true;
        }, (error) => {
        })
      }
    })
  }

  createProjectNetwork(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `Straßennetz mit Projektgebiet verschneiden`,
        confirmButtonText: 'Straßennetz verschneiden',
        message: 'Das gesamtdeutsche Straßennetz wird mit dem Projektgebiet (inkl. Buffer) verschnitten und die individuellen Router für die verschiedenen Modi werden gebaut. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      if (ok)
        this.http.post<any>(`${this.rest.URLS.networks}build_project_network/`, {}).subscribe(() => {
          this.isProcessing = true;
        },(error) => {
        })
    })
  }

  createMatrices(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `Reisezeitmatrizen erzeugen`,
        confirmButtonText: 'Berechnung starten',
        message: 'Die Reisezeiten zwischen allen vorhandenen Standorten und den Siedlungszellen mit den Modi Fuß, Rad und Auto werden berechnet. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      if (ok)
        this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`, {variants: this.modeVariants.map(m => m.id)}).subscribe(() => {
          // this.isProcessing = true;
        },(error) => {
        })
    })
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.success) {
      this.isProcessing = false;
      this.settings.fetchBaseDataSettings();
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
