import { Component, OnInit } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";
import { BasedataSettings, ModeVariant, TransportMode } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";

export const mockRouters = ['Deutschland 2020', 'SHK mit ÖPNV 2021', 'Dtl 2020 mit A13 Ausbau'];

@Component({
  selector: 'app-road-network',
  templateUrl: './road-network.component.html',
  styleUrls: ['./road-network.component.scss']
})
export class RoadNetworkComponent implements OnInit {
  routers = mockRouters;
  selectedRouter = this.routers[0];
  baseDataSettings?: BasedataSettings;
  modeVariants: ModeVariant[] = [];

  constructor(private http: HttpClient, private rest: RestAPI, private dialog: MatDialog,
              private settings: SettingsService, private restCache: RestCacheService) { }

  ngOnInit(): void {
    this.settings.baseDataSettings$.subscribe(baseSettings => this.baseDataSettings = baseSettings);
    this.restCache.getModeVariants().subscribe(modeVariants => {
      this.modeVariants = modeVariants.filter(m => m.mode !== TransportMode.TRANSIT);
    })
  }

  downloadBaseNetwork(): void {
    const dialogRef = SimpleDialogComponent.show(
      'Das Basisnetz wird heruntergeladen. Bitte warten',
      this.dialog, { showAnimatedDots: true, width: '400px' });
    this.http.post<any>(`${this.rest.URLS.networks}pull_base_network/`, {}).subscribe(() => {
      dialogRef.close();
      this.settings.fetchBaseDataSettings();
    },(error) => {
      dialogRef.close();
    })
  }

  createProjectNetwork(): void {
    const dialogRef = SimpleDialogComponent.show(
      'Das Basisnetz wird mit dem Projektgebiet verschnitten. Bitte warten',
      this.dialog, { showAnimatedDots: true, width: '400px' });
    this.http.post<any>(`${this.rest.URLS.networks}build_project_network/`, {}).subscribe(() => {
      dialogRef.close();
      this.settings.fetchBaseDataSettings();
    },(error) => {
      dialogRef.close();
    })
  }

  createMatrices(): void {
    const dialogRef = SimpleDialogComponent.show(
      'Die Reisezeitmatrizen für die Modi "Auto", "Fahrrad" und "zu Fuß" werden erzeugt. Bitte warten',
      this.dialog, { showAnimatedDots: true, width: '400px' });
    this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`, {variants: this.modeVariants.map(m => m.id)}).subscribe(() => {
      dialogRef.close();
    },(error) => {
      dialogRef.close();
    })
  }
}
