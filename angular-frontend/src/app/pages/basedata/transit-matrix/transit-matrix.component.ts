import { Component, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MapControl } from "../../../map/map.service";
import {
  LogEntry,
  ModeVariant,
  TransportMode,
  ModeStatistics
} from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormGroup } from "@angular/forms";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import * as fileSaver from "file-saver";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { BehaviorSubject } from "rxjs";
import { environment } from "../../../../environments/environment";
import { showAPIError } from "../../../helpers/utils";

@Component({
  selector: 'app-transit-matrix',
  templateUrl: './transit-matrix.component.html',
  styleUrls: ['./transit-matrix.component.scss']
})
export class TransitMatrixComponent implements OnInit, OnDestroy {
  backend: string = environment.backend;
  mapControl?: MapControl;
  variants: ModeVariant[] = [];
  selectedVariant?: ModeVariant;
  variantForm: FormGroup;
  file?: File;
  statistics?: ModeStatistics;
  isLoading$ = new BehaviorSubject<boolean>(false);
  isProcessing$ = new BehaviorSubject<boolean>(false);
  @ViewChild('editVariant') editVariantTemplate?: TemplateRef<any>;
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;

  constructor(private dialog: MatDialog, private restService: RestCacheService,
              private http: HttpClient, private rest: RestAPI, private formBuilder: FormBuilder) {
    // make sure data requested here is up-to-date
    this.restService.reset();
    this.variantForm = this.formBuilder.group({
      label: ''
    });
  }

  ngOnInit(): void {
    this.fetchVariants();
  }

  fetchVariants(options?: { reset?: boolean }): void {
    this.isLoading$.next(true);
    this.restService.getModeVariants({reset: options?.reset}).subscribe(variants => {
      this.variants = variants.filter(v => v.mode === TransportMode.TRANSIT);
      this.isLoading$.next(false);
    })
  }

  selectVariant(variant: ModeVariant): void {
    if (variant === this.selectedVariant) return;
    this.selectedVariant = variant;
    this.statistics = undefined;
    this.isLoading$.next(true);
    this.restService.getRoutingStatistics({ reset: true }).subscribe(stats => {
      this.statistics = stats;
      this.isLoading$.next(false);
    });
  }

  onEditVariant(create = false): void {
    if (!create && !this.selectedVariant) return;
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: create? 'ÖPNV-Netz hinzufügen': 'ÖPNV-Netz bearbeiten',
        template: this.editVariantTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterOpened().subscribe(() => {
      this.variantForm.reset({ label: create? '': this.selectedVariant!.label});
    })
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.variantForm.markAllAsTouched();
      if (this.variantForm.invalid) return;
      dialogRef.componentInstance.isLoading$.next(true);
      let attributes = {
        label: this.variantForm.value.label,
        mode: TransportMode.TRANSIT
      };
      if (create) {
        this.http.post<ModeVariant>(this.rest.URLS.modevariants, attributes
        ).subscribe(variant => {
          this.variants.push(variant);
          dialogRef.close();
        }, (error) => {
          showAPIError(error, this.dialog);
          dialogRef.componentInstance.isLoading$.next(false);
        });
      }
      else {
        this.http.patch<ModeVariant>(`${this.rest.URLS.modevariants}${this.selectedVariant!.id}/`, attributes
        ).subscribe(variant => {
          Object.assign(this.selectedVariant, variant);
          dialogRef.close();
        }, (error) => {
          showAPIError(error, this.dialog);
          dialogRef.componentInstance.isLoading$.next(false);
        });
      }
    });
  }

  createMatrices(): void {
    if (!this.selectedVariant) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: `Reisezeitmatrizen erzeugen`,
        confirmButtonText: 'Berechnung starten',
        message: 'Die Reisezeiten zwischen allen vorhandenen Standorten und den Siedlungszellen über die Haltestellen im ÖPNV-Netz werden berechnet. Dies kann einige Minuten dauern.',
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`, {variants: [this.selectedVariant!.id]}).subscribe(() => {
        this.isProcessing$.next(true);
        dialogRef.close();
      }, (error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      })
    });
  }

  onSetAsDefault(): void {
    if (!this.selectedVariant) return; //  || this.selectedVariant.isDefault
    const attributes = { isDefault: true };
    this.http.patch<ModeVariant>(`${this.rest.URLS.modevariants}${this.selectedVariant.id}/`, attributes
    ).subscribe(variant => {
      this.variants.forEach(v => v.isDefault = false);
      this.selectedVariant!.isDefault = variant.isDefault;
    })
  }

  downloadTemplate(matrix: boolean = false): void {
    let url = matrix? this.rest.URLS.transitMatrix : this.rest.URLS.transitStops;
    url += 'create_template/';
    const dialogRef = SimpleDialogComponent.show('Bereite Template vor. Bitte warten', this.dialog, { showAnimatedDots: true });
    this.http.post(url, { variant: this.selectedVariant?.id }, { responseType: 'blob' }).subscribe((res:any) => {
      const blob: any = new Blob([res],{ type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      dialogRef.close();
      fileSaver.saveAs(blob, matrix? 'matrix-template.xlsx': 'haltestellen-template.xlsx');
    },(error) => {
      showAPIError(error, this.dialog);
      dialogRef.close();
    });
  }

  uploadStops(): void {
    if (!this.selectedVariant) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: 'Haltestellen hochladen',
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate,
        closeOnConfirm: false,
        message: 'Befülltes Excel-Template mit den Haltestellen hochladen',
        context: {
          accept: '.xlsx,.xls'
        }
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      const formData = new FormData();
      dialogRef.componentInstance.setLoading(true);
      formData.append('excel_file', this.file);
      formData.append('variant', this.selectedVariant!.id.toString());
      const url = `${this.rest.URLS.transitStops}upload_template/`;
      this.http.post(url, formData).subscribe(res => {
        this.isProcessing$.next(true);
        dialogRef.close();
      }, error => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.setLoading(false);
      });
    });
  }

  uploadMatrix(visum: boolean = false): void {
    if (!this.selectedVariant) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      panelClass: 'absolute',
      data: {
        title: 'Fahrzeitenliste hochladen',
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate,
        closeOnConfirm: false,
        message: visum? 'Fahrzeitenliste im VISUM-Format hochladen': 'Befülltes Excel-Template mit der Fahrzeitenliste hochladen',
        context: {
          accept: visum? '*': '.xlsx,.xls'
        }
      }
    });
    dialogRef.componentInstance.confirmed.subscribe((confirmed: boolean) => {
      if (!this.file)
        return;
      dialogRef.componentInstance.setLoading(true);
      const formData = new FormData();
      formData.append('excel_or_visum_file', this.file);
      formData.append('variant', this.selectedVariant!.id.toString());
      const url = `${this.rest.URLS.transitMatrix}upload_template/`;
      this.http.post(url, formData).subscribe(res => {
        this.isProcessing$.next(true);
        dialogRef.close();
      }, error => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.setLoading(false);
      });
    });
  }

  onMessage(log: LogEntry): void {
    if (log?.status?.finished) {
      this.isProcessing$.next(false);
      this.restService.getRoutingStatistics({ reset: true }).subscribe(stats => this.statistics = stats)
    }
  }

  setFiles(event: Event): void {
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  onDeleteVariant(): void {
    if (!this.selectedVariant)
      return;
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '400px',
      data: {
        title: 'Das ÖPNV-Netz wirklich entfernen?',
        message: 'Die Entfernung des ÖPNV-Netzes entfernt auch alle Haltestellen und die berechneten Erreichbarkeiten.',
        confirmButtonText: `ÖPNV-Netz entfernen`,
        value: this.selectedVariant.label
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.modevariants}${this.selectedVariant!.id}/?force=true`
        ).subscribe(res => {
          this.selectedVariant = undefined;
          // other variants might change on deletion of the default one
          this.fetchVariants({reset: true});
        }, error => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
