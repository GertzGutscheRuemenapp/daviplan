import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { CheckTreeComponent, TreeItemNode } from "../../../elements/check-tree/check-tree.component";
import { MapControl, MapService } from "../../../map/map.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { arrayMove, showAPIError } from "../../../helpers/utils";
import { ExtLayerGroup, ExtLayer } from "../../../rest-interfaces";
import { RestCacheService } from "../../../rest-cache.service";
import { MapLayer, MapLayerGroup, WMSLayer } from "../../../map/layers";

function isLayer(obj: any): obj is ExtLayer{
  return 'layerName' in obj;
}

@Component({
  selector: 'app-external-layers',
  templateUrl: './external-layers.component.html',
  styleUrls: ['./external-layers.component.scss']
})
export class ExternalLayersComponent implements AfterViewInit, OnDestroy {
  @ViewChild('layerTree') layerTree!: CheckTreeComponent;
  @ViewChild('addLayerTemplate') addLayerTemplate?: TemplateRef<any>;
  @ViewChild('editLayerTemplate') editLayerTemplate?: TemplateRef<any>;
  @ViewChild('editLayerGroupTemplate') editLayerGroupTemplate?: TemplateRef<any>;
  @ViewChild('layerCard') layerCard?: InputCardComponent;
  @ViewChild('layerGroupCard') layerGroupCard?: InputCardComponent;
  layerGroups: MapLayerGroup[] = [];
  mapControl?: MapControl;
  layerGroupForm: FormGroup;
  addLayerForm: FormGroup;
  editLayerForm: FormGroup;
  selectedLayer?: MapLayer;
  selectedGroup?: MapLayerGroup;
  availableLayers: MapLayer[] = [];
  isLoading$ = new BehaviorSubject<boolean>(false);

  constructor(private mapService: MapService, private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private restService: RestCacheService, private formBuilder: FormBuilder) {
    this.addLayerForm = this.formBuilder.group({
      name: new FormControl(''),
      url: new FormControl(''),
      layerName: new FormControl(''),
      description: new FormControl('')
    });
    this.editLayerForm = this.formBuilder.group({
      name: new FormControl(''),
      description: new FormControl('')
    });
    this.addLayerForm.controls['layerName'].disable();
    this.addLayerForm.controls['url'].disable();
    this.layerGroupForm = this.formBuilder.group({
      name: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.isLoading$.next(true);
    this.mapService.fetchExternalLayers({ reset: true }).subscribe(groups => {
      this.layerGroups = groups;
      this.layerTree.setItems(this.layerGroups);
      this.layerGroups.forEach(group => {
        group.children?.forEach(layer => {
          if (layer.active)
            this.layerTree.setChecked(layer, layer.active);
        })
        this.isLoading$.next(false);
      });
    })
    this.layerTree.addItemClicked.subscribe(node => {
      const parent = this.getGroup(node.id);
      if (!parent) return;
      this.addLayer(parent);
    })
    this.layerTree.itemSelected.subscribe(node => {
      this.selectedLayer = (node.children) ? undefined : this.getLayer(node.id);
      this.selectedGroup = (node.children) ? this.getGroup(node.id) : undefined;
    })
    this.layerTree.itemChecked.subscribe(evt => {
      this.onToggleActive(evt.item, evt.checked);
    })
    this.mapControl = this.mapService.get('base-layers-map');
    this.setupLayerGroupCard();
    this.setupLayerCard();
  }

  /**
   * setup edit-layer card, form and dialog
   */
  setupLayerCard(): void {
    this.layerCard?.dialogOpened.subscribe(ok => {
      this.editLayerForm.reset({
        name: this.selectedLayer?.name,
        description: this.selectedLayer?.description
      });
    })
    this.layerCard?.dialogConfirmed.subscribe((ok)=>{
      // display errors for all fields even if not touched
      this.editLayerForm.markAllAsTouched();
      if (this.editLayerForm.invalid) return;
      let attributes: any = {
        name: this.editLayerForm.value.name,
        description: this.editLayerForm.value.description
      }
      this.layerCard?.setLoading(true);
      this.http.patch<ExtLayer>(`${this.rest.URLS.layers}${this.selectedLayer?.id}/`, attributes
      ).subscribe(layer => {
        this.selectedLayer!.name = layer.name;
        this.selectedLayer!.description = layer.description;
        this.layerTree.refresh();
        this.mapControl?.refresh({ external: true });
        this.layerCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.layerCard?.setLoading(false);
      });
    })
    this.layerCard?.dialogClosed.subscribe(ok => {
      this.editLayerForm.reset()
    })
  }

  /**
   * setup edit-layer-group card, form and dialog
   */
  setupLayerGroupCard(): void {
    this.layerGroupCard?.dialogOpened.subscribe(ok => {
      this.layerGroupForm.reset({
        name: this.selectedGroup?.name
      });
    })
    this.layerGroupCard?.dialogConfirmed.subscribe((ok)=>{
      // display errors for all fields even if not touched
      this.layerGroupForm.markAllAsTouched();
      if (this.layerGroupForm.invalid) return;
      let attributes: any = {
        name: this.layerGroupForm.value.name
      }
      this.layerGroupCard?.setLoading(true);
      this.http.patch<ExtLayerGroup>(`${this.rest.URLS.layerGroups}${this.selectedGroup?.id}/`, attributes
      ).subscribe(group => {
        this.selectedGroup!.name = group.name;
        this.layerTree.refresh();
        this.mapControl?.refresh({ external: true });
        this.layerGroupCard?.closeDialog(true);
      },(error) => {
        showAPIError(error, this.dialog);
        this.layerGroupCard?.setLoading(false);
      });
    })
    this.layerGroupCard?.dialogClosed.subscribe(ok => {
      this.layerGroupForm.reset()
    })
  }

  /**
   * get layer with given id from already fetched layers
   *
   * @param id
   */
  getLayer(id: number | string | undefined): MapLayer | undefined {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
      if (!group.children) continue;
      for (let layer of group.children){
        if (layer.id === id) {
          return layer;
        }
      }
    }
    return;
  }

  /**
   * get layer-group with given id from already fetched groups
   *
   * @param id
   */
  getGroup(id: number | string | undefined): MapLayerGroup | undefined {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
        if (group.id === id) {
          return group;
      }
    }
    return;
  }

  /**
   * open dialog to create new layer-group, post to backend on confirm
   */
  addGroup(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Neue Layergruppe',
        template: this.editLayerGroupTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.afterClosed().subscribe(ok => {
      this.layerGroupForm.reset();
      this.availableLayers = [];
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      // display errors for all fields even if not touched
      this.layerGroupForm.markAllAsTouched();
      if (this.layerGroupForm.invalid) return;
      let attributes: any = {
        name: this.layerGroupForm.value.name,
        order: this.layerGroups.length + 1,
        external: true
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<ExtLayerGroup>(this.rest.URLS.layerGroups, attributes
      ).subscribe(group => {
        this.layerGroups.push(new MapLayerGroup(group.name, { order: group.order, id: group.id, external: true }));
        this.layerTree.refresh();
        this.mapControl?.refresh({ external: true });
        this.layerTree.select(group);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  /**
   * open dialog to create new layer, post to backend on confirm
   */
  addLayer(parent: MapLayerGroup): void {
    this.addLayerForm.reset();
    this.availableLayers = [];
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '900px',
      disableClose: true,
      data: {
        title: `Neuer Layer in "${parent.name}"`,
        template: this.addLayerTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.addLayerForm.markAllAsTouched();
      if (this.addLayerForm.invalid) return;
      let attributes: any = {
        name: this.addLayerForm.value.name,
        layerName: this.addLayerForm.get('layerName')!.value,
        url: this.addLayerForm.get('url')!.value,
        description: this.addLayerForm.value.description || '',
        order: parent.children?.length,
        group: parent.id
      }
      dialogRef.componentInstance.isLoading$.next(true);
      this.http.post<ExtLayer>(this.rest.URLS.layers, attributes).subscribe(layer => {
        const group = this.getGroup(layer.group);
        group?.addLayer(new WMSLayer(layer.name, layer.url, {
          id: layer.id,
          order: layer.order,
          description: layer.description,
          layerName: layer.layerName,
          active: layer.active
        }));
        this.layerTree.refresh();
        this.mapControl?.refresh({ external: true });
        this.layerTree.select(layer);
        dialogRef.close();
      },(error) => {
        showAPIError(error, this.dialog);
        dialogRef.componentInstance.isLoading$.next(false);
      });
    });
  }

  /**
   * request WMS-capabilities from given url (via backend as proxy)
   *
   * @param url
   */
  requestCapabilities(url: string): void {
    if (!url) return;
    this.addLayerForm.reset();
    this.addLayerForm.setErrors(null);
    this.http.post(this.rest.URLS.getCapabilities, { url: url }).subscribe((res: any) => {
      this.availableLayers = [];
      if (!res.cors) {
        showAPIError({ message: 'Der Server unterstützt kein Cross-Origin Resource Sharing (CORS).' }, this.dialog);
        return;
      }
      for (let i = 0; i < res.layers.length; i += 1) {
        const l = res.layers[i];
        const layer = new WMSLayer(l.title, res.url,{
          id: i,
          layerName: l.name,
          order: 0,
          description: l.abstract
        });
        this.availableLayers.push(layer);
        if (res.layers.length > 0)
          this.onAvLayerSelected(0);
      }
    }, error => {
      showAPIError(error, this.dialog);
    })
  }

  /**
   * handle selection of an available layer in add-layer dialog (capabilities)
   *
   * @param idx
   */
  onAvLayerSelected(idx: number): void {
    const layer = this.availableLayers[idx],
          controls = this.addLayerForm.controls;
    controls['name'].patchValue(layer.name);
    controls['description'].patchValue(layer.description);
    controls['layerName'].patchValue((layer as WMSLayer).layerName);
    controls['url'].patchValue(layer.url);
  }

  /**
   * handle removal of node in layer-tree
   */
  onRemoveNode(): void {
    if (this.selectedLayer) this.removeLayer(this.selectedLayer);
    if (this.selectedGroup) this.removeGroup(this.selectedGroup);
  }

  /**
   * ask if given layer shall be removed and post delete to backend on confirm
   *
   * @param layer
   */
  removeLayer(layer: MapLayer){
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      data: {
        title: $localize`Den Layer wirklich entfernen?`,
        confirmButtonText: $localize`Layer entfernen`,
        value: layer.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.layers}${layer.id}/`
        ).subscribe(res => {
          for (let group of this.layerGroups) {
            if (!group.children) continue;
            const idx = group.children.indexOf(layer);
            if (idx >= 0) {
              group.children.splice(idx, 1);
              this.selectedLayer = undefined;
              this.layerTree.refresh();
              this.mapControl?.refresh({ external: true });
            }
          }
        },(error) => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  /**
   * ask if given group shall be removed and post delete to backend on confirm
   *
   * @param group
   */
  removeGroup(group: MapLayerGroup){
    const dialogRef = this.dialog.open(RemoveDialogComponent, {
      width: '420px',
      data: {
        title: $localize`Die Layergruppe wirklich entfernen?`,
        confirmButtonText: $localize`Layergruppe entfernen`,
        message: (group.children && group.children.length > 0) ? `Achtung: Die Layergruppe enthält ${group.children.length} Layer, die bei der Entfernung der Gruppe ebenfalls dauerhaft entfernt werden.`: '',
        value: group.name
      }
    });
    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.http.delete(`${this.rest.URLS.layerGroups}${group.id}/?override_protection=true`
        ).subscribe(res => {
          const idx = this.layerGroups.indexOf(group);
          if (idx >= 0) {
            this.layerGroups.splice(idx, 1);
            this.selectedGroup = undefined;
            this.layerTree.refresh();
            this.mapControl?.refresh({ external: true });
          }
        },(error) => {
          showAPIError(error, this.dialog);
        });
      }
    });
  }

  /**
   * patches layer-order of layers or layer-groups to their current place in the array
   *
   */
  patchOrder(array: MapLayer[] | MapLayerGroup[]): void {
    if (array.length === 0) return;
    const url = isLayer(array[0]) ? this.rest.URLS.layers: this.rest.URLS.layerGroups;
    let observables: Observable<any>[] = [];
    for ( let i = 0; i < array.length; i += 1){
      const obj = array[i];
      const request = this.http.patch<any>(`${url}${obj.id}/`, { order: i + 1 });
      request.subscribe(res => {
        obj.order = res.order;
      });
      // ToDo: chain - refresh and fetchlayers at the end
      observables.push(request);
    }
    forkJoin(...observables).subscribe(next => {
      this.mapControl?.refresh({ external: true });
      this.layerTree.refresh();
    })
  }

  /**
   * move currently selected layer up or down in layer tree
   *
   * @param direction - 'up' or 'down'
   */
  moveSelected(direction: string): void {
    const selected = this.selectedLayer? this.selectedLayer: this.selectedGroup? this.selectedGroup: undefined;
    if (!selected) return;
    const array = (this.selectedLayer && this.selectedLayer.group)? this.selectedLayer.group.children!: this.layerGroups;
    // @ts-ignore
    const idx = array.indexOf(selected);
    if (direction === 'up'){
      if (idx <= 0) return;
      arrayMove(array, idx, idx - 1);
    }
    else if (direction === 'down'){
      if (idx === -1 || idx === array.length - 1) return;
      arrayMove(array, idx, idx + 1);
    }
    else return;

    this.patchOrder(array);
  }

  /**
   * handle the toggle of the checkbox of a group or layer in the layer-tree
   * and post the current state to backend
   *
   * @param node
   * @param active
   */
  onToggleActive(node: TreeItemNode, active: boolean): void {
    const layers: MapLayer[] = (node.children)? this.getGroup(node.id)!.children || []: [this.getLayer(node.id)!];
    let observables: Observable<any>[] = [];
    layers.forEach(layer => {
      const req = this.http.patch<ExtLayer>(`${this.rest.URLS.layers}${layer.id}/`,
        { active: active });
      observables.push(req);
    })
    forkJoin(...observables).subscribe(next => {
      this.mapControl?.refresh({ external: true });
    })
  };

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
