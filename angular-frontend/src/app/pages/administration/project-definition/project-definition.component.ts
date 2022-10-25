import { AfterViewInit, Component, ElementRef, OnDestroy, TemplateRef, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { Geometry, MultiPolygon, Polygon } from "ol/geom";
import { Feature } from 'ol';
import { AgeGroup } from "../../../rest-interfaces";
import { register } from 'ol/proj/proj4'
import union from '@turf/union';
import * as turf from '@turf/helpers';
import { GeoJSON, WKT } from "ol/format";
import proj4 from 'proj4';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { Observable } from "rxjs";
import { Layer } from "ol/layer";
import { ConfirmDialogComponent } from "../../../dialogs/confirm-dialog/confirm-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { RemoveDialogComponent } from "../../../dialogs/remove-dialog/remove-dialog.component";
import { tap } from "rxjs/operators";
import { SimpleDialogComponent } from "../../../dialogs/simple-dialog/simple-dialog.component";

export interface ProjectSettings {
  projectArea: string,
  startYear: number,
  endYear: number,
  minYear: number
}
interface BKGLayer {
  name: string,
  tag: string
}

const areaLayers: BKGLayer[] = [
  { name: 'Kreise', tag: 'vg250_krs' },
  { name: 'Verwaltungsgemeinschaften', tag: 'vg250_vwg' },
  { name: 'Gemeinden', tag: 'vg250_gem' }
]

proj4.defs("EPSG:25832", "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs");
register(proj4);

function transformAgeGroups(ageGroups: AgeGroup[]): AgeGroup[] {
  const trans = ageGroups.map(ag => {
    return { fromAge: ag.fromAge, toAge: ag.toAge + 1 }
  })
  // remove last element
  trans.pop();
  return trans;
}

@Component({
  selector: 'app-project-definition',
  templateUrl: './project-definition.component.html',
  styleUrls: ['./project-definition.component.scss']
})
export class ProjectDefinitionComponent implements AfterViewInit, OnDestroy {
  previewMapControl?: MapControl;
  areaSelectMapControl?: MapControl;
  projectGeom?: MultiPolygon;
  startYear: number = 0;
  endYear: number = 0;
  years?: number[];
  ageGroups: AgeGroup[] = [];
  editAgeGroups: AgeGroup[] = [];
  ageGroupDefaults: AgeGroup[] = [];
  projectAreaErrors = [];
  projectSettings?: ProjectSettings;
  yearForm!: FormGroup;
  Object = Object;
  areaLayers = areaLayers;
  selectedAreaLayer: BKGLayer = areaLayers[0];
  baseAreaLayer: BKGLayer = areaLayers[areaLayers.length - 1];
  selectedBaseAreaMapping = new Map<string, Feature<any>>();
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
      this.updatePreviewLayer();
    });
    this.fetchYears().subscribe(settings => {
      this.setupYearCard();
    });
    this.fetchAgeGroups().subscribe(ageGroups => {
      this.setupAgeGroupCard();
    });
  }

  fetchProjectSettings(): Observable<ProjectSettings> {
    let query = this.http.get<ProjectSettings>(this.rest.URLS.projectSettings).pipe(tap(projectSettings => {
      this.projectSettings = projectSettings;
    }));
    return query;
  }

  fetchYears(): Observable<any> {
    let query = this.http.get<any[]>(this.rest.URLS.years).pipe(tap(years => {
      this.applyYears(years);
    }));
    return query;
  }

  private applyYears(years: any[]) {
    let ys = years.map((y: any) => y.year);
    ys.sort();
    this.years = ys;
    this.startYear = ys[0];
    this.endYear = ys[ys.length - 1];
  }

  fetchAgeGroups(): Observable<AgeGroup[]> {
    this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups, {params: {defaults: true}}).subscribe(ageGroups => {
      this.ageGroupDefaults = ageGroups;
    })
    let query = this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups).pipe(tap(ageGroups => {
      this.ageGroups = ageGroups;
    }))
    return query;
  }

  setupPreviewMap(): void {
    this.previewMapControl = this.mapService.get('project-preview-map');
    this.previewMapControl.setBackground(this.previewMapControl.backgroundLayers[0].id!);
    this.previewMapControl.map?.addVectorLayer('project-area',{
      visible: true,
      zIndex: 1000,
      stroke: { color: '#DA9A22', width: 3 },
      fill: { color: 'rgba(218, 154, 34, 0.7)' }
    });
  }

  setupAgeGroupCard(): void {
    this.editAgeGroups = transformAgeGroups(this.ageGroups);

    this.ageGroupCard.dialogConfirmed.subscribe(ok => {
      // transformation raised toAge, revert
      const changedGroups = this.editAgeGroups.map(ag => {
        return { fromAge: ag.fromAge, toAge: ag.toAge - 1 }
      })
      // append last group that was cut
      if (this.editAgeGroups.length === 0)
        changedGroups.push({ fromAge: 0, toAge: 999 })
      changedGroups.push({
        fromAge: (this.editAgeGroups.length === 0)? 0: this.editAgeGroups[this.editAgeGroups.length-1].toAge,
        toAge: 999
      })
      const valid = this.validateAgeGroups(changedGroups),
            _this = this;
      if (!valid) {
        this.ageGroupErrors = ['Die Altersgruppen müssen lückenlos sein und dürfen sich nicht überschneiden'];
        return;
      }
      const matchesDefaults = this.compareAgeGroupsDefault(changedGroups);
      function postAgeGroups(){
        _this.ageGroupCard.setLoading(true);
        _this.http.post<AgeGroup[]>(`${_this.rest.URLS.ageGroups}replace/`, changedGroups
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
          if (confirmed) {
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
      this.editAgeGroups = transformAgeGroups(this.ageGroups);
      this.ageGroupErrors = [];
    })
  }

  setupYearCard(): void {
    this.yearForm = this.formBuilder.group({
      startYear: this.years![0],
      endYear: this.years![this.years!.length - 1]
    });
    this.yearCard.dialogConfirmed.subscribe(()=>{
      this.yearForm.setErrors(null);
      this.yearForm.markAllAsTouched();
      if (this.yearForm.invalid) return;
      const startYear = this.yearForm.value.startYear,
        endYear = this.yearForm.value.endYear;
      const newYears = Array.from({length: 1 + endYear - startYear}, (_, i) => i + startYear);
      const curYears = Array.from({length: 1 + this.endYear - this.startYear}, (_, i) => i + this.startYear);
      const yearsToDelete = curYears.filter(y => !newYears.includes(y));
      if (endYear <= startYear) {
        this.yearForm.controls['startYear'].setErrors({'tooHigh': true});
        return;
      }
      let attributes: any = {
        from_year: startYear,
        to_year: endYear
      }
      const _this = this;
      function postYears(){
        _this.yearCard.setLoading(true);
        _this.http.post<any[]>(`${_this.rest.URLS.years}set_range/`, attributes
        ).subscribe(years => {
          _this.applyYears(years);
          _this.yearCard.setLoading(false);
          _this.yearCard.closeDialog(true);
        }, (error) => {
          // ToDo: set specific errors to fields
          _this.yearForm.setErrors(error.error);
          _this.yearCard.setLoading(false);
        });
      }
      if (yearsToDelete.length > 0){
        const dialogRef = this.dialog.open(RemoveDialogComponent, {
          width: '500px',
          data: {
            title: $localize`Zeitraum bestätigen`,
            confirmButtonText: $localize`Änderung des Zeitraums bestätigen`,
            value: yearsToDelete.join(', '),
            message: 'Bereits in der Datenbank angelegte Jahre, die nicht im angegebenen neuen Betrachtungszeitraum liegen, ' +
              'werden gelöscht. Alle für diese Jahre vorhandenen Daten (Bevölkerung, Nachfragequoten) ' +
              'werden ebenfalls entfernt. Folgende Jahre und damit verknüpfte Daten sind von der Löschung betroffen: '
          }
        });
        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
          if (confirmed) postYears();
        })
      }
      else
        postYears()
    })
    this.yearCard.dialogOpened.subscribe((ok)=>{
      this.yearForm.reset({
        startYear: this.years![0],
        endYear: this.years![this.years!.length - 1]
      });
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
          this.previewMapControl?.map?.zoomToExtent('project-area');
      }
    }
  }

  setupAreaCard(): void {
    this.areaCard.dialogOpened.subscribe(x => {
      this.projectAreaErrors = [];
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.backgroundLayers[0].id!);

      const projectLayer = this.areaSelectMapControl.map?.addVectorLayer('project-area', {
        zIndex: 1000,
        stroke: { color: 'rgba(0, 0, 0, 0)' },
        fill: { color: 'rgba(218, 154, 34, 0.7)' },
        visible: true
      });

      const hasProjectArea = this.projectGeom?.getArea();
      if (hasProjectArea) {
        projectLayer?.getSource().addFeature(new Feature(this.projectGeom));
        this.areaSelectMapControl.map?.zoomToExtent('project-area');
      }
      projectLayer?.getSource().clear();
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
            visible: al === this.baseAreaLayer,
            zIndex: 1001,
            selectable: true,
            tooltipField: 'gen',
            stroke: { color: 'black', selectedColor: 'black',
               mouseOverColor: 'blue', mouseOverWidth: 3 },
            fill: { color: 'rgba(0, 0, 0, 0)', selectedColor: 'rgba(0, 0, 0, 0)' }
          });
        layer?.getSource().addEventListener('featuresloadend', function () {
          nLoaded += 1;
          if (nLoaded == _this.areaLayers.length){
            _this.areaCard.setLoading(false);
            nLoaded = 0;
          }
        })
      })
      this.changeAreaLayer();
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
        _this._baseSelectLayer?.setVisible(false);
        if (!hasProjectArea) return;
        let intersections = _this.getIntersections(_this.projectGeom!, _this._baseSelectLayer!);
        intersections.forEach((feature: Feature<any>) => {
          if (feature.get('gf') != 4) return;
          feature.set('inSelection', true);
          _this.selectedBaseAreaMapping.set(feature.get('objid'), feature)
        })
        _this.updateProjectLayer();
      });
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
      this.selectedAreaLayer = this.areaLayers[0];
      this.showAreaLayers = false;
    })
    this.areaCard.dialogConfirmed.subscribe(ok => {
      const dialogRef = SimpleDialogComponent.show(
        'Geometrie des Projektgebietes wird hochgeladen und mit dem Raster verschnitten. ' +
                'Die Gebiete der vordefinierten Gebietseinteilungen innerhalb des Projektgebietes werden heruntergeladen.<br><br>' +
                'Dies kann einige Minuten dauern. Bitte warten',
        this.dialog, { showAnimatedDots: true, width: '400px' });
      const format = new WKT();
      let projectGeom = this.getMergedSelectGeometry();
      let wkt = projectGeom? `SRID=${this.areaSelectMapControl?.srid};` + format.writeGeometry(projectGeom) : null
      this.http.patch<ProjectSettings>(`${this.rest.URLS.projectSettings}`,
        { projectArea: wkt }
      ).subscribe(settings => {
        dialogRef.close();
        this.areaCard?.closeDialog(true);
        this.projectSettings = settings;
        this.updatePreviewLayer();
      },(error) => {
        dialogRef.close();
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
    this.editAgeGroups = transformAgeGroups(this.ageGroupDefaults);
    this.ageGroupErrors = [];
  }

  addAgeGroup(): void {
    if (this.editAgeGroups.length > 0) {
      const lastAgeGroup = this.editAgeGroups[this.editAgeGroups?.length - 1];
      this.editAgeGroups.push({ fromAge: lastAgeGroup.toAge, toAge: lastAgeGroup.toAge + 1});
    }
    else {
      this.editAgeGroups = [{ fromAge: 0, toAge: 1 }];
    }
    this.ageGroupErrors = [];
    this.ageGroupContainer.nativeElement.scrollTop = this.ageGroupContainer.nativeElement.scrollHeight;
  }

  removeAgeGroup(ageGroup: AgeGroup): void {
    const index = this.editAgeGroups.indexOf(ageGroup);
    if (index == -1) return;
    // if (index > 0)
    //   this.editAgeGroups[index - 1].toAge = (index < this.editAgeGroups.length - 1)? ageGroup.toAge: 999;
    // else
    //   this.editAgeGroups[index + 1].fromAge = 0;
    this.editAgeGroups.splice(index, 1);
    this.ageGroupErrors = [];
  }

  insertAgeGroup(index: number) {
    this.editAgeGroups.splice(index+1, 0, {
      fromAge: this.editAgeGroups[index].toAge,
      toAge: this.editAgeGroups[index+1].fromAge,
    })
  }

  /**
   * change active layer to currently selected one
   */
  changeAreaLayer(): void {
    this.areaCard.setLoading(true);
    this.areaLayers.forEach(al => {
      const layer = this.areaSelectMapControl?.map?.getLayer(al.tag),
            select = layer?.get('select');
      layer?.setOpacity((al.tag === this.selectedAreaLayer.tag) ? 0.5 : 0);
      select.setActive(al.tag === this.selectedAreaLayer.tag);
      layer?.set('showTooltip', al.tag === this.selectedAreaLayer.tag);
      const overlay = this.areaSelectMapControl?.map?.overlays[layer?.get('name')];
      if (overlay) {
        // overlay.getSource().clear();
        overlay.setVisible(al.tag === this.selectedAreaLayer.tag);
      }
    })
    const layer = this.areaSelectMapControl?.map?.getLayer(this.selectedAreaLayer.tag),
          select = layer?.get('select');
    select.getFeatures().clear();
    const selectGeom = this.getMergedSelectGeometry();
    if (selectGeom) {
      let intersections = this.getIntersections(selectGeom, layer!);
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
        if (feature.get('gf') != 4) return;
        let intersections = this.getBaseIntersections(feature);
        selectedBaseFeatures = selectedBaseFeatures.concat(intersections);
      })
      deselected.forEach(feature => {
        let intersections = this.getBaseIntersections(feature);
        deselectedBaseFeatures = selectedBaseFeatures.concat(intersections);
      })
    }
    else {
      selectedBaseFeatures = selected;
      deselectedBaseFeatures = deselected;
    }
    const _this = this;

    selectedBaseFeatures.forEach(feature => {
      if (feature.get('gf') === 4) {
        feature.set('inSelection', true);
        _this.selectedBaseAreaMapping.set(feature.get('objid'), feature);
      }
    })
    deselectedBaseFeatures.forEach(feature => {
      feature.set('inSelection', false);
      _this.selectedBaseAreaMapping.delete(feature.get('objid'));
    })
    this.updateProjectLayer();
    this.areaCard.setLoading(false);
  }

  updateProjectLayer(): void {
    this.areaSelectMapControl?.map?.clear('project-area');
    let features: Feature<any>[] = [];
    this.selectedBaseAreaMapping.forEach(feature => {
      features.push(new Feature(feature.getGeometry()));
    })
    this.areaSelectMapControl?.map?.addFeatures('project-area', features);
  }

  getMergedSelectGeometry(): MultiPolygon{
    let mergedGeom: turf.Feature<turf.MultiPolygon | turf.Polygon> | null = null;
    this.selectedBaseAreaMapping.forEach((f: Feature<any>) => {
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
    return projectGeom;
  }

  /**
   * get intersections of geometry with all features of given layer
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
   * Returns features of base area layer intersecting the given feature
   *
   * @param feature
   * @param cached - cache results of intersections (ToDo: causes problems for areas
   * that exceed current extent)
   */
  getBaseIntersections(feature: Feature<any>, cached: boolean = false): Feature<any>[]{
    let intersections = cached? undefined: feature.get('intersect');
    if (!intersections) {
      intersections = this.getIntersections(feature.getGeometry(), this._baseSelectLayer!);
      if (cached) feature.set('intersect', intersections);
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
    let areas = Array.from(this.selectedBaseAreaMapping.values());
    intersections.forEach(feature => {
      if (!_this.selectedBaseAreaMapping.has(feature.get('objid')) && (feature.get('gf') == 4))
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
    if (this.showAreaLayers) {
      this.updateAreasInExtent();
    }
  }

  toggleFeatureSelection(feature: Feature<any>): void{
    this.areaCard.setLoading(true);
    const isSelected = this.selectedBaseAreaMapping.has(feature.get('objid'));
    if (isSelected)
      this.selectedBaseAreaMapping.delete(feature.get('objid'));
    else
      this.selectedBaseAreaMapping.set(feature.get('objid'), feature);
    feature.set('inSelection', !isSelected);
    this.updateProjectLayer();
    this.areaCard.setLoading(false);
  }

  removeAreaSelections(): void {
    this.areaCard.setLoading(true);
    this.selectedBaseAreaMapping.forEach((feature, key) => {
      feature.set('inSelection', false);
    })
    this.selectedBaseAreaMapping.clear();
    this.updateProjectLayer();
    this.areaCard.setLoading(false);
  }
}
