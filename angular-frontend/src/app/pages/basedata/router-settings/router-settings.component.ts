import { Component, OnInit } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import { MatDialog } from "@angular/material/dialog";

export const mockRouters = ['Deutschland 2020', 'SHK mit ÖPNV 2021', 'Dtl 2020 mit A13 Ausbau'];

@Component({
  selector: 'app-router-settings',
  templateUrl: './router-settings.component.html',
  styleUrls: ['./router-settings.component.scss']
})
export class RouterSettingsComponent implements OnInit {
  routers = mockRouters;
  selectedRouter = this.routers[0];

  constructor(private http: HttpClient, private rest: RestAPI, private dialog: MatDialog) { }

  ngOnInit(): void {
  }

  createBaseNetwork(): void {
    const dialogRef = SimpleDialogComponent.show(
      'Das Basisnetz wird erstellt mit den Luftlinien zwischen Orten und Rasterzellen ' +
      '(wird später in der Entwicklung durch echtes Routing ersetzt). Bitte warten',
      this.dialog, { showAnimatedDots: true, width: '400px' });
    this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}calculate_beelines/`, {}).subscribe(() => {
      dialogRef.close();
    },(error) => {
      dialogRef.close();
    })
  }
}
