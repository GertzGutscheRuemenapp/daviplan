import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl } from "../../../map/map.service";
import { DemandRateSet, ModeVariant, Service, TransportMode } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { FormBuilder, FormGroup } from "@angular/forms";

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
  @ViewChild('editVariant') editVariantTemplate?: TemplateRef<any>;

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

  onSetAsDefault(): void {
    if (!this.selectedVariant) return; //  || this.selectedVariant.isDefault
    const attributes = { isDefault: true };
    this.http.patch<ModeVariant>(`${this.rest.URLS.modevariants}${this.selectedVariant.id}/`, attributes
    ).subscribe(variant => {
      this.variants.forEach(v => v.isDefault = false);
      this.selectedVariant!.isDefault = variant.isDefault;
    })
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
// /matrixcellplaces/precalculate_traveltime
}
