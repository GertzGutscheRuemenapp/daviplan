import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { Geometry, GeometryCollection, MultiPolygon, Polygon } from "ol/geom";
import { Collection, Feature } from 'ol';
import { register } from 'ol/proj/proj4'
import union from '@turf/union';
import pointOnSurface from '@turf/point-on-surface';
import booleanWithin from "@turf/boolean-within";
import * as turf from '@turf/helpers';
import { GeoJSON, WKT } from "ol/format";
import proj4 from 'proj4';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { SiteSettings } from "../../../settings.service";
import { Observable } from "rxjs";
import { Layer } from "ol/layer";
import { last } from "rxjs/operators";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";

export interface ProjectSettings {
  projectArea: string,
  startYear: number,
  endYear: number
}

export interface AgeGroup {
  id?: number,
  fromAge: number,
  toAge: number
}

interface BKGLayer {
  name: string,
  tag: string
}

const areaLayers: BKGLayer[] = [
  { name: 'Kreise', tag: 'vg250_krs' },
  { name: 'Verwaltungsgebiete', tag: 'vg250_vwg' },
  { name: 'Gemeinden', tag: 'vg250_gem' },
]

proj4.defs("EPSG:25832", "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs");
register(proj4);

@Component({
  selector: 'app-project-definition',
  templateUrl: './project-definition.component.html',
  styleUrls: ['./project-definition.component.scss']
})
export class ProjectDefinitionComponent implements AfterViewInit, OnDestroy {
  previewMapControl?: MapControl;
  areaSelectMapControl?: MapControl;
  projectGeom?: MultiPolygon;
  mergedSelectArea?: Feature<any>;
  ageGroups: AgeGroup[] = [];
  __ageGroups: AgeGroup[] = [];
  ageGroupDefaults: AgeGroup[] = [];
  projectAreaErrors = [];
  projectSettings?: ProjectSettings;
  yearForm!: FormGroup;
  Object = Object;
  areaLayers = areaLayers;
  selectedAreaLayer: BKGLayer = areaLayers[0];
  baseAreaLayer: BKGLayer = areaLayers[areaLayers.length - 1];
  selectedBaseAreaMap = new Map<string, Feature<any>>();
  baseAreasInExtent: Feature<any>[] = [];
  showAreaLayers = false;
  ageGroupErrors: string[] = [];
  private _baseSelectLayer?: Layer<any>;
  @ViewChild('areaCard') areaCard!: InputCardComponent;
  @ViewChild('yearCard') yearCard!: InputCardComponent;
  @ViewChild('ageGroupCard') ageGroupCard!: InputCardComponent;
  @ViewChild('ageGroupContainer') ageGroupContainer!: ElementRef;
  @ViewChild('ageGroupWarning') ageGroupWarningTemplate?: TemplateRef<any>;

  constructor(private mapService: MapService, private formBuilder: FormBuilder, private http: HttpClient,
              private rest: RestAPI, private dialog: MatDialog) { }

  ngAfterViewInit(): void {
    this.setupPreviewMap();
    this.setupAreaCard();
    this.fetchProjectSettings().subscribe(settings => {
      this.setupYearCard();
      this.updatePreviewLayer();
    });
    this.fetchAgeGroups().subscribe(ageGroups => {
      this.setupAgeGroupCard();
    });
  }

  fetchProjectSettings(): Observable<ProjectSettings> {
    let query = this.http.get<ProjectSettings>(this.rest.URLS.projectSettings);
    query.subscribe(projectSettings => {
      this.projectSettings = projectSettings;
    })
    return query;
  }

  fetchAgeGroups(): Observable<AgeGroup[]> {
    this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups, {params: {defaults: true}}).subscribe(ageGroups => {
      this.ageGroupDefaults = ageGroups;
    })
    let query = this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups);
    query.subscribe(ageGroups => {
      this.ageGroups = ageGroups;
    })
    return query;
  }

  setupPreviewMap(): void {
    this.previewMapControl = this.mapService.get('project-preview-map');
    this.previewMapControl.setBackground(this.previewMapControl.getBackgroundLayers()[0].id);
    this.previewMapControl.map?.addVectorLayer('project-area',{
      visible: true,
      stroke: { color: '#2196F3', width: 3 },
      fill: { color: 'rgba(33, 150, 243, 0.5)' }
    });
  }

  setupAgeGroupCard(): void {
    this.__ageGroups = JSON.parse(JSON.stringify(this.ageGroups!));

    this.ageGroupCard.dialogConfirmed.subscribe(ok => {
      const valid = this.validateAgeGroups(this.__ageGroups),
            _this = this;
      if (!valid) {
        this.ageGroupErrors = ['Die Altersgruppen müssen lückenlos sein und dürfen sich nicht überschneiden'];
        return;
      }
      const matchesDefaults = this.compareAgeGroupsDefault(this.__ageGroups);
      function postAgeGroups(){
        _this.ageGroupCard.setLoading(true);
        _this.http.post<AgeGroup[]>(`${_this.rest.URLS.ageGroups}replace/`, _this.__ageGroups
        ).subscribe(ageGroups => {
          _this.ageGroupCard.closeDialog(true);
          _this.ageGroups = ageGroups;
        },(error) => {
          // ToDo: set specific errors to fields
          _this.ageGroupErrors = [error.error.detail];
          _this.ageGroupCard.setLoading(false);
        });
      }

      if (!matchesDefaults){
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
          width: '400px',
          data: {
            title: $localize`Altersgruppen bestätigen`,
            confirmButtonText: $localize`Altersgruppen übernehmen`,
            template: this.ageGroupWarningTemplate,
            closeOnConfirm: true,
            infoText: 'Wenn die Altersgruppen nicht mit der Regionalstatistik übereinstimmen, können die ' +
              'Bevölkerungsdaten im Bereich "Grundlagendaten" nicht automatisch von der Regionalstatistik abgerufen werden, ' +
              'sondern müssen manuell eingespielt werden.'
          },
          panelClass: 'warning'
        });
        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
          if (confirmed === true) {
            postAgeGroups();
          }
        });
      }
      else {
        postAgeGroups();
      }
    })
    this.ageGroupCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
      }
      this.__ageGroups = JSON.parse(JSON.stringify(this.ageGroups!));
      this.ageGroupErrors = [];
    })
  }

  setupYearCard(): void {
    this.yearForm = this.formBuilder.group({
      startYear: this.projectSettings!.startYear,
      endYear: this.projectSettings!.endYear
    });
    this.yearCard.dialogConfirmed.subscribe(()=>{
      this.yearForm.setErrors(null);
      this.yearForm.markAllAsTouched();
      if (this.yearForm.invalid) return;
      const startYear = this.yearForm.value.startYear,
        endYear = this.yearForm.value.endYear;
      if (endYear <= startYear) {
        this.yearForm.controls['startYear'].setErrors({'tooHigh': true});
        return;
      }
      let attributes: any = {
        startYear: startYear,
        endYear: endYear
      }
      this.yearCard.setLoading(true);
      this.http.patch<ProjectSettings>(this.rest.URLS.projectSettings, attributes
      ).subscribe(settings => {
        this.yearCard.closeDialog(true);
        this.projectSettings = settings;
      },(error) => {
        // ToDo: set specific errors to fields
        this.yearForm.setErrors(error.error);
        this.yearCard.setLoading(false);
      });
    })
    this.yearCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.yearForm.reset({
          startYear: this.projectSettings!.startYear,
          endYear: this.projectSettings!.endYear
        });
      }
    })
  }

  updatePreviewLayer(){
    let previewLayer = this.previewMapControl?.map?.getLayer('project-area');
    if (previewLayer) {
      const format = new WKT();
      if (this.projectSettings!.projectArea) {
        const wktSplit = this.projectSettings!.projectArea.split(';'),
          epsg = wktSplit[0].replace('SRID=','EPSG:'),
          wkt = wktSplit[1];

        let feature = format.readFeature(wkt);
        feature.getGeometry().transform(epsg, `EPSG:${this.previewMapControl?.srid}`);
        this.projectGeom = feature.getGeometry();
        const source = previewLayer.getSource();
        source.clear();
        source.addFeature(feature);
        if (this.projectGeom?.getArea())
          this.previewMapControl?.map?.centerOnLayer('project-area');
      }
    }
  }

  setupAreaCard(): void {
    this.areaCard.dialogOpened.subscribe(x => {
      this.projectAreaErrors = [];
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.getBackgroundLayers()[0].id)

      let projectLayer = this.areaSelectMapControl.map?.addVectorLayer('project-area', {
        stroke: { color: '#2196F3', width: 3 },
        fill: { color: 'rgba(33, 150, 243, 0.5)' },
        visible: true
      });
      this.mergedSelectArea = new Feature(this.projectGeom);
      projectLayer?.getSource().addFeature(this.mergedSelectArea);
      const hasProjectArea = this.projectGeom?.getArea();
      if (hasProjectArea)
        this.areaSelectMapControl.map?.centerOnLayer('project-area');
      this.areaSelectMapControl.map?.selected.subscribe(event => {
        this.featuresSelected(event.layer, event.selected, event.deselected);
      })
      const _this = this;

      let nLoaded = 0;
      this.areaLayers.forEach(al => {
        const layer = _this.areaSelectMapControl!.map?.addVectorLayer(
          al.tag, {
            url: function (extent: any) {
              return (
                'https://sgx.geodatenzentrum.de/wfs_vg250?service=WFS&' +
                `version=1.1.0&request=GetFeature&typename=${al.tag}&` +
                'outputFormat=application/json&srsname=EPSG:3857&' +
                'bbox=' +
                extent.join(',') +
                ',EPSG:3857'
              )},
            visible: (al === this.baseAreaLayer)? true: false,
            selectable: true,
            opacity: (al === _this.selectedAreaLayer)? 0.5 : 0,
            tooltipField: 'gen',
            stroke: { color: 'black', selectedColor: 'black' },
            fill: { color: 'rgba(0, 0, 0, 0)', selectedColor: 'rgba(0, 0, 0, 0)' }
          });
        layer?.set('showTooltip', al === this.selectedAreaLayer);
        layer?.get('select').setActive(al === this.selectedAreaLayer);
        layer?.getSource().addEventListener('featuresloadend', function () {
          nLoaded += 1;
          if (nLoaded == _this.areaLayers.length){
            _this.areaCard.setLoading(false);
            nLoaded = 0;
          }
        })
      })
      this.areaSelectMapControl.map?.map.getView().on('change', function(){
        if (_this.showAreaLayers) _this.updateAreasInExtent();
      })
      this._baseSelectLayer = this.areaSelectMapControl.map?.getLayer(this.baseAreaLayer.tag);
      this._baseSelectLayer?.getSource().addEventListener('featuresloadstart', function () {
        _this.areaCard.setLoading(true);
      });
      this._baseSelectLayer?.getSource().addEventListener('featuresloadend', function () {
        if (_this.showAreaLayers) _this.updateAreasInExtent();
      });
      this._baseSelectLayer?.getSource().once('featuresloadend', function () {
        _this.areaCard.setLoading(false);
        if (!hasProjectArea) return;
        let intersections = _this.getIntersections(_this.mergedSelectArea!.getGeometry(), _this._baseSelectLayer!);
        intersections.forEach((feature: Feature<any>) => {
          feature.set('inSelection', true);
          _this.selectedBaseAreaMap.set(feature.get('debkg_id'), feature)
        })
        _this._baseSelectLayer?.setVisible(false);
      });
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
      this.selectedAreaLayer = this.areaLayers[0];
      this.showAreaLayers = false;
    })
    this.areaCard.dialogConfirmed.subscribe(ok => {
      const format = new WKT();
      let projectGeom = this.mergedSelectArea?.getGeometry();
      let wkt = projectGeom? `SRID=${this.areaSelectMapControl?.srid};` + format.writeGeometry(projectGeom) : null
      this.http.patch<ProjectSettings>(`${this.rest.URLS.projectSettings}`,
        { projectArea: wkt }
      ).subscribe(settings => {
        this.areaCard?.closeDialog(true);
        this.projectSettings = settings;
        this.updatePreviewLayer();
      },(error) => {
        this.projectAreaErrors = error.error;
      });
    })
  }

  /**
   * check if agegroups are complete (seamless from 0 to 999 with) and do not intersect
   *
   * @param ageGroups
   */
  validateAgeGroups(ageGroups: AgeGroup[]): boolean {
    for (let i = 0; i < ageGroups.length; i+= 1) {
      const expectedFrom = (i === 0)? 0: ageGroups[i-1].toAge + 1,
            expectedTo = (i === ageGroups.length - 1)? 999: ageGroups[i+1].fromAge - 1,
            ageGroup = ageGroups[i];
      // actually redundant to check both, but do it nonetheless
      if (expectedFrom != ageGroup.fromAge || expectedTo != ageGroup.toAge){
        return false;
      }
    }
    return true;
  }

  compareAgeGroupsDefault(ageGroups: AgeGroup[]): boolean {
    if (ageGroups.length !== this.ageGroupDefaults.length) return false;
    for (let i = 0; i < ageGroups.length; i+= 1){
      const ageGroup = ageGroups[i],
        defaultAgeGroup = this.ageGroupDefaults[i]
      if (ageGroup.fromAge !== defaultAgeGroup.fromAge || ageGroup.toAge !== defaultAgeGroup.toAge){
        return false
      }
    }
    return true;
  }

  resetAgeGroups(): void {
    this.__ageGroups = JSON.parse(JSON.stringify(this.ageGroupDefaults));
    this.ageGroupErrors = [];
  }

  addAgeGroup(): void {
    if (this.__ageGroups.length > 0) {
      const lastAgeGroup = this.__ageGroups[this.__ageGroups?.length - 1];
      lastAgeGroup.toAge = lastAgeGroup.fromAge + 1;
      this.__ageGroups.push({ fromAge: lastAgeGroup.toAge + 1, toAge: 999});
    }
    else {
      this.__ageGroups = [{ fromAge: 0, toAge: 999 }];
    }
    this.ageGroupErrors = [];
    this.ageGroupContainer.nativeElement.scrollTop = this.ageGroupContainer.nativeElement.scrollHeight;
  }

  removeAgeGroup(ageGroup: AgeGroup): void {
    const index = this.__ageGroups.indexOf(ageGroup);
    if (index == -1) return;
    if (index > 0)
      this.__ageGroups[index - 1].toAge = (index < this.__ageGroups.length - 1)? ageGroup.toAge: 999;
    else
      this.__ageGroups[index + 1].fromAge = 0;
    this.__ageGroups.splice(index, 1);
    this.ageGroupErrors = [];
  }

  removeAllAgeGroups(): void {
    this.__ageGroups = [];
    this.addAgeGroup();
  }

  /**
   * change active layer to currently selected one
   */
  changeAreaLayer(): void {
    const _this = this;
    this.areaCard.setLoading(true);
    this.areaLayers.forEach(al => {
      const layer = this.areaSelectMapControl?.map?.getLayer(al.tag),
            select = layer?.get('select');
      layer?.setOpacity((al === _this.selectedAreaLayer) ? 0.5 : 0);
      select.setActive(al === this.selectedAreaLayer);
      layer?.set('showTooltip', al === this.selectedAreaLayer);
    })
    const layer = this.areaSelectMapControl?.map?.getLayer(this.selectedAreaLayer.tag),
          select = layer?.get('select');
    select.getFeatures().clear();
    if (this.mergedSelectArea) {
      let intersections = this.getIntersections(this.mergedSelectArea.getGeometry(), layer!);
      select.getFeatures().extend(intersections);
    }
    this.areaCard.setLoading(false);
  }

  /**
   * update project area and selected base features
   * when feature on map is selected/deselected (any area layer)
   *
   * @param layer
   * @param selected
   * @param deselected
   */
  featuresSelected(layer: Layer<any>, selected: Feature<any>[], deselected: Feature<any>[]){
    this.areaCard.setLoading(true);

    let selectedBaseFeatures: Feature<any>[] = [],
        deselectedBaseFeatures: Feature<any>[] = [];

    if (layer !== this._baseSelectLayer){
      selected.forEach(feature => {
        let intersections =  this.getBaseIntersections(feature);
        selectedBaseFeatures = selectedBaseFeatures.concat(intersections);
      })
      deselected.forEach(feature => {
        let intersections =  this.getBaseIntersections(feature);
        deselectedBaseFeatures = selectedBaseFeatures.concat(intersections);
      })
    }
    else {
      selectedBaseFeatures = selected;
      deselectedBaseFeatures = deselected;
    }

    selectedBaseFeatures.forEach(feature => {
      feature.set('inSelection', true);
      this.selectedBaseAreaMap.set(feature.get('debkg_id'), feature);
    })
    deselectedBaseFeatures.forEach(feature => {
      feature.set('inSelection', false);
      this.selectedBaseAreaMap.delete(feature.get('debkg_id'));
    })
    this.updateMergedSelectArea();
    this.areaCard.setLoading(false);
  }

  updateMergedSelectArea(){
    let mergedGeom: turf.Feature<turf.MultiPolygon | turf.Polygon> | null = null;
    this.selectedBaseAreaMap.forEach((f: Feature<any>) => {
      // const json = format.writeGeometryObject(f.getGeometry());
      const poly = turf.multiPolygon(f.getGeometry().getCoordinates());
      mergedGeom = mergedGeom ? union(poly, mergedGeom) : poly;
    })
    const format = new GeoJSON();
    // @ts-ignore
    let projectGeom = mergedGeom ? format.readFeature(mergedGeom.geometry).getGeometry() : new MultiPolygon([]);
    if (projectGeom instanceof Polygon)
      // @ts-ignore
      projectGeom = new MultiPolygon([projectGeom.getCoordinates()]);
    this.mergedSelectArea?.setGeometry(projectGeom);
  }

  /**
   * get intersections of feature with all features of given layer
   *
   * @param geom
   * @param layer
   */
  getIntersections(geom: Geometry, layer: Layer<any>): Feature<any>[]{
    const features = layer.getSource().getFeatures();
    let intersections: Feature<any>[] = [];
    features.forEach((f: Feature<any>) => {
      let poss = f.getGeometry().getInteriorPoints().getCoordinates();
      for (let i = 0; i < poss.length; i++) {
        let coords = poss[i],
          intersection = geom.intersectsCoordinate(coords);
        if (intersection) {
          intersections.push(f);
          break;
        }
      }
    })
    return intersections;
  }


  /**
   * Returns cached features of base area layer intersecting the given feature
   *
   * @param feature
   */
  getBaseIntersections(feature: Feature<any>): Feature<any>[]{
    let intersections = feature.get('intersect');
    if (!intersections) {
      intersections = this.getIntersections(feature.getGeometry(), this._baseSelectLayer!);
      feature.set('intersect', intersections);
    }
    return intersections;
  }

  ngOnDestroy(): void {
    this.previewMapControl?.destroy();
  }

  updateAreasInExtent(): void {
    const _this = this,
          extent = this.areaSelectMapControl?.map?.getExtent(),
          intersections = this.getIntersections(extent!, this._baseSelectLayer!);
    let areas = Array.from(this.selectedBaseAreaMap.values());
    intersections.forEach(feature => {
      if (!_this.selectedBaseAreaMap.has(feature.get('debkg_id')))
        areas.push(feature);
    })
    this.baseAreasInExtent = areas.sort(
      (a, b) => a.get('gen').localeCompare(b.get('gen')));
  }

  toggleLayerVisibility(): void{
    this.areaLayers.forEach(al => {
      const layer = this.areaSelectMapControl?.map?.getLayer(al.tag);
      layer?.setVisible(this.showAreaLayers);
    })
    if (this.showAreaLayers)
      this.updateAreasInExtent();
  }

  toggleFeatureSelection(feature: Feature<any>): void{
    this.areaCard.setLoading(true);
    const isSelected = this.selectedBaseAreaMap.has(feature.get('debkg_id'));
    if (isSelected)
      this.selectedBaseAreaMap.delete(feature.get('debkg_id'));
    else
      this.selectedBaseAreaMap.set(feature.get('debkg_id'), feature);
    feature.set('inSelection', !isSelected);
    this.updateMergedSelectArea();
    this.areaCard.setLoading(false);
  }

  removeAreaSelections(): void {
    this.areaCard.setLoading(true);
    this.selectedBaseAreaMap.forEach((feature, key) => {
      feature.set('inSelection', false);
    })
    this.selectedBaseAreaMap.clear();
    this.updateMergedSelectArea();
    this.areaCard.setLoading(false);
  }
}
