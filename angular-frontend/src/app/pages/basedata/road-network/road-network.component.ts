import { Component, OnDestroy, OnInit } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { MatDialog } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";
import { BasedataSettings, LogEntry, ModeVariant, TransportMode } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { BehaviorSubject, Subscription } from "rxjs";
import { showAPIError } from "../../../helpers/utils";

@Component({
  selector: 'app-road-network',
  templateUrl: './road-network.component.html',
  styleUrls: ['./road-network.component.scss']
})
export class RoadNetworkComponent implements OnInit, OnDestroy {
  baseDataSettings?: BasedataSettings;
  modeVariants: ModeVariant[] = [];
  isProcessing$ = new BehaviorSubject<boolean>(false);
  subscriptions: Subscription[] = [];
  isLoading$ = new BehaviorSubject<boolean>(false);
  statistics: Record<number, number> = {};
  TransportMode = TransportMode;

  constructor(private http: HttpClient, private rest: RestAPI, private dialog: MatDialog,
              private settings: SettingsService, private restService: RestCacheService) {
    // make sure data requested here is up-to-date
    this.restService.reset();
  }

  ngOnInit() {
    this.settings.baseDataSettings$.subscribe(baseSettings => this.baseDataSettings = baseSettings);
    this.subscriptions.push(this.settings.baseDataSettings$.subscribe(bs => {
      this.baseDataSettings = bs;
      this.isProcessing$.next(bs.processes?.routing || false);
    }));
    this.settings.fetchBaseDataSettings();
    this.isLoading$.next(true);
    this.restService.getModeVariants().subscribe(modeVariants => {
      this.modeVariants = modeVariants.filter(m => m.mode !== TransportMode.TRANSIT && m.isDefault);
      this.isLoading$.next(false);
      this.getStatistics();
    })
  }

  getStatistics(): void {
    this.isLoading$.next(true);
    this.restService.getRoutingStatistics({ reset: true }).subscribe(stats => {
      this.statistics = {};
      this.modeVariants.forEach(mV => this.statistics[mV.mode] = stats.nRelsPlaceCellModevariant[mV.id]);
      this.isLoading$.next(false);
    })
  }

  downloadBaseNetwork(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `OpenStreetMap-Straßennetz herunterladen`,
        confirmButtonText: 'Straßennetz herunterladen',
        message: 'Das gesamtdeutsche Straßennetz wird von der Geofabrik heruntergeladen und auf dem Server für die weitere Verarbeitung gespeichert. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      if (this.baseDataSettings?.routing) {
        // this.baseDataSettings.routing.projectNetDate = undefined;
        this.baseDataSettings.routing.baseNetDate = undefined;
      }
      this.http.post<any>(`${this.rest.URLS.networks}pull_base_network/`, {}).subscribe(() => {
        this.isProcessing$.next(true);
      }, (error) => {
        showAPIError(error, this.dialog);
      })
    })
  }

  createProjectNetwork(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Straßennetz mit Projektgebiet verschneiden`,
        confirmButtonText: 'Straßennetz verschneiden',
        message: 'Das gesamtdeutsche Straßennetz wird mit dem Projektgebiet (inkl. Buffer) verschnitten und die individuellen Router für die verschiedenen Modi werden gebaut. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    this.isLoading$.next(true);
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.http.post<any>(`${this.rest.URLS.networks}build_project_network/`, {}).subscribe(() => {
        this.isProcessing$.next(true);
        if (this.baseDataSettings?.routing) {
          this.baseDataSettings.routing.projectNetDate = undefined;
        }
        this.isLoading$.next(false);
      },(error) => {
        showAPIError(error, this.dialog);
        this.isLoading$.next(false);
      })
    })
  }

  createMatrices(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Reisezeitmatrizen erzeugen`,
        confirmButtonText: 'Berechnung starten',
        message: 'Die Reisezeiten zwischen allen vorhandenen Standorten und den Siedlungszellen mit den Modi Fuß, Rad und Auto werden berechnet. Dies kann einige Minuten dauern.',
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`, {variants: this.modeVariants.map(m => m.id)}).subscribe(() => {
        this.isProcessing$.next(true);
        dialogRef.close();
      }, (error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      })
    });
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing$.next(false);
      this.settings.fetchBaseDataSettings();
      this.getStatistics();
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
