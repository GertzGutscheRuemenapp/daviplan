import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl } from "../../../map/map.service";
import {
  DemandRateSet,
  ModeVariant,
  Service,
  TransitMatrixEntry,
  TransitStop,
  TransportMode
} from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormGroup } from "@angular/forms";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";
import * as fileSaver from "file-saver";

@Component({
  selector: 'app-transit-matrix',
  templateUrl: './transit-matrix.component.html',
  styleUrls: ['./transit-matrix.component.scss']
})
export class TransitMatrixComponent implements AfterViewInit, OnDestroy {
  mapControl?: MapControl;
  variants: ModeVariant[] = [];
  selectedVariant?: ModeVariant;
  variantForm: FormGroup;
  file?: File;
  uploadErrors: any = {};
  stops: TransitStop[] = [];
  matrixEntries: TransitMatrixEntry[] = [];
  @ViewChild('editVariant') editVariantTemplate?: TemplateRef<any>;
  @ViewChild('fileUploadTemplate') fileUploadTemplate?: TemplateRef<any>;

  constructor(private dialog: MatDialog, private restService: RestCacheService,
              private http: HttpClient, private rest: RestAPI, private formBuilder: FormBuilder) {
    this.variantForm = this.formBuilder.group({
      label: ''
    });
    this.restService.getModeVariants().subscribe(variants => {
      this.variants = variants.filter(v => v.mode === TransportMode.TRANSIT);
    })
  }

  ngAfterViewInit(): void {
  }

  selectVariant(variant: ModeVariant): void {
    if (variant === this.selectedVariant) return;
    this.selectedVariant = variant;
    this.stops = []; this.matrixEntries = [];
    if (this.selectedVariant) {
      this.restService.getTransitStops({ variant: this.selectedVariant.id }).subscribe(stops => {
        this.stops = stops;
      })
      this.restService.getTransitMatrix({ variant: this.selectedVariant.id }).subscribe(entries => {
        this.matrixEntries = entries;
      })
    }
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
          this.variantForm.setErrors(error.error);
          dialogRef.componentInstance.isLoading$.next(false);
        });
      }
      else {
        this.http.patch<ModeVariant>(`${this.rest.URLS.modevariants}${this.selectedVariant!.id}/`, attributes
        ).subscribe(variant => {
          Object.assign(this.selectedVariant, variant);
          dialogRef.close();
        }, (error) => {
          this.variantForm.setErrors(error.error);
          dialogRef.componentInstance.isLoading$.next(false);
        });
      }
    });
  }

  createMatrices(): void {
    if (!this.selectedVariant) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: `Reisezeitmatrizen erzeugen`,
        confirmButtonText: 'Berechnung starten',
        message: 'Die Reisezeiten zwischen allen vorhandenen Standorten und den Siedlungszellen über die Haltestellen im ÖPNV-Netz werden berechnet. Dies kann einige Minuten dauern.',
        closeOnConfirm: true
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      if (ok)
        this.http.post<any>(`${this.rest.URLS.matrixCellPlaces}precalculate_traveltime/`, {variants: [this.selectedVariant!.id]}).subscribe(() => {
        },(error) => {
        })
    })
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
      dialogRef.close();
    });
  }

  uploadStops(): void {
    if (!this.selectedVariant) return;
    this.uploadErrors = {};
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
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
        this.restService.getTransitStops({ reset: true, variant: this.selectedVariant!.id }).subscribe(stops => {
          this.stops = stops;
          this.restService.getTransitMatrix({ reset: true, variant: this.selectedVariant!.id }).subscribe(entries => {
            this.matrixEntries = entries;
            dialogRef.close();
          })
        })
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.setLoading(false);
      });
    });
  }

  uploadMatrix(visum: boolean = false): void {
    if (!this.selectedVariant) return;
    this.uploadErrors = {};
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: 'Fahrzeitenliste hochladen',
        confirmButtonText: 'Datei hochladen',
        template: this.fileUploadTemplate,
        closeOnConfirm: false,
        message: visum? 'Fahrzeitenliste im VISUM-Format hochladen': 'Befülltes Excel-Template mit der Fahrzeitenliste hochladen',
        context: {
          accept: visum? '.mtx': '.xlsx,.xls'
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
        dialogRef.close();
      }, error => {
        this.uploadErrors = error.error;
        dialogRef.componentInstance.setLoading(false);
      });
    });
  }


  setFiles(event: Event){
    const element = event.currentTarget as HTMLInputElement;
    const files: FileList | null = element.files;
    this.file =  (files && files.length > 0)? files[0]: undefined;
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
// /matrixcellplaces/precalculate_traveltime
}
