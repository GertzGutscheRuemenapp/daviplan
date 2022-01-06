import { AfterViewInit, Component, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { CheckTreeComponent } from "../../../elements/check-tree/check-tree.component";
import { MapControl, MapService } from "../../../map/map.service";
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { Observable } from "rxjs";
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { InputCardComponent } from "../../../dash/input-card.component";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import WMSCapabilities from 'ol/format/WMSCapabilities';

export interface LayerGroup {
  id: number,
  order: number,
  name: string,
  external: boolean,
  children?: Layer[]
}

export interface Layer {
  id: number,
  group: number,
  order: number,
  url: string,
  name: string
}

function sortBy(array: any[], attr: string): any[]{
  return array.sort((a, b) =>
    (a[attr] > b[attr])? 1: (a[attr] < b[attr])? -1: 0);
}

@Component({
  selector: 'app-external-layers',
  templateUrl: './external-layers.component.html',
  styleUrls: ['./external-layers.component.scss']
})
export class ExternalLayersComponent implements AfterViewInit, OnDestroy {
  @ViewChild('layerTree') layerTree!: CheckTreeComponent;
  @ViewChild('editLayer') editLayerTemplate?: TemplateRef<any>;
  @ViewChild('editLayerGroup') editLayerGroupTemplate?: TemplateRef<any>;
  @ViewChild('layerCard') layerCard?: InputCardComponent;
  @ViewChild('layerGroupCard') layerGroupCard?: InputCardComponent;
  layerGroups: LayerGroup[] = [];
  mapControl?: MapControl;
  layerGroupForm: FormGroup;
  layerForm: FormGroup;

  selectedLayer?: Layer;
  selectedGroup?: LayerGroup;
  Object = Object;

  constructor(private mapService: MapService, private http: HttpClient, private dialog: MatDialog,
              private rest: RestAPI, private formBuilder: FormBuilder) {
    this.layerForm = this.formBuilder.group({
      name: new FormControl(''),
      url: new FormControl(''),
      // layer_name: new FormControl('')
    });
    this.layerGroupForm = this.formBuilder.group({
      name: new FormControl('')
    });
  }

  ngAfterViewInit(): void {
    this.fetchLayerGroups().subscribe(res => {
      this.fetchLayers().subscribe(res => {
        this.layerTree.setItems(this.layerGroups);
      })
    })
    this.layerTree.addItemClicked.subscribe(node => {
      const parent = this.getGroup(node.id);
      if (!parent) return;
      this.addLayer(parent);
    })
    this.layerTree.selected.subscribe(node => {
      this.selectedLayer = (node.expandable) ? undefined : this.getLayer(node.id);
      this.selectedGroup = (node.expandable) ? this.getGroup(node.id) : undefined;
    })
    this.mapControl = this.mapService.get('base-layers-map');
    this.setupLayerGroupCard();
    this.setupLayerCard();
  }

  fetchLayerGroups(): Observable<LayerGroup[]> {
    const query = this.http.get<LayerGroup[]>(`${this.rest.URLS.layerGroups}?external=true`);
    query.subscribe((layerGroups) => {
      layerGroups.forEach(layerGroup => {
        layerGroup.children = [];
      })
      this.layerGroups = sortBy(layerGroups, 'order');
    });
    return query;
  }

  fetchLayers(): Observable<Layer[]> {
    const query = this.http.get<Layer[]>(this.rest.URLS.layers);
    query.subscribe((layers) => {
      layers.forEach(layer => {
        const group = this.getGroup(layer.group);
        if (group) {
          group.children!.push(layer);
        }
      })
    });
    return query;
  }

  setupLayerCard(): void {

  }

  setupLayerGroupCard(): void {
    this.layerGroupCard?.dialogOpened.subscribe(ok => {
      this.layerGroupForm.reset({
        name: this.selectedGroup?.name
      });
    })
    this.layerGroupCard?.dialogConfirmed.subscribe((ok)=>{
      this.layerGroupForm.setErrors(null);
      // display errors for all fields even if not touched
      this.layerGroupForm.markAllAsTouched();
      if (this.layerGroupForm.invalid) return;
      let attributes: any = {
        name: this.layerGroupForm.value.name
      }
      this.layerGroupCard?.setLoading(true);
      this.http.patch<LayerGroup>(`${this.rest.URLS.layerGroups}${this.selectedGroup?.id}/`, attributes
      ).subscribe(group => {
        this.selectedGroup!.name = group.name;
        this.layerTree.refresh();
        this.layerGroupCard?.closeDialog(true);
      },(error) => {
        // ToDo: set specific errors to fields
        this.layerGroupForm.setErrors(error.error);
        this.layerGroupCard?.setLoading(false);
      });
    })
    this.layerGroupCard?.dialogClosed.subscribe(ok => {
      this.layerGroupForm.reset()
    })
  }

  getLayer(id: number | undefined): Layer | undefined {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
      if (!group.children || group.children.length == 0) return;
      for (let layer of group.children){
        if (layer.id === id) {
          return layer;
        }
      }
    }
    return;
  }

  getGroup(id: number | undefined): LayerGroup | undefined {
    if (id === undefined) return;
    for (let group of this.layerGroups) {
        if (group.id === id) {
          return group;
      }
    }
    return;
  }

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
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.layerGroupForm.setErrors(null);
      // display errors for all fields even if not touched
      this.layerGroupForm.markAllAsTouched();
      if (this.layerGroupForm.invalid) return;
      let attributes: any = {
        name: this.layerGroupForm.value.name,
        order: this.layerGroups.length + 1,
        external: true
      }
      dialogRef.componentInstance.isLoading = true;
      this.http.post<LayerGroup>(this.rest.URLS.layerGroups, attributes
      ).subscribe(group => {
        group.children = [];
        this.layerGroups.push(group);
        this.selectedGroup = group;
        this.layerTree.refresh();
        dialogRef.close();
      },(error) => {
        this.layerGroupForm.setErrors(error.error);
        dialogRef.componentInstance.isLoading = false;
      });
    });
  }

  addLayer(parent: LayerGroup): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '500px',
      disableClose: true,
      data: {
        title: `Neuer Layer in "${parent.name}"`,
        template: this.editLayerTemplate,
        closeOnConfirm: false
      }
    });
  }

  requestURL(): void {
    const url = this.layerForm.value.url;
    if (!url) return;
    const parser = new WMSCapabilities(),
          split = url.split('?'),
          baseURL = split[0];
    let options: string[] = (split.length > 1)? split[1].split('&'): [];
    options = options.concat(['request=GetCapabilities', 'version=2.0.0', 'service=wms']);
    const capURL = `${baseURL}?${options.join('&')}`;
    fetch(capURL, {referrer: "https://monitor.ioer.de", // no-referrer, origin, same-origin...
      mode: "cors"}).then(res => {
      console.log(res)
    }).catch((error) => {
      console.log(error)
    });

  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }

}
